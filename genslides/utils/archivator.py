import py7zr
import os
from os import listdir
from os.path import isfile, join

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import asksaveasfilename



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

    def getProjectFileName():
        app = Tk()
        app.withdraw() 
        app.attributes('-topmost', True)
        filepath = asksaveasfilename(defaultextension='.7z', initialfile='untitled.7z', confirmoverwrite=True, filetypes = [('Project archive','*.7z')]) 
        return filepath


    def saveAllbyPath(data_path, trgfile_path):
        if trgfile_path[-3:] != ".7z":
            print('Filename',trgfile_path,'is not 7z archive')
            return
        with py7zr.SevenZipFile( trgfile_path, 'w') as archive:
            archive.writeall(data_path, arcname='')
        print(f"Save data from {data_path} to {trgfile_path}")

    def saveAllbyName(src_path, trg_path, name):
        print('Archivator save from',src_path,'to', trg_path,'with name', name)
        res_trg_path = join(trg_path , name + ".7z")
        with py7zr.SevenZipFile( res_trg_path, 'w') as archive:
            print('write',src_path,'to', res_trg_path)
            archive.writeall(src_path, arcname='')
        return
    
    def extractFiles(trg_path, filename, path_to_extract):
        onlyfiles = [f for f in listdir(trg_path) if isfile(join(trg_path, f))]
        if filename + ".7z" not in onlyfiles:
            return False
        with py7zr.SevenZipFile(join(trg_path, filename + ".7z"), 'r') as archive:
            print('Extract all from',trg_path, filename,'to',path_to_extract)
            archive.extractall(path=path_to_extract)
        return True
