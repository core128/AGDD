import os
import cv2
import json
import numpy as np
from math import sin, cos, pi

from utils.converter import calculate_rotation_theta, adjust_rectangle_coordinates
from utils.utility import gen_yaml


def rotate_image(raw_img, angle, make_flip=False):
    img = cv2.flip(raw_img, 1) if make_flip else raw_img.copy()
    if angle == 0:
        return img
    elif angle == 90:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        height, width = img.shape[:2]  # (H,W,C)
        center = (width / 2, height / 2)
        scale = 1.0
        borderValue = (0, 114, 114)  # fill color
        M = cv2.getRotationMatrix2D(center, -angle, scale)
        rotated_img = cv2.warpAffine(src=img, M=M, dsize=(height, width), borderValue=borderValue)
        return rotated_img


def rotate_point(point, angle, flip_before_rotate, img_width, img_height):
    center_point = [img_width / 2.0, img_height / 2.0]
    x1 = img_width - point[0] if flip_before_rotate else point[0]
    y1 = img_height - point[1]
    x2 = center_point[0]
    y2 = img_height - center_point[1]
    radian = - pi / 180.0 * angle
    x = (x1 - x2) * cos(radian) - (y1 - y2) * sin(radian) + x2
    y = (x1 - x2) * sin(radian) + (y1 - y2) * cos(radian) + y2
    point[0] = x
    point[1] = img_height - y


def is_missing(point_list, img_width, img_height):
    """Check whether the box falls outside the image."""
    miss_cnt = 0
    for point in point_list:
        if point[0] <= 0 or point[0] >= img_width or point[1] <= 0 or point[1] >= img_height:
            miss_cnt += 1
    return miss_cnt == 4


def rotate_json_label(json_file_path, output_file_path, angle, flip_before_rotate=False, new_img_name=None):
    with open(json_file_path, 'r', encoding="utf-8") as f:
        data = json.load(f)
        shapes = data['shapes']
        w, h = data["imageWidth"], data["imageHeight"]
        for shape in shapes:
            points = shape["points"]
            for point in points:
                rotate_point(point, angle, flip_before_rotate, w, h)
            adjust_rectangle_coordinates(points, w, h)
            shape['direction'] = calculate_rotation_theta(points)
        if new_img_name is not None:
            data["imagePath"] = new_img_name

    with open(output_file_path, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def rotate_obb_label(obb_file_path, output_file_path, angle, flip_before_rotate=False):
    with open(obb_file_path, 'r') as f, open(output_file_path, 'w') as g:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            class_idx = parts[0]
            coords = [float(p) for p in parts[1:]]  # n * 8
            rotated_point_list = []  # [x, y] * 4
            for i in range(4):
                point = [coords[i * 2], coords[i * 2 + 1]]
                rotate_point(point, angle, flip_before_rotate, 1.0, 1.0)
                rotated_point_list.append(point)

            if is_missing(rotated_point_list, 1.0, 1.0):
                # print(f"skip missing {rotated_point_list}")
                continue

            try:
                adjust_rectangle_coordinates(rotated_point_list, 1.0, 1.0)
                flat = sum(rotated_point_list, [])  # n * 8
                formatted_coords = ["{:.7f}".format(coord) for coord in flat]
                g.write(f"{class_idx} {' '.join(formatted_coords)}\n")
            except Exception as e:
                print(f"error processing {rotated_point_list}")
                print(e)
                print(output_file_path)


def rotate_rect_label(rect_file_path, output_file_path, angle, flip_before_rotate=False):
    assert angle in [0, 90, 180, 270]  # any angle is not allowed
    with open(rect_file_path, 'r') as f, open(output_file_path, 'w') as g:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            class_idx = parts[0]
            x, y, w, h = [float(p) for p in parts[1:]]
            points = [[x - w / 2, y - h / 2], [x + w / 2, y - h / 2], [x + w / 2, y + h / 2], [x - w / 2, y + h / 2]]
            for point in points:
                rotate_point(point, angle, flip_before_rotate, 1.0, 1.0)
                point[0] = max(0.0, min(point[0], 1.0))
                point[1] = max(0.0, min(point[1], 1.0))

            np_points = np.array(points)
            x1, y1 = np.min(np_points, axis=0)
            x2, y2 = np.max(np_points, axis=0)
            x, y, w, h = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
            formatted_coords = ["{:.7f}".format(coord) for coord in [x, y, w, h]]
            g.write(f"{class_idx} {' '.join(formatted_coords)}\n")


def octal_image(src_image_folder_path, dst_image_folder_path, angle_list=None):
    if angle_list is None:
        angle_list = [0, 90, 180, 270]
    if not os.path.exists(dst_image_folder_path):
        os.makedirs(dst_image_folder_path)
    for filename in os.listdir(src_image_folder_path):
        if filename.endswith("png"):
            raw_img = cv2.imread(os.path.join(src_image_folder_path, filename))
            for a in angle_list:
                for f in [False, True]:
                    save_name = f"{filename[:-5]}_{int(f)}{a:03d}.png"
                    save_path = os.path.join(dst_image_folder_path, save_name)
                    img = rotate_image(raw_img, a, f)
                    cv2.imwrite(save_path, img)


def octal_json_label(src_json_folder_path, dst_json_folder_path, angle_list=None):
    if angle_list is None:
        angle_list = [0, 90, 180, 270]
    if not os.path.exists(dst_json_folder_path):
        os.makedirs(dst_json_folder_path)
    for filename in os.listdir(src_json_folder_path):
        if filename.endswith(".json"):
            json_file_path = os.path.join(src_json_folder_path, filename)
            for a in angle_list:
                for f in [False, True]:
                    save_name = f"{filename[:-6]}_{int(f)}{a:03d}.json"
                    save_path = os.path.join(dst_json_folder_path, save_name)
                    new_img_name = save_name.replace(".json", ".png")
                    rotate_json_label(json_file_path, save_path, a, f, new_img_name)


def octal_obb_label(src_obb_folder_path, dst_obb_folder_path, angle_list=None):
    if angle_list is None:
        angle_list = [0, 90, 180, 270]
    if not os.path.exists(dst_obb_folder_path):
        os.makedirs(dst_obb_folder_path)
    for filename in os.listdir(src_obb_folder_path):
        if filename.endswith(".txt"):
            obb_file_path = os.path.join(src_obb_folder_path, filename)
            for a in angle_list:
                for f in [False, True]:
                    save_name = f"{filename[:-5]}_{int(f)}{a:03d}.txt"
                    save_path = os.path.join(dst_obb_folder_path, save_name)
                    rotate_obb_label(obb_file_path, save_path, a, f)


def octal_rect_label(src_rect_folder_path, dst_rect_folder_path, angle_list=None):
    if angle_list is None:
        angle_list = [0, 90, 180, 270]
    if not os.path.exists(dst_rect_folder_path):
        os.makedirs(dst_rect_folder_path)
    for filename in os.listdir(src_rect_folder_path):
        if filename.endswith(".txt"):
            rect_file_path = os.path.join(src_rect_folder_path, filename)
            for a in angle_list:
                for f in [False, True]:
                    save_name = f"{filename[:-5]}_{int(f)}{a:03d}.txt"
                    save_path = os.path.join(dst_rect_folder_path, save_name)
                    rotate_rect_label(rect_file_path, save_path, a, f)


def creat_single_x(rotate_angle_step, base_dataset_path, output_dir, new_dataset_name, label_type="obb"):
    angle_list = list(range(0, 360, rotate_angle_step))
    expand_rate = len(angle_list) * 2
    new_dataset_path = os.path.join(output_dir, new_dataset_name)
    print(f"Generating x{expand_rate} dataset...")

    for l1 in ["images", "labels"]:
        for l2 in ["train", "val"]:
            src = os.path.join(base_dataset_path, l1, l2)
            dst = os.path.join(new_dataset_path, l1, l2)
            if l1 == "labels":
                if label_type == "obb":
                    octal_obb_label(src, dst, angle_list)
                else:
                    octal_rect_label(src, dst, angle_list)
            else:
                octal_image(src, dst, angle_list)

    gen_yaml(new_dataset_path, new_dataset_name)


def creat_dual_x(rotate_angle_step, base_dataset_path, output_dir, new_dataset_name, label_type="obb"):
    angle_list = list(range(0, 360, rotate_angle_step))
    expand_rate = len(angle_list) * 2
    new_dataset_path = os.path.join(output_dir, new_dataset_name)
    print(f"Generating x{expand_rate} dataset...")

    for l1 in ["images", "image", "labels"]:
        for l2 in ["train", "val"]:
            src = os.path.join(base_dataset_path, l1, l2)
            dst = os.path.join(new_dataset_path, l1, l2)
            if l1 == "labels":
                if label_type == "obb":
                    octal_obb_label(src, dst, angle_list)
                else:
                    octal_rect_label(src, dst, angle_list)
            else:
                octal_image(src, dst, angle_list)

    gen_yaml(new_dataset_path, new_dataset_name)
