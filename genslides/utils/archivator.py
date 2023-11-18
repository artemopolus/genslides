import py7zr
import os
from os import listdir
from os.path import isfile, join


class Archivator():

    def saveOnlyFiles(src_path, trg_path, name):
        onlyfiles = [f for f in listdir(src_path) if isfile(join(src_path, f))]
        first = True
        for file in onlyfiles:
            tpathname = os.path.join(trg_path, name + ".7z")
            srcpathfile = os.path.join(src_path, file)
            if first:
                with py7zr.SevenZipFile( tpathname , 'w') as archive:
                    archive.write(srcpathfile, arcname = file)
                first = False
            else:
                with py7zr.SevenZipFile( tpathname, 'a') as archive:
                    archive.write(srcpathfile, arcname = file)

    def saveAll(src_path, trg_path, name):
        print('Archivator save all')
        Archivator.saveOnlyFiles(src_path, trg_path, name)
        onlyfolders = [f for f in listdir(src_path) if not isfile(join(src_path, f))]
        print(onlyfolders)
        for fld in onlyfolders:
            if fld != 'tmp':
                with py7zr.SevenZipFile( trg_path + name + ".7z", 'w') as archive:
                    ppath = os.path.join(src_path, fld)
                    print('Archive write=',ppath)
                    archive.writeall(ppath)

    def extractFiles(trg_path, filename, path_to_extract):
        onlyfiles = [f for f in listdir(trg_path) if isfile(join(trg_path, f))]
        if filename + ".7z" not in onlyfiles:
            return False
        with py7zr.SevenZipFile(trg_path + filename + ".7z", 'r') as archive:
            archive.extractall(path=path_to_extract)
        return True
