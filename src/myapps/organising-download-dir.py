# automation.py
import os
from os.path import isfile, join
from shutil import move

# directory paths

user = os.getenv("USER")
target_parent = "mock_downloads_dir"
root_dir = "/home/{}/{}".format(user, target_parent)
image_dir = "/home/{}/{}/images".format(user, target_parent)
documents_dir = "/home/{}/{}/documents".format(user, target_parent)
others_dir = "/home/{}/{}/others".format(user, target_parent)
software_dir = "/home/{}/{}/softwares".format(user, target_parent)

# category wise file types

doc_types = (".doc", ".docx", ".txt", ".pdf", ".xls", ".ppt", ".xlsx", ".pptx")
img_types = (".jpg", ".jpeg", ".png", ".svg", ".gif", ".tif", ".tiff")
software_types = (".exe", ".pkg", ".dmg", "deb")


def get_non_hidden_files_except_current_file(root_dir):
    return [
        f
        for f in os.listdir(root_dir)
        if isfile(join(root_dir, f))
        and not f.startswith(".")
        and not f.__eq__(__file__)
    ]


def create_directories(
    root_dir, image_path, documents_path, software_path, others_path
):
    dir_dict = {
        "image_dir": image_dir,
        "docs_dir": documents_dir,
        "software_dir": software_dir,
        "others": others_dir,
    }
    # print(dir_dict)
    for k, v in dir_dict.items():
        if os.path.isdir(v) == True:
            continue
        else:
            print(f"{k} not present. Creating '{v}'")
            os.mkdir(v)


def move_files(root_dir, files):
    for file in files:
        # file moved and overwritten if already exists
        if file.endswith(doc_types):
            move(os.path.join(root_dir, file), "{}/{}".format(documents_dir, file))
            print("file {} moved to {}".format(file, documents_dir))
        elif file.endswith(img_types):
            move(os.path.join(root_dir, file), "{}/{}".format(image_dir, file))
            print("file {} moved to {}".format(file, image_dir))
        elif file.endswith(software_types):
            move(os.path.join(root_dir, file), "{}/{}".format(software_dir, file))
            print("file {} moved to {}".format(file, others_dir))
        else:
            move(os.path.join(root_dir, file), "{}/{}".format(others_dir, file))
            print("file {} moved to {}".format(file, others_dir))


if __name__ == "__main__":
    files = get_non_hidden_files_except_current_file(root_dir)
    create_directories(root_dir, image_dir, documents_dir, software_dir, others_dir)
    move_files(root_dir, files)
