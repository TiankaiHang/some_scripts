r"""
Build webdataset from huggingface dataset
"""

import os
from datasets import load_dataset
import webdataset as wds

import uuid


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



if __name__ == "__main__":
    main()