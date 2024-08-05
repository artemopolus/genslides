import json
import os
import genslides.utils.loader as ld
import copy


class RequestHelper:
    def __init__(self) -> None:
        self.dict = []
        with open(os.path.join('config','prompt.json'), 'r') as reader:
            input = json.load(reader)
            self.dict = input

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
                value = self.dict[type][flag]
                if isinstance(value, dict):
                    if value['type'] == 'path':
                        return True, ld.Loader.getUniPath(value['value'])
                return True, value
        return False, None


    def getNames(self) -> str:
        return self.dict
    
    def getParams(self, type: str) -> list[bool, list]:
        res, value = copy.deepcopy( self.getValue(type, 'params') )
        if res and isinstance(value, list):
            return res, value
        return False, None

