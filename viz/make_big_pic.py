import numpy as np
import cv2

import glob


def main():
    data_dir = "D:/LOGS/2022-10/val_1w"
    target_path = "tmp.png"
    
    M = 9
    N = 16
    resolution = 64
    suffix = "png"

    total_files = glob.glob(f"{data_dir}/*.{suffix}")
    total_files = total_files[:(M * N)]

    target_img = np.zeros((M * resolution, N * resolution, 3), dtype=np.uint8)

    for i, _f in enumerate(total_files):
        img = cv2.imread(_f)
        target_img[i//N * resolution:(i//N + 1) * resolution, i%N * resolution:(i%N + 1) * resolution] = img

    cv2.imwrite(filename=target_path, img=target_img)


if __name__ == '__main__':
    main()
