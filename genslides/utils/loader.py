import json, re, os

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename, askdirectory, askopenfilenames, asksaveasfilename

from sys import platform

from pathlib import PureWindowsPath, Path, PurePosixPath


class Loader:

    def stringToList(text: str) -> list:
        output_paths = text.strip('][').split(',')
        out = []
        for ppath in output_paths:
            i = ppath.strip("\'")
            # print('from',ppath,'insert',i)
            out.append(i)
        # print('list path=',out)
        return out
    
    def stringToPathList(  text:str):
        pp = Loader.stringToList(text)

        for path in pp:
            # aps = path.strip('\'').split('\\')    
            # aps = list(filter(None, aps))
            # aps.pop()
            # aps = "\\".join(aps)
            # print(aps)
            # path = aps
            # print('Check',path)
            if not os.path.exists(path):
                return False, pp
        return True, pp


    def loadJsonFromText(text : str):
        # print(text)
        # results = re.findall(r'\{.*?\}', text)


        # print(results)
        # for res in results:
        prop = text
        arr = prop.split("{",1)
        if len(arr) > 1:
            prop = "{" + arr[1]
            for i in range(len(prop)):
                val = len(prop) - 1 - i
                if prop[val] == "}":
                    prop = prop[:val] + "}"
                    break
        else:
            # print('Can\'t find json object in txt', arr)
            return False, None
        # print(prop)
        try:
            val = json.loads(prop, strict=False)
            return True, val
        except Exception as e:
            # print('Raise err:', e,'\nInput:\n', prop)
            pass

        # print('Can\'t find json object in txt', arr)
        return False, None
    
    def convertFilePathToTag(path, manager_path):
        filename = PurePosixPath(Path(path))
        res, filename = Loader.checkManagerTag2(path, manager_path, False)
        if not res:
            res2, filename = Loader.checkManagerTag2(path, manager_path)
            if res2:
                return filename
        else:
            return filename
        return path
    
    def getFilePathToSave():
        app = Tk()
        app.withdraw() 
        app.attributes('-topmost', True)
        filepath = asksaveasfilename(defaultextension='.7z', initialfile='untitled.7z', confirmoverwrite=True, filetypes = [('Project archive','*.7z')]) 
        app.destroy()
        return filepath

    
    def getFilePathArrayFromSysten(manager_path = '') ->list[str]:
        app = Tk()
        app.withdraw()  
        app.attributes('-topmost', True)
        filename_src = list( askopenfilenames() )
        app.destroy()

        out_filenames = []
        for filepath in filename_src:
            out_filenames.append(Loader.getManRePath(filepath, manager_path))
        return out_filenames
 
    def getFilePathFromSystemRaw(filetypes = [('Project archive','*.7z')]) -> Path:
        app = Tk()
        app.withdraw() # we don't want a full GUI, so keep the root window from appearing
        app.attributes('-topmost', True)
        filepath = askopenfilename(filetypes=filetypes) # show an "Open" dialog box and return the path to the selected file
        return Path(filepath)
  
    def getDirPathFromSystemRaw() -> Path:
        app = Tk()
        app.withdraw() # we don't want a full GUI, so keep the root window from appearing
        app.attributes('-topmost', True)
        dirpath = askdirectory() # show an "Open" dialog box and return the path to the selected file
        return Path(dirpath)

    def getFilePathFromSystem(manager_path = '') -> str:
        app = Tk()
        app.withdraw() # we don't want a full GUI, so keep the root window from appearing
        app.attributes('-topmost', True)
        filepath = askopenfilename() # show an "Open" dialog box and return the path to the selected file
        app.destroy()
        return Loader.getManRePath(filepath, manager_path)
        # path = Path(filepath)
        # filename = PurePosixPath(path)
        # if manager_path != '':
        #     mfilename = Loader.checkManagerTag(path, manager_path, False)
        #     print(filename, mfilename, filename == mfilename)
        #     if Path(filename) == Path(mfilename):
        #         return Loader.checkManagerTag(path, manager_path)
        #     else:
        #         return mfilename
        # return str(filename)

    def checkManagerTag(spath, manager_path, to_par_fld = True):
        print('check')
        try:
            path = Path(spath)
            mpath = Path(manager_path)
            tag = 'spc'
            if to_par_fld:
                tag = 'fld'
                mpath = mpath.parent.parent
            rel_path = path.relative_to(mpath)
            print('Check manager tag', mpath, 'with', path,':', rel_path)
            str_rel_path = str(PurePosixPath(rel_path))
            filename = '[[manager:path:'+ tag +']]/'+ str_rel_path
        except Exception as e:
            print('Manager folder is not relative:',e,spath)
            filename = str(PurePosixPath(path))
            return filename
        return filename
    
    def restorePathUsingManPath(key : str, man_path):
        if key.startswith('sub'):
            index = int(key.split('_')[1])
            mpath = Path(man_path)
            npath = mpath
            for idx in range(index):
                npath = npath.parent
            if platform == 'win32':
                return str(PurePosixPath(npath))
            return str(npath)
        return man_path
        
        
    
    def getManRePath(trgpath, man_path):
        spath = Path(trgpath)
        mpath = Path(man_path)
        idx = 0
        while True:
            try:
                rpath = spath.relative_to(mpath)
                str_rel_path = str(PurePosixPath(rpath))
                filename = '[[manager:path:sub_'+ str(idx) +']]/'+ str_rel_path
                return filename
            except Exception as e:
                npath = mpath.parent
                if str(npath) == str(mpath):
                    return trgpath
                else:
                    mpath = npath
            idx += 1
            if idx > 1000:
                break
        return trgpath



    def checkManagerTagRe(dirpath, manager_path):
        path = Path(dirpath)
        filename = PurePosixPath(path)
        if manager_path != '':
            mfilename = Loader.checkManagerTag(path, manager_path, False)
            if Path(filename) == Path( mfilename):
                return Loader.checkManagerTag(path, manager_path)
            else:
                return mfilename
        return str(filename)
    
    def getDirPathFromSystem(manager_path = '') -> str:
        print('Get dir path from mpath',manager_path)
        app = Tk()
        app.withdraw() # we don't want a full GUI, so keep the root window from appearing
        app.attributes('-topmost', True)
        dirpath = askdirectory() # show an "Open" dialog box and return the path to the selected file
        app.destroy()
        return Loader.getManRePath(dirpath, manager_path)
   
  
    def getFolderPath(path : str, to_par_fld = True) -> str:
        out = Path(path)
        if to_par_fld:
            out = out.parent.parent
        if platform == 'win32':
            out = PurePosixPath(out)
        return str(out)
    
    def getUniPath(path: str) -> str:
        out = Path(path)
        if platform == 'win32':
            out = PureWindowsPath(out)
        return str(out)
    
    def getProgramFolder():
        return Loader.getUniPath( Path.cwd() )
    
    def comparePath( path1 : str, path2 : str):
        return Path( path1 ) == Path( path2 )
        

    def checkManagerTag2(spath, manager_path, to_par_fld = True) -> list[bool, str]:
        print('check')
        try:
            path = Path(spath)
            mpath = Path(manager_path)
            tag = 'spc'
            if to_par_fld:
                tag = 'fld'
                mpath = mpath.parent.parent
            rel_path = path.relative_to(mpath)
            print('Check manager tag', mpath, 'with', path,':', rel_path)
            str_rel_path = str(PurePosixPath(rel_path))
            filename = '[[manager:path:'+ tag +']]/'+ str_rel_path
        except Exception as e:
            print('Manager folder is not relative:',e,spath)
            filename = str(PurePosixPath(path))
            return False, filename
        return True, filename

 
