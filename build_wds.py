r"""
Build webdataset from huggingface dataset
"""

import os
from functools import partial

import PIL.Image
import numpy as np
import logging
from datasets import load_dataset
import webdataset as wds
from webdataset.tariterators import (
    base_plus_ext, url_opener, 
    tar_file_expander, valid_sample
)


import uuid
import click


@click.group()
def cli():
    r"""
    CLI entry
    """


def my_handler(obj):
    # return obj.encode("utf-8") if isinstance(obj, str) else obj
    return str(obj).encode("utf-8") if isinstance(obj, bool) else obj


def generate_shard(oname, dataset, inds, prefix=""):
    """Generate a shard of samples.
    """
    with wds.TarWriter(oname) as output:
        for idx in inds:
            sample = dataset[idx]
            sample["__key__"] = uuid.uuid4().hex

            for key in sample:
                if isinstance(sample[key], (bytes, str)):
                    continue
                else:
                    sample[key] = str(sample[key])
            
            output.write(sample)
            if idx % 1000 == 0:
                print(f"{idx:09d} {prefix}:", sample["caption"][:40])



@cli.command()
def main():
    
    ds = load_dataset("/mnt/external/datasets/pickapic_v2/")
    os.makedirs("/mnt/external/datasets/pickapic_v2_webdataset", exist_ok=True)

    # >> ds.keys()
    # dict_keys(['train', 'validation', 'test', 'test_unique', 'validation_unique'])

    chunk_size = 100000

    for split in ds.keys():
        print(f"Processing {split}...")
        dataset = ds[split]
        num_samples = len(dataset)
        num_shards = num_samples // chunk_size + 1

        for i in range(num_shards):
            inds = list(range(i * chunk_size, min((i + 1) * chunk_size, num_samples)))
            oname = f"/mnt/external/datasets/pickapic_v2_webdataset/{split}_{i:05d}.tar"
            generate_shard(oname, dataset, inds, prefix=f"{split}_{i:05d}")



def log_and_continue(exn) -> bool:
    logging.warning(f'Webdataset error ({repr(exn)}). Ignoring.')
    return True


def group_by_keys_nothrow(
    data,
    keys=base_plus_ext,
    lcase=True,
    suffixes=None,
    handler=None,
):
    """Return function over iterator that groups key, value pairs into samples.
    :param keys: function that splits the key into key and extension (base_plus_ext)
    :param lcase: convert suffixes to lower case (Default value = True)
    """
    current_sample = None
    for filesample in data:
        assert isinstance(filesample, dict)
        fname, value = filesample["fname"], filesample["data"]
        prefix, suffix = keys(fname)
        if prefix is None:
            continue
        if lcase:
            suffix = suffix.lower()
        # FIXME webdataset version throws if suffix in current_sample, but we have a potential for
        #  this happening in the current LAION400m dataset if a tar ends with same prefix as the next
        #  begins, rare, but can happen since prefix aren't unique across tar files in that dataset
        if current_sample is None or prefix != current_sample["__key__"] or suffix in current_sample:
            if valid_sample(current_sample):
                yield current_sample
            current_sample = dict(__key__=prefix, __url__=filesample["__url__"])
        if suffixes is None or suffix in suffixes:
            current_sample[suffix] = value
    if valid_sample(current_sample):
        yield current_sample


def tarfile_to_samples_nothrow(src, handler=log_and_continue):
    # Re-implementation of the wds with group_by_keys that doesn't throw.
    streams = url_opener(src, handler=handler)
    files = tar_file_expander(streams, handler=handler)
    samples = group_by_keys_nothrow(files, handler=handler)
    return samples


def preprocess_img(img: PIL.Image, resolution: int = 256) -> np.ndarray:
    img = np.array(img)
    if img.ndim == 2:
        img = img[:, :, np.newaxis] # HW => HWC
    img = center_crop(resolution, resolution,  img)
    img = img.transpose(2, 0, 1) # HWC => CHW
    return img


def preprocess_txt(text: str) -> str:
    return text


def filter_no_caption(sample: dict) -> bool:
    return 'txt' in sample


def center_crop(width: int, height: int, img: np.ndarray) -> np.ndarray:
    crop = np.min(img.shape[:2])
    img = img[(img.shape[0] - crop) // 2 : (img.shape[0] + crop) // 2, (img.shape[1] - crop) // 2 : (img.shape[1] + crop) // 2]
    img = PIL.Image.fromarray(img, 'RGB')
    img = img.resize((width, height), PIL.Image.LANCZOS)
    return np.array(img)


@cli.command()
def test_wds():
    train_data: list[str]
    batch_size: int = 32
    resolution: int = 256
    workers: int = 3
    shard_shuffle_size: int = 1000
    sample_shuffle_size: int = 10000

    input_shards = train_data
    assert input_shards is not None

    dataset = wds.DataPipeline([
        wds.ResampledShards(input_shards),
        tarfile_to_samples_nothrow,
        wds.shuffle(shard_shuffle_size),
        wds.select(filter_no_caption),
        wds.decode("pilrgb", handler=log_and_continue),
        wds.shuffle(sample_shuffle_size),
        wds.rename(image="jpg;png", text="txt"),
        wds.map_dict(image=partial(preprocess_img, resolution=resolution), text=preprocess_txt),
        wds.to_tuple("image", "text"),
        wds.batched(batch_size),
    ])

    # build dataloader
    dataloader = wds.WebLoader(
        dataset,
        batch_size=None,
        shuffle=False,
        num_workers=workers,
    )

    return dataloader



if __name__ == "__main__":
    cli()