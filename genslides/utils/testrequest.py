import nltk.data
from genslides.utils.request import Requester
from genslides.utils.request import Response
import json
import genslides.utils.parser as pr


class TestRequester(Requester):
    def __init__(self) -> None:
        super().__init__()
        self.tokenizer = nltk.data.load('nltk:tokenizers/punkt/english.pickle')
        self.path = "examples/"

    def getResponse(self, prompt : str):
        output = []
        text = self.tokenizer.tokenize(prompt)
        print('response on: ', prompt)
        for sent in text:
            # print(sent)
            if sent.startswith( "Give me json list of search actions" ):
                print('Search action')
                path = self.path + "01info_present1_chat.txt"
                with open(path, 'r') as input:
                    text = input.read()
                    trg = pr.find_json(text)
                    loaded = json.loads(trg)
                    out = []
                    out, res = pr.find_keys(['ratings', 'search'], loaded,out)
                    if res:
                        print('Get output')
                        for elem in out:
                            output.append(Response(type='Search',info=elem['search'], nums=elem['ratings']))
                return output
        if "Give me table." in text:
            output.append(Response("Cell", "Some info", [0,0]))
            return output
        if "Give me chart." in text:
            output.append(Response("Col", "East",[1.2]))
            return output
        if "Give me text input." in text:
            output.append(Response("Text", "Very usefull info",[]))
            return output
        if "Give me plot." in text:
            return output
        return output
