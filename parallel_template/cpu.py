from multiprocessing import Pool
from tqdm.auto import tqdm


def main_worker(sub_ids):
    for _ in range(len(sub_ids)):
        pass
    return {i: i for i in sub_ids}


def main():
    pool = Pool(4)

    with tqdm(total=2) as pbar:
        for _ in pool.imap_unordered(main_worker, [[1, 2, 3, 4], [5, 6, 7, 8]]):
            pbar.update()


if __name__ == "__main__":
    main()