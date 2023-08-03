import sys
sys.path.append("J:\\WorkspaceFast\\ThirdParty\\exmathlib\\python\\exactolink\\build\\Debug")
import ExactolinkPy


class MlinerCallback(ExactolinkPy.ZmqDevCallback):
    
    def setMliner(self, mliner):
        self.mliner = mliner
    def process(self, data):
        print(("Get data=", len(data)))
        self.mliner.pack_input = data
        self.mliner.is_input = True


class Mliner():
    def __init__(self) -> None:
        self.man = ExactolinkPy.ZmqDevSec(7)
        self.man.initLogger()
        self.pack_input = ""
        self.call = MlinerCallback()
        self.call.setMliner(self)
        self.man.init()
        self.is_input = False


    def isDataGetted(self) -> bool:
        return self.is_input

    def isDataSended(self) -> bool:
        return self.man.is_sended
    
    def getResponse(self) -> str:
        out = self.pack_input
        print("Response=",out)
        self.pack_input = ""
        # print("Response=",out)
        self.is_input = False
        return out

    def update(self):
        self.man.update(self.call)
        # print("cnt=", self.man.getCounter())
        # print("sndcnt=", self.man.getSendCounter())


    def upload(self, msg: str, id: int, reg=0):
        print("Send msg size=", len(msg))
        self.man.sending(id, reg, msg)

    def close(self):
        pass
