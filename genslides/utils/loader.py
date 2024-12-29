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
    
    def convertJsonTextPartToMsg(md_text : str, index = 1):
        code_pattern = r'```json(.*?)```'
        parts = re.split(code_pattern, md_text, flags=re.DOTALL)
        text = ""
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Non-code parts treated as comments
                pass
            else:  # Code parts
                if i == index:
                # print("parts", part)
                    return part.strip()
        return md_text

    def convJsonToText(val, indent = None):
        return json.dumps(val, ensure_ascii=False, indent=indent)

    def loadJsonFromText(text : str, report = False):
        try:
            val = json.loads(text, strict=False)
            return True, val
        except Exception as e:
            if report:
                print("error:",e)

        try:
            prop = Loader.convertJsonTextPartToMsg(text)
            val = json.loads(prop, strict=False)
            return True, val
        except Exception as e:
            if report:
                print("error:",e)


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
        app.destroy()
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
        
        
    
    def getManRePath(trgpath, man_path, prefix = 'manager'):
        spath = Path(trgpath)
        mpath = Path(man_path)
        idx = 0
        while True:
            try:
                rpath = spath.relative_to(mpath)
                str_rel_path = str(PurePosixPath(rpath))
                if prefix == 'manager':
                    filename = '[[manager:path:sub_'+ str(idx) +']]/'+ str_rel_path
                else:
                    filename = prefix + str_rel_path
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

    def filter_dicts(json_string, target_key_values):
        """
        Filters a JSON array of dictionaries based on key-value pairs, handling string to number and boolean conversions.

        Args:
            json_string: A JSON string representing an array of dictionaries.
            target_key_values: A list of key-value pairs (keys at even indices, values at odd, always strings).

        Returns:
            A JSON string (encoded in cp1251) of the filtered dictionaries.
            Returns an empty string if any errors occur or no matches are found.
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError:
            return ""

        if not isinstance(data, list):
            return ""

        filtered_dicts = []
        for dictionary in data:
            if not isinstance(dictionary, dict):
                return ""

            is_match = True
            for i in range(0, len(target_key_values), 2):
                key = target_key_values[i]
                target_value_str = target_key_values[i + 1]  # Always a string

                if key not in dictionary:
                    is_match = False
                    break

                dict_value = dictionary[key]

                try:
                    if isinstance(dict_value, bool):  # Handle boolean conversion
                        if target_value_str.lower() == "true":
                            target_value = True
                        elif target_value_str.lower() == "false":
                            target_value = False
                        else:
                            target_value = target_value_str #  Keeps target value as string if it is not "true" or "false"

                    elif isinstance(dict_value, (int, float)): # Handle numeric conversion
                        try:
                            target_value = int(target_value_str)
                        except ValueError:
                            try:
                                target_value = float(target_value_str)
                            except ValueError:
                                target_value = target_value_str  # Keep as string
                    else:
                        target_value = target_value_str

                    # print(dict_value,'=', target_value)

                    if dict_value != target_value:
                        is_match = False
                        break


                except Exception as e: # Handle unexpected errors during conversion or comparison
                    print(f"Error during comparison: {e}")
                    return "" # Or handle the error in a more specific way


            if is_match:
                filtered_dicts.append(dictionary)

        if filtered_dicts:
            try:
                json_str = json.dumps(filtered_dicts, ensure_ascii=False, indent=2).encode('cp1251')
                # print(json_str.decode('cp1251'))
                return json_str.decode('cp1251')  # Return the encoded string
            except UnicodeEncodeError:
                print("Encoding error.  String could not be encoded in cp1251.")
                return "" # Return empty string in case of error
        else:
            return "" # Return empty string if no matches
 
       
    def remove_additional_properties(json_data, property_to_remove="additionalProperties"):
        """Recursively removes a specified property from a JSON object.

        Args:
            json_data: The JSON data (either a dict or a list) to process.
            property_to_remove: The name of the property to remove. 
                            Defaults to "additionalProperties".
        """

        if isinstance(json_data, dict):
            if property_to_remove in json_data:
                del json_data[property_to_remove]
            for key, value in json_data.items():
                json_data[key] = Loader.remove_additional_properties(value, property_to_remove)
        elif isinstance(json_data, list):
            for i in range(len(json_data)):
                json_data[i] = Loader.remove_additional_properties(json_data[i], property_to_remove)
        return json_data