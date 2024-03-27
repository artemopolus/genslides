import json


class RequestHelper:
    def __init__(self) -> None:
        # print('Read prompt from config')
        self.dict = []
        with open('config/prompt.json', 'r') as reader:
            input = json.load(reader)
            self.dict = input
        # for val in self.dict:
            # print(str(val) + '=>' + str(self.dict[val]))
        # print('Get dictionary reading is done')
    def getPrompt(self, type, info):
        if type in self.dict:
            return self.dict[type]['Init'] + info + self.dict[type]['Endi']
        return ""
    def getInit(self, type):
        if type in self.dict:
            return self.dict[type]['Init']
        return ""
    def getEndi(self, type):
        if type in self.dict:
            return self.dict[type]['Endi']
        return ""
    
    def getValue(self, type, flag):
        if type in self.dict:
            if flag in self.dict[type]:
                return True, self.dict[type][flag]
        return False, None


    def getNames(self) -> str:
        return self.dict
    
    def getParams(self, type: str) -> list[bool, dict]:
        res, value = self.getValue(type, 'params')
        if res and isinstance(value, dict):
            return res, value
        return False, None

