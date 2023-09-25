import os


class ReadFileMan():
    def readPartitial(self, s_path, s_start):
        if os.path.isfile(s_path):
            div = s_path.split('.')[-1]
            if div == '.txt' or div == '.json':
                pass
            else:
                return True, "There is file on path: " + s_path
            with open(s_path, 'r',encoding='utf-8') as f:
                text = f.read()
            start = s_start
            stop = start + s_start
            if len(text) > stop*8:
                med = int((len(text) - stop)/2)
                return True, "This is parts of file:\n\n" + text[start:stop] + "...\n\n..." + text[med:med + stop]  + "...\n\n..." + text[len(text) - stop :]
            if len(text) > stop*4:
                return True, "This is parts of file:\n\n" + text[start:stop] + "...\n\n..." + text[len(text) - stop :]
            if len(text) > stop:
                return True, "This is part of file:\n\n" + text[start:stop]
        else:
            return False, "There is no any files on path: " + s_path

