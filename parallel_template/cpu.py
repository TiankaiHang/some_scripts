r"""
A template for parallel processing using CPU.
"""

from multiprocessing import Pool
from tqdm.auto import tqdm

from glob import glob
from PIL import Image

import click
import time


def main_worker(args):
    idx, image_path = args
    image = Image.open(image_path).convert("RGB")

    # process the image here

    return idx, None


@click.group()
def main():
    pass


@main.command()
@click.option("--num-cores", type=int, default=1)
def benchmark(num_cores=1):
    NUM_CORES = num_cores
    
    image_paths = glob("../datasets/VGPhraseCut_v0/images/*.jpg")
    args_list = [(idx, path) for idx, path in enumerate(image_paths)]

    start_time = time.time()

    with Pool(NUM_CORES) as pool:
        _ = list(tqdm(
            pool.imap_unordered(main_worker, args_list), 
            total=len(image_paths)))

    end_time = time.time()

    # to time format d/h:m:s
    elapsed_time = end_time - start_time
    elapsed_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

    print(f"Elapsed time: {elapsed_time}")


if __name__ == "__main__":
    r"""
    Command:
        python parallel_template/cpu.py benchmark --num-cores 1
        python parallel_template/cpu.py benchmark --num-cores 4
        python parallel_template/cpu.py benchmark --num-cores 40
        python parallel_template/cpu.py benchmark --num-cores 100
    """
    main()