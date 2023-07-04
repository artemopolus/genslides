import sys
sys.path.append("J:\\WorkspaceFast\\ThirdParty\\exmathlib\\python\\exactolink\\build\\Debug")
import ExactolinkPy


class MlinerCallback(ExactolinkPy.ZmqDevCallback):
    def process(self, data):
        print(("Get data=", len(data)))


class Mliner():
    def __init__(self) -> None:
        self.man = ExactolinkPy.ZmqDevSec(7)
        self.sending_process = False
        self.max_len = 900
        self.pack_input = ""
        self.call = MlinerCallback()
        self.man.init()


    def isDataGetted(self) -> bool:
        return self.man.get_request

    def isDataSended(self) -> bool:
        return self.man.is_sended
    


    def update(self):
        self.man.update(self.call)
        # print("cnt=", self.man.getCounter())
        # print("sndcnt=", self.man.getSendCounter())


    def upload(self, msg: str, id: int, reg=0):
        self.man.sending(id, reg, msg)

    def close(self):
        pass
