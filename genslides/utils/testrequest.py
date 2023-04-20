import nltk.data
from genslides.utils.request import Requester
from genslides.utils.request import Response


class TestRequester(Requester):
    def __init__(self) -> None:
        super().__init__()
        self.tokenizer = nltk.data.load('nltk:tokenizers/punkt/english.pickle')

    def getResponse(self, prompt):
        output = []
        text = self.tokenizer.tokenize(prompt)
        if "Give me presentation." in text:
            output.append(Response("Slide", "Slide with text",[0]))
            return output
        if "Give me title." in text:
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
