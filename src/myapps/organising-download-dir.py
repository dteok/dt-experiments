import os
from os.path import isfile, join

# from pathlib import Path
from shutil import move
from typing import List
import logging

# directory paths

BASE_PATH = os.getenv("HOME")
TARGET_PARENT = "Downloads"  # change target location here; e.g. /home/username/{foobar}
TARGET_PARENT_PATH = f"{BASE_PATH}/{TARGET_PARENT}"

parent_images_path = f"{TARGET_PARENT_PATH}/images"
parent_documents_path = f"{TARGET_PARENT_PATH}/documents"
parent_others_path = f"{TARGET_PARENT_PATH}/others"
parent_softwares_path = f"{TARGET_PARENT_PATH}/softwares"

parent_paths = [
    parent_images_path,
    parent_documents_path,
    parent_others_path,
    parent_softwares_path,
]


# category wise file types

doc_types = (".doc", ".docx", ".txt", ".pdf", ".xls", ".ppt", ".xlsx", ".pptx")
img_types = (".jpg", ".jpeg", ".png", ".svg", ".gif", ".tif", ".tiff")
software_types = (".exe", ".pkg", ".dmg", "deb")


def get_files(parent_dir) -> List:
    """Returns a list containing every filenames in the
    `parent_dir`. Hidden or dot files are ignored

    Arguments:
        parent_dir {string} -- base path

    Returns:
        List -- Every filenames found in `parent_dir` (e.g. 'foobar.txt')
    """
    return [
        f
        for f in os.listdir(parent_dir)
        if isfile(join(parent_dir, f))
        and not f.startswith(".")
        and not f.__eq__(__file__)
    ]


def create_directories():
    """Creates necessary target directories for moving files to

    Arguments: None
    """

    for path in parent_paths:
        if not os.path.isdir(path):
            print(f"{dir} not present. Creating '{path}'")
            os.mkdir(path)


def execution_report(files):
    """Simple report on number of files moved. If no files, this function does nothing.

    Arguments:
        files {[type]} -- [description]
    """
    if files:
        print(f"\nMoved {len(files)} files to their locations. Nice and tidy now!")


def move_files(parent_dir, files):
    """Execute moving of file from source to target destination

    Arguments:
        parent_dir {string} -- base path, is actually the source
        files {string} -- file object to move
    """
    if not files:
        print("+-" * 20)
        logging.warning(f"'{TARGET_PARENT_PATH}' has no files to organise!")
        return

    for file in files:
        fpath = os.path.join(parent_dir, file)

        # file moved and overwritten if already exists
        if file.endswith(doc_types):
            move(fpath, f"{parent_documents_path}/{file}")
            print(f"file {file} moved to {parent_documents_path}")

        elif file.endswith(img_types):
            move(fpath, f"{parent_images_path}/{file}")
            print(f"file {file} moved to {parent_images_path}")

        elif file.endswith(software_types):
            move(fpath, f"{parent_softwares_path}/{file}")
            print(f"file {file} moved to {parent_softwares_path}")

        else:
            move(fpath, f"{parent_others_path}/{file}")
            print(f"file {file} moved to {parent_others_path}")


if __name__ == "__main__":
    files = get_files(TARGET_PARENT_PATH)
    create_directories()
    move_files(TARGET_PARENT_PATH, files)
    execution_report(files)
