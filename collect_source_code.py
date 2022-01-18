import os
from pathlib import Path
from shutil import copyfile

from tqdm import tqdm

# Uncomment to download dataset
# url = "http://files.srl.inf.ethz.ch/data/py150_files.tar.gz"

# #download 150k python dataset
# os.system(f"wget {url}")

""" Copies files from subdirectories in src_path to single directory dest_path for
    ease of handling. 
"""
def copy_files(src_path, dest_path, allow_non_empty=False, new_extension=False):

    # progress bar handling
    num_src_files = sum(len(files) for _, _, files in os.walk(src_path))
    num_dst_files = len(os.listdir(dest_path))

    if not allow_non_empty:
        assert num_dst_files == 0
    else:
        print("Copying Despite Exsiting Files in Dest")

    with tqdm(desc = "Files Copied", total=num_src_files) as pbar:
        for (root, dirs, files) in os.walk(src_path):
            for f in files:
                src = os.path.join(root, f)
                filename, ext = os.path.splitext(src[src.rfind('/')+1:])
                
                
                # renaming duplicates
                has_duplicate_name = True
                i = 0
                while has_duplicate_name:
                    # change extension
                    if new_extension: ext = new_extension
                    dest_name = filename + f"__{i}{ext}"
                    has_duplicate_name = os.path.isfile(f'{dest_path}/{dest_name}')

                    i += 1 

                #copying file to dest
                copyfile(src, f'{dest_path}/{dest_name}')
                # updates progress bar
                pbar.update(1)

src_path = "py150_files/data"
dest_path = "py150_files/just_files"
# copy_files(src_path, dest_path, new_extension=".txt")