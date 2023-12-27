import py7zr
import os
from os import listdir
from os.path import isfile, join


class Archivator():

    def saveOnlyFiles(src_path, trg_path, name):
        onlyfiles = [f for f in listdir(src_path) if isfile(join(src_path, f))]
        first = True
        res_trg_path = join(trg_path, name + ".7z")
        for file in onlyfiles:
            res_src_path = join(src_path, file)
            if first:
                with py7zr.SevenZipFile( res_trg_path, 'w') as archive:
                    print('write',res_src_path,'to', res_trg_path)
                    archive.write(res_src_path, arcname = file)
                first = False
            else:
                with py7zr.SevenZipFile( res_trg_path, 'a') as archive:
                    print('append',res_src_path,'to', res_trg_path)
                    archive.write(res_src_path, arcname = file)

    def saveAll(src_path, trg_path, name):
        print('Archivator save from',src_path,'to', trg_path,'with name', name)
        res_trg_path = join(trg_path , name + ".7z")
        with py7zr.SevenZipFile( res_trg_path, 'w') as archive:
            print('write',src_path,'to', res_trg_path)
            archive.writeall(src_path, arcname='')
        return
        # Archivator.saveOnlyFiles(src_path, trg_path, name)
        # onlyfolders = [f for f in listdir(src_path) if not isfile(join(src_path, f))]
        # res_trg_path = join(trg_path , name + ".7z")
        # for fld in onlyfolders:
        #     if fld != 'tmp':
        #         ctrl = 'w'
        #         if os.path.exists(res_trg_path):
        #             ctrl = 'a'
        #         with py7zr.SevenZipFile( res_trg_path, ctrl) as archive:
        #             res_src_path = join(src_path , fld)
        #             print('write',res_src_path,'to', res_trg_path)
        #             archive.writeall(res_src_path, arcname=fld)

    def extractFiles(trg_path, filename, path_to_extract):
        onlyfiles = [f for f in listdir(trg_path) if isfile(join(trg_path, f))]
        if filename + ".7z" not in onlyfiles:
            return False
        with py7zr.SevenZipFile(join(trg_path, filename + ".7z"), 'r') as archive:
            archive.extractall(path=path_to_extract)
        return True
