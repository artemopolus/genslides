import os
from os import listdir
from os.path import isfile, join
import shutil
from pathlib import Path


def deleteFiles(mypath):
    for f in listdir(mypath):
        f_path = join(mypath, f)
        if isfile(f_path):
            os.remove(f_path)
        else:
            shutil.rmtree(f_path)

def copyFiles(src_folder, trg_folder, trg_files = []):
    print('Copy files from', src_folder,'to', trg_folder,':', trg_files)
    if len(trg_files):
        files = trg_files
    else:
        files = listdir(src_folder)
    createFolder(trg_folder)
    for file in files:
        path = join(src_folder, file)
        if isfile(path):
            shutil.copyfile(path, join(trg_folder, file))

def createFolder(path):
    if not os.path.exists( path ):
        Path( path ).mkdir( parents=True, exist_ok=True )        

def createUniqueDir(path : str, folder :str, name : str) -> list[bool, Path]:
    print('Create in', path, 'folder',folder, 'target',name)
    ppath = Path(path)
    idx = 0
    while (idx < 1000):
        ext_pr_name = name + str(idx)
        rpath = ppath / folder / ext_pr_name
        if not rpath.exists():
            return True, rpath
        idx += 1
    return False, None

def getFilesInFolder(path: str):
    return [f for f in listdir(path) if isfile(join(path, f))]