import ExactolinkPy
import sys

sys.path.append(
    "J:\\WorkspaceFast\\ThirdParty\\exmathlib\\python\\exactolink\\build\\Debug")


class Mliner():
    def __init__(self) -> None:
        self.man = ExactolinkPy.ZmqDevSec(7)

    def update(self):
        if self.man.get_request:
            print("Get request")
            # break

        if self.man.is_sended:
            print("Send success")
            # break

        self.man.update()
        print("cnt=", self.man.getCounter())
        print("sndcnt=", self.man.getSendCounter())

    def upload(self, msg: str, id: int, reg=0):
        max_len = 900
        if len(msg) < max_len:
            self.man.sending(id, reg, 0, msg)
        else:
            last = len(msg) % max_len
            parts = int((len(msg) - last) / max_len)
            add = 0
            if parts > 0:
                add = 1
            for i in range(0, parts):

                self.man.sending(id, reg, parts - i + add,
                                 msg[i*max_len: ((i+1) * max_len)])

            if parts > 0:
                self.man.sending(id, reg, 0, msg[(max_len - last):])
