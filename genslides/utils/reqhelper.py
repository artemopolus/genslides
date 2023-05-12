import json


class RequestHelper:
    def __init__(self) -> None:
        print('Read prompt from config')
        self.dict = []
        with open('config/prompt.json', 'r') as reader:
            input = json.load(reader)
            self.dict = input
        for val in self.dict:
            print(str(val) + '=>' + str(self.dict[val]))
        print('Get dictionary reading is done')
    def getPrompt(self, type, info):
        if type in self.dict:
            return self.dict[type]['Init'] + info + self.dict[type]['Endi']
        return None
    def getInit(self, type):
        if type in self.dict:
            return self.dict[type]['Init']
        return None
    def getEndi(self, type):
        if type in self.dict:
            return self.dict[type]['Endi']
        return None

    def getNames(self) -> str:
        return self.dict
