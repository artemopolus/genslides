# import distutils.dir_util
import os
from os import listdir
from os.path import isfile, join, isdir
import shutil
from pathlib import Path
# import distutils

import setuptools
import datetime

def deleteFolder( mypath ):
    shutil.rmtree( mypath )

def deleteFile( mypath):
    if isfile (mypath):
        os.remove(mypath)

def deleteFiles(mypath):
    print('Delete files by path', mypath)
    for f in listdir(mypath):
        f_path = join(mypath, f)
        if isfile(f_path):
            os.remove(f_path)
        else:
            shutil.rmtree(f_path)

def copyDirToDir(src_path : str, trg_path : str):
    createFolder(trg_path)
    files = setuptools.dist.Command.copy_tree(infile=src_path, outfile=trg_path)
    
    # files = distutils.dir_util.copy_tree(src=src_path, dst=trg_path)
    # print('Copy:\n', files)

def copyFile(filepath, folderpath):
    srcpath = Path(filepath)
    trgpath = Path(folderpath) / srcpath.name
    shutil.copyfile(srcpath, trgpath)


def copyFiles(src_folder, trg_folder, trg_files = [], exld_files = []):
    if len(trg_files):
        files = trg_files
    else:
        files = listdir(src_folder)
    createFolder(trg_folder)
    idx = 0
    print('Copy',len(files),'files from', src_folder,'to', trg_folder,':', trg_files,'except', exld_files)
    for file in files:
        if file not in exld_files:
            path = join(src_folder, file)
            if isfile(path):
                idx += 1
                shutil.copyfile(path, join(trg_folder, file))
    print('Copied files count:', idx)

def createFolder(path):
    if not os.path.exists( path ):
        Path( path ).mkdir( parents=True, exist_ok=True )        

def addFolderToPath(path : str, folder_names : list[str]) -> str:
    dir = Path(path)
    for name in folder_names:
        dir = dir / name
    return str( dir )

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

def checkExistPath(path : str):
    return os.path.exists(path)

def getFilesInFolder(path: str):
    if not os.path.exists(path):
        return []
    return [f for f in listdir(path) if isfile(join(path, f))]

def getFilesPathInFolder(path: str):
    return [join(path,f) for f in listdir(path) if isfile(join(path, f))]

def getFilenamesFromFilepaths( paths : list[str]):
    return [Path(p).name for p in paths]

def getClearFilenamesFromFilepaths( paths : list[str]):
    return [Path(p).stem for p in paths]

def getFoldersInFolder(path:str):
    return [f for f in listdir(path) if isdir(join(path, f))]

def checkDirsContent(dirpath1 : str, dirpath2 : str) -> bool:
    files1 = getFilesInFolder(dirpath1)
    files2 = getFilesInFolder(dirpath2)
    return files1 == files2

def getFileName(path:str):
    return Path(path).stem


def manageOldestFolderFiles(folder_path, max_files=10):
    """
    Checks the number of files in a given folder and removes the oldest file
    (based on modification time) if the count exceeds a specified maximum.

    Args:
        folder_path (str): The path to the folder to manage.
        max_files (int): The maximum number of files allowed in the folder.
                         If the count exceeds this, the oldest file will be removed.
                         Defaults to 10.

    Returns:
        bool: True if a file was removed, False otherwise.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist or is not a directory.")
        return False

    try:
        # Get all files in the folder (excluding subdirectories)
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        # If the number of files is within the limit, do nothing
        if len(files) <= max_files:
            print(f"Folder '{folder_path}' contains {len(files)} files, which is within the limit of {max_files}.")
            return False

        print(f"Folder '{folder_path}' contains {len(files)} files, exceeding the limit of {max_files}.")

        # Get modification times for all files and store them as (timestamp, filepath) tuples
        file_times = []
        for f in files:
            try:
                # os.path.getmtime returns the time of last modification as a float
                # We'll use this directly for comparison
                mod_time = os.path.getmtime(f)
                file_times.append((mod_time, f))
            except OSError as e:
                print(f"Warning: Could not get modification time for '{f}': {e}")
                continue

        if not file_times:
            print("No files found to manage (or error getting times for all files).")
            return False

        # Sort files by modification time (oldest first)
        file_times.sort()

        # The first element after sorting is the oldest file
        oldest_file_mod_time, oldest_file_path = file_times[0]

        # Convert timestamp to human-readable format for logging
        oldest_file_datetime = datetime.datetime.fromtimestamp(oldest_file_mod_time)

        print(f"Identified oldest file: '{oldest_file_path}' (Last modified: {oldest_file_datetime})")

        # Remove the oldest file
        os.remove(oldest_file_path)
        print(f"Successfully removed oldest file: '{oldest_file_path}'")
        return True

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False



