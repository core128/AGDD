import os
import cv2
import json
import math
import numpy as np
from scipy.optimize import linprog


def x_json_to_yolo_obb(json_file_path, output_file_path):
    class_mapping = {
        "contusion": 0,
        "scratches": 1,
        "crack": 2,
        "spot": 3,
    }

    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        image_width, image_height = float(data["imageWidth"]), float(data["imageHeight"])

    with open(output_file_path, "w", encoding="utf-8") as f:
        for shape in data["shapes"]:
            class_label = shape["label"]
            class_idx = class_mapping[class_label]
            points = shape["points"]
            normalized_coords = []
            for i in range(4):
                normalized_coords.append(points[i][0] / image_width)
                normalized_coords.append(points[i][1] / image_height)
            formatted_coords = ["{:.7f}".format(coord) for coord in normalized_coords]
            f.write(f"{class_idx} {' '.join(formatted_coords)}\n")


def x_json_to_yolo_rect(json_file_path, output_file_path):
    class_mapping = {
        "contusion": 0,
        "scratches": 1,
        "crack": 2,
        "spot": 3,
    }

    with open(json_file_path, 'r', encoding="utf-8") as f:
        data = json.load(f)
        image_width, image_height = float(data["imageWidth"]), float(data["imageHeight"])
        image_size = np.array([[image_width, image_height]])

    with open(output_file_path, "w", encoding="utf-8") as f:
        for shape in data["shapes"]:
            class_label = shape["label"]
            class_idx = class_mapping[class_label]
            points = np.array(shape["points"])
            norm_points = points / image_size
            x1, y1 = np.min(norm_points, axis=0)
            x2, y2 = np.max(norm_points, axis=0)
            x, y, w, h = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
            formatted_coords = ["{:.7f}".format(coord) for coord in [x, y, w, h]]
            f.write(f"{class_idx} {' '.join(formatted_coords)}\n")


def adjust_rectangle_coordinates(point_list, width: float, height: float):
    def cal_k(a1, a2, a3, a4, a5, a6):
        """
        min k
        s.t.  k >= 0
              0 <= a[0] + k * vector_ab[0] <= width
              0 <= a[1] + k * vector_ab[1] <= height

        let a1, a2, a3, a4, a5, a6 = a[0], a[1], vector_ab[0], vector_ab[1], width, height
        -a3 * k <= a1
         a3 * k <= a5 - a1
        -a4 * k <= a2
         a4 * k <= a6 - a2
        """
        _c = [1]
        _A = [[-a3], [a3], [-a4], [a4]]
        _b = [a1, a5 - a1, a2, a6 - a2]
        _bounds = [(0, None)]
        result = linprog(_c, A_ub=_A, b_ub=_b, bounds=_bounds, method='highs')
        return result.x[0]

    def is_inside_canvas(point):
        return 0 <= point[0] <= width and 0 <= point[1] <= height

    def distance(p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def translate_point(point, vector, _k):
        point[0] += vector[0] * _k
        point[1] += vector[1] * _k
        # fix accuracy error
        tolerance = 8.0e-5
        if math.fabs(point[0]) < tolerance:
            point[0] = 0.0
        elif math.fabs(point[0] - width) < tolerance:
            point[0] = float(width)
        if math.fabs(point[1]) < tolerance:
            point[1] = 0.0
        elif math.fabs(point[1] - height) < tolerance:
            point[1] = float(height)

    while not all(is_inside_canvas(p) for p in point_list):
        for i in range(4):
            if is_inside_canvas(point_list[i]):
                continue

            a = point_list[i]
            pre_idx = i - 1
            next_idx = (i + 1) % 4

            # b and c are two points adjacent to a
            # make sure ab is the long side of the rectangle
            if distance(a, point_list[pre_idx]) > distance(a, point_list[next_idx]):
                b, c = point_list[pre_idx], point_list[next_idx]
            else:
                c, b = point_list[pre_idx], point_list[next_idx]

            # move a and c in the direction of vector ab
            # that is, add k * vector_ab to the coordinates
            # which makes point a moved exactly to the boundary
            vector_ab = [b[0] - a[0], b[1] - a[1]]
            k = cal_k(a[0], a[1], vector_ab[0], vector_ab[1], width, height)
            translate_point(a, vector_ab, k)
            translate_point(c, vector_ab, k)


def calculate_rotation_theta(_points):
    x1, y1 = _points[0]
    x2, y2 = _points[1]

    # calculate one of the diagonal vectors (after rotation)
    diagonal_vector_x = x2 - x1
    diagonal_vector_y = y2 - y1

    # calculate the rotation angle in radians
    rotation_angle = math.atan2(diagonal_vector_y, diagonal_vector_x)

    # convert radians to degrees
    rotation_angle_degrees = math.degrees(rotation_angle)

    if rotation_angle_degrees < 0:
        rotation_angle_degrees += 360

    return rotation_angle_degrees / 360 * (2 * math.pi)


def modify_json_file(json_file_path, target_shape="rotation", force_write=False):
    assert target_shape in ["rotation", "rectangle"]

    with open(json_file_path, 'r') as file:
        data = json.load(file)
        print(f"load {json_file_path}")
    shapes = data["shapes"]
    img_w, img_h = float(data["imageWidth"]), float(data["imageHeight"])

    modified_flag = False
    for shape in shapes:
        if not force_write and shape["shape_type"] == target_shape:
            continue
        modified_flag = True
        polygon_points = shape["points"]

        if target_shape == "rotation":
            rect = cv2.minAreaRect(np.array(polygon_points, dtype=np.float32))
            box = cv2.boxPoints(rect).tolist()
            # print(box)
            adjust_rectangle_coordinates(box, img_w, img_h)
            # print(box)
            shape["points"] = box
            shape["direction"] = calculate_rotation_theta(box)
        elif target_shape == "rectangle":
            x, y, w, h = cv2.boundingRect(np.array(polygon_points, dtype=np.float32))
            rect_points = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
            for p in rect_points:
                p[0] = max(0.0, min(p[0], img_w))
                p[1] = max(0.0, min(p[1], img_h))
            shape["points"] = rect_points
        shape["shape_type"] = target_shape

    if modified_flag:
        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=2)
            print(f"write {json_file_path}")
    else:
        print(f"no change to {json_file_path}")


def modify_json_folder(json_folder, target_shape="rotation", force_write=False):
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            modify_json_file(os.path.join(json_folder, filename), target_shape, force_write)
