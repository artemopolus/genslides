class Response:
    def __init__(self, type, info, nums) -> None:
        self.type = type
        self.info = info
        self.nums = nums


class Requester:
    def __init__(self) -> None:
        pass
    def getResponse(self, prompt)-> Response:
        return None

