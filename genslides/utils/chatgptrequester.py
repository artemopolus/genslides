from genslides.utils.request import Requester
from genslides.utils.request import Response
from genslides.utils.largetext import SimpleChatGPT

import genslides.utils.parser as pr

import json

class ChatGPTsimple(Requester):
    def __init__(self) -> None:
        super().__init__()
    def getResponse(self, prompt)->str:
        chat = SimpleChatGPT()
        res, text = chat.recvResponse(prompt)
        if res:
            return text
        return ""
       


class ChatGPTrequester(Requester):
    def __init__(self) -> None:
        super().__init__()

    def getResponse(self, prompt: str, trgs : list = ['name','ratings', 'search']) -> Response:
        chat = SimpleChatGPT()
        res, text = chat.recvResponse(prompt)
        output = []
        if not res:
            print("Bad response")
            return output
        print("text=", text)
        trg_json = pr.find_json(text)
        print("found json=", trg_json)
        loaded = json.loads(trg_json)
        out = []
        out, res = pr.find_keys(trgs, loaded, out)
        if res:
            print('Get output')
            for elem in out:
                item = Response()
                for trg in trgs:
                    if trg in elem:
                        value = elem[trg]
                    else:
                        c_trg = trg.capitalize()
                        value = elem[c_trg]
                    item.addTrg(trg, value)
                output.append( item )
        return output
