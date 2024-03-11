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
            print('Can\'t find json object in txt')
            return False, None
        # print(prop)
        try:
            val = json.loads(prop, strict=False)
            return True, val
        except:
            pass

        print('Can\'t find json object in txt')
        return False, None
    
    def getFilePathFromSystem() -> str:
        app = Tk()
        app.withdraw() # we don't want a full GUI, so keep the root window from appearing
        app.attributes('-topmost', True)
        filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file
        path = Path(filename)
        filename = PurePosixPath(path)
        return filename
    
    def getDirPathFromSystem() -> str:
        app = Tk()
        app.withdraw() # we don't want a full GUI, so keep the root window from appearing
        app.attributes('-topmost', True)
        filename = askdirectory() # show an "Open" dialog box and return the path to the selected file
        path = Path(filename)
        filename = PurePosixPath(path)
        return filename
    
    def getUniPath(path : str) -> str:
        out = Path(path)
        if platform == 'win32':
            out = PureWindowsPath(out)
        return out

