import os
import json

class ReadFileMan():
    def readWithHeader(s_path:str, header: str):
        text = header
        text += 10*"=" + '\n'
        text += ReadFileMan.readStandart(s_path)
        text += 10*"=" + '\n'
        return text
    
    def readJson(s_path: str):
        print('Read json by path:', s_path)
        text = {}
        with open(s_path,'r',encoding='utf-8') as f:
            text = json.load(f)
        return text
    
    def readStandart(s_path: str):
        with open(s_path, 'r',encoding='utf-8') as f:
            text = f.read()
        return text
    def readPartitial( s_path, s_start):
        if os.path.isfile(s_path):
            div = s_path.split('.')[-1]
            if div == 'txt' or div == 'json':
                pass
            else:
                return True, "There is file on path: " + s_path
            text = ReadFileMan.readStandart(s_path)
            start = s_start
            stop = start + s_start
            if len(text) > stop*8:
                med = int((len(text) - stop)/2)
                return True, "This is parts of file("+s_path+")\n\n" + text[start:stop] + "...\n\n..." + text[med:med + stop]  + "...\n\n..." + text[len(text) - stop :]
            if len(text) > stop*4:
                return True, "This is parts of file("+s_path+")\n\n" + text[start:stop] + "...\n\n..." + text[len(text) - stop :]
            if len(text) > stop:
                return True, "This is part of file("+s_path+")\n\n" + text[start:stop]
        return False, "There is no any files on path: " + s_path

