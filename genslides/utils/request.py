from json import JSONEncoder

class Response(JSONEncoder):
    def default(self, o):
            return o.__dict__  
    
    def __init__(self, type = None, name = None, info = None, nums = None) -> None:
        self.type = type
        self.name = name
        self.info = info
        self.nums = nums
        self.trgs = {}

    def addTrg(self, trg, val):
         self.trgs[trg] = val


class Requester:
    def __init__(self) -> None:
        pass
    def getResponse(self, prompt)-> Response:
        return None

