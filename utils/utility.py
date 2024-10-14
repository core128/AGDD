import os
import shutil


def makedir(_dir, delete_if_exist=False):
    if os.path.exists(_dir):
        if delete_if_exist:
            shutil.rmtree(_dir)
            os.makedirs(_dir)
    else:
        os.makedirs(_dir)


def copy_file(_src, _dst, log_level=2):
    if os.path.exists(_src):
        shutil.copyfile(_src, _dst)
        if log_level > 1:
            print(f"copy: {_src} -> {_dst}")
    else:
        if log_level > 0:
            print(f"source file not found: {_src}")


def copy_folder(_src, _dst, log_level=2):
    if os.path.exists(_src):
        shutil.copytree(_src, _dst)
        if log_level > 1:
            print(f"copy: {_src} -> {_dst}")
    else:
        if log_level > 0:
            print(f"source file not found: {_src}")


def gen_yaml(output_folder_path, dataset_name):
    s = f"""\
# parent
# ├── ultralytics
# └── datasets
#     └── {dataset_name}

# Train/val/test sets as 1) dir: path/to/imgs, 2) file: path/to/imgs.txt, or 3) list: [path/to/imgs1, path/to/imgs2, ..]
path: ../datasets/{dataset_name} # dataset root dir
train: images/train # train images (relative to 'path')
val: images/val # val images (relative to 'path')
#test: images/test # test images (optional)

# Classes
names:
  0: contusion
  1: scratches
  2: crack
  3: spot
"""
    with open(os.path.join(output_folder_path, dataset_name + ".yaml"), "w", encoding='utf-8') as f:
        f.write(s)
