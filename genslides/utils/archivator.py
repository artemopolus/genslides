import py7zr
from os import listdir
from os.path import isfile, join


class Archivator():

    def saveOnlyFiles(src_path, trg_path, name):
        onlyfiles = [f for f in listdir(src_path) if isfile(join(src_path, f))]
        first = True
        for file in onlyfiles:
            if first:
                with py7zr.SevenZipFile( trg_path + name + ".7z", 'w') as archive:
                    archive.write(src_path + file, arcname = file)
                first = False
            else:
                with py7zr.SevenZipFile( trg_path + name + ".7z", 'a') as archive:
                    archive.write(src_path + file, arcname = file)

    def saveAll(src_path, trg_path, name):
        with py7zr.SevenZipFile( trg_path + name + ".7z", 'w') as archive:
            archive.writeall(src_path)

