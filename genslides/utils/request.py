class Response:
    def __init__(self, type, info) -> None:
        self.type = type
        self.info = info


class Requester:
    def __init__(self) -> None:
        pass
    def getResponse(self, prompt):
        return ""

class TestRequester(Requester):
    def getResponse(self, prompt):
        output = []
        if "Presentation" in prompt:
            output.append( Response("Slide", "Slide with text"))
            output.append( Response("Slide", "Slide with image"))
            output.append( Response("Slide", "Slide with table"))
        return output