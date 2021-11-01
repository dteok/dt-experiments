# automation.py
import os
from os.path import isfile, join
from pathlib import Path
from shutil import move
from typing import List
import logging

# directory paths

BASE_PATH = Path(os.path.abspath(__file__)).parent.parent.parent.parent.parent.parent
TARGET_PARENT = "Downloads"  # change target location here; e.g. /home/username/{foobar}
TARGET_PARENT_PATH = f"{BASE_PATH}/{TARGET_PARENT}"

parent_images_path = f"{TARGET_PARENT_PATH}/images"
parent_documents_path = f"{TARGET_PARENT_PATH}/documents"
parent_others_path = f"{TARGET_PARENT_PATH}/others"
parent_softwares_path = f"{TARGET_PARENT_PATH}/softwares"

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


def create_directories(image_path, documents_path, software_path, others_path):
    """Creates necessary target directories for moving files to

    Arguments:
        image_path {string} -- the images directory.
        documents_path {string} -- the documents directory.
        software_path {string} -- the software/applications directory.
        others_path {string} -- the directory for files that do not belong to the above three.
    """
    dir_dict = {
        "image_dir": image_path,
        "docs_dir": documents_path,
        "software_dir": software_path,
        "others": others_path,
    }
    # print(dir_dict)
    for k, v in dir_dict.items():
        if os.path.isdir(v) == True:
            continue
        else:
            print(f"{k} not present. Creating '{v}'")
            os.mkdir(v)


def execution_report(files):
    numfiles = len(files)
    return f"\nMoved {numfiles} files to their locations. Nice and tidy now!"


def move_files(parent_dir, files):
    """Execute moving of file from source to target destination

    Arguments:
        parent_dir {string} -- base path, is actually the source
        files {string} -- file object to move
    """
    if files:
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

        print(execution_report(files))
    else:
        # print("No files to move!")
        logging.warning(
            f" `parent_dir` ({TARGET_PARENT_PATH}) has no files to organise!"
        )
        pass


if __name__ == "__main__":
    files = get_files(TARGET_PARENT_PATH)
    create_directories(
        parent_images_path,
        parent_documents_path,
        parent_softwares_path,
        parent_others_path,
    )
    move_files(TARGET_PARENT_PATH, files)
