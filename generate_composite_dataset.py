from utils.utility import *
from utils.rotation import creat_single_x
from utils.fusion import combine_image


def create_composite_base(_data_folder_path, _output_dir, dataset_name, label_type="obb"):
    dataset_path = os.path.join(_output_dir, dataset_name)
    makedir(dataset_path, True)

    src_labels_folder = os.path.join(_data_folder_path, "labels" if label_type == "obb" else "labels_rect")
    copy_folder(src_labels_folder, os.path.join(dataset_path, "labels"), 1)

    output_images_path = os.path.join(dataset_path, "images")

    for sub_folder in ["train", "val"]:
        dst_dir = os.path.join(output_images_path, sub_folder)
        makedir(dst_dir)

        img1_folder = os.path.join(_data_folder_path, "images", sub_folder)
        img2_folder = os.path.join(_data_folder_path, "image", sub_folder)

        for filename in os.listdir(img1_folder):
            img1_path = os.path.join(img1_folder, filename)
            img2_path = os.path.join(img2_folder, filename)
            combine_image(img1_path, img2_path, os.path.join(dst_dir, filename))

    gen_yaml(dataset_path, dataset_name)


if __name__ == "__main__":
    gen_name = "ag_composite_obb"
    gen_type = "obb"  # "obb" or "rect"
    rotate_angle_step = 90  # x8

    base_path = os.getcwd()
    data_folder_path = os.path.join(base_path, "data")
    output_dir = base_path

    if not os.path.exists(data_folder_path):
        print(f"Error: The data folder does not exist at {data_folder_path}")
    elif not any(os.scandir(data_folder_path)):  # check empty
        print(f"Error: The data folder at {data_folder_path} is empty.")
    else:
        temp_dir = os.path.join(base_path, "temp")
        makedir(temp_dir, True)
        temp_name = f"{gen_name}_base"
        create_composite_base(data_folder_path, temp_dir, temp_name, gen_type)
        creat_single_x(rotate_angle_step, os.path.join(temp_dir, temp_name), output_dir, gen_name, gen_type)
