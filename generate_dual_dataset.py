from utils.utility import *
from utils.rotation import creat_dual_x


def create_dual_base(_data_folder_path, _output_dir, dataset_name, label_type="obb"):
    include_folders = ["image", "images", ("labels" if label_type == "obb" else "labels_rect")]
    dataset_path = os.path.join(_output_dir, dataset_name)
    makedir(dataset_path, True)
    for folder_name in include_folders:
        src_path = os.path.join(_data_folder_path, folder_name)
        dst_path = os.path.join(dataset_path, folder_name.split('_')[0])
        copy_folder(src_path, dst_path, 1)
    gen_yaml(dataset_path, dataset_name)


if __name__ == "__main__":
    gen_name = "ag_dual_obb"
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
        create_dual_base(data_folder_path, temp_dir, temp_name, gen_type)
        creat_dual_x(rotate_angle_step, os.path.join(temp_dir, temp_name), output_dir, gen_name, gen_type)
