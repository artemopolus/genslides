import json, re, os

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename, askdirectory, askopenfilenames

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
            print('Can\'t find json object in txt', arr)
            return False, None
        # print(prop)
        try:
            val = json.loads(prop, strict=False)
            return True, val
        except Exception as e:
            print('Raise err:', e,'\nInput:\n', prop)
            pass

        # print('Can\'t find json object in txt', arr)
        return False, None
    
    def convertFilePathToTag(path, manager_path):
        filename = PurePosixPath(path)
        mfilename = Loader.checkManagerTag(path, manager_path, False)
        if filename == mfilename:
            return Loader.checkManagerTag(path, manager_path)
        return filename
    
    def getFilePathArrayFromSysten(manager_path = '') ->list[str]:
        app = Tk()
        app.withdraw()  
        app.attributes('-topmost', True)
        filename_src = list( askopenfilenames() )
        if manager_path != '':
            out = []
            for path in filename_src:
                out.append(Loader.convertFilePathToTag(path, manager_path))
        return filename_src
 
    def getFilePathFromSystemRaw(filetypes = None) -> Path:
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
        path = Path(filepath)
        if manager_path != '':
            return Loader.convertFilePathToTag(path, manager_path)
        return str(PurePosixPath(path))
    
    def checkManagerTag(path, manager_path, to_par_fld = True):
        try:
            mpath = Path(manager_path)
            tag = 'spc'
            if to_par_fld:
                tag = 'fld'
                mpath = mpath.parent.parent
            rel_path = path.relative_to(mpath)
            str_rel_path = str(PurePosixPath(rel_path))
            filename = '[[manager:path:'+ tag +']]/'+ str_rel_path
        except Exception as e:
            print('Manager folder is not relative:',e)
            filename = PurePosixPath(path)
            return path
        return filename

    
    def getDirPathFromSystem(manager_path = '') -> str:
        app = Tk()
        app.withdraw() # we don't want a full GUI, so keep the root window from appearing
        app.attributes('-topmost', True)
        dirpath = askdirectory() # show an "Open" dialog box and return the path to the selected file
        path = Path(dirpath)
        filename = PurePosixPath(path)
        if manager_path != '':
            mfilename = Loader.checkManagerTag(path, manager_path, False)
            if filename == mfilename:
                return Loader.checkManagerTag(path, manager_path)
        return str(filename)
    
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
        


