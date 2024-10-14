import os
import cv2
import numpy as np


def combine_image(img_path1, img_path2, output_path):
    img1 = cv2.imread(img_path1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img_path2, cv2.IMREAD_GRAYSCALE)

    avg_value = (img1.astype(int) + img2.astype(int)) // 2
    avg_value = avg_value.astype('uint8')

    bgr_img = cv2.merge((avg_value, img2, img1))
    cv2.imwrite(output_path, bgr_img)


def combine_image_diff(img_path1, img_path2, output_path):
    img1 = cv2.imread(img_path1)
    img2 = cv2.imread(img_path2)
    img3 = cv2.subtract(img1, img2)
    # img3 = cv2.absdiff(img1, img2)

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    gray3 = cv2.cvtColor(img3, cv2.COLOR_BGR2GRAY)

    merged_image = np.zeros_like(img1)
    merged_image[:, :, 0] = gray3  # B
    merged_image[:, :, 1] = gray1  # G
    merged_image[:, :, 2] = gray2  # R

    cv2.imwrite(output_path, merged_image)
