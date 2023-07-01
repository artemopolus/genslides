import sys
sys.path.append("J:\\WorkspaceFast\\ThirdParty\\exmathlib\\python\\exactolink\\build\\Debug")
import ExactolinkPy


class Mliner():
    def __init__(self) -> None:
        self.man = ExactolinkPy.ZmqDevSec(7)
        self.sending_process = False
        self.max_len = 900
        self.pack_input = ""


    def isDataGetted(self) -> bool:
        return self.man.get_request

    def isDataSended(self) -> bool:
        return self.man.is_sended
    

    def checkData(self):
        if self.man.get_request:
            self.man.get_request = False
            indata = self.man.responded_str
            print(10*"======", "get part=", self.man.responded_prt)
            if self.man.responded_prt == 0:
                self.pack_input += indata
                return True
            else:
                self.pack_input += indata
        return False


    def update(self):
        self.man.update()
        print("cnt=", self.man.getCounter())
        print("sndcnt=", self.man.getSendCounter())
        if self.sending_process and self.man.is_sended:
            i = self.index
            print("Send process=",i)
            if self.last > 0:
                part_trg = self.parts - i
                if self.index == self.parts:
                    short_msg = self.msg[len(self.msg)-self.last :]
                    print("Send last=", len(short_msg))
                    self.man.sending(self.id, self.reg, 0, short_msg)
                    self.sending_process = False
                    return

            else:
                part_trg = self.parts - i - 1
                if self.index == self.parts:
                    print("Send last")
                    self.sending_process = False
                    return
            
                    
            short_msg = self.msg[i*self.max_len: ((i+1) * self.max_len)]
            print("=========>Send [", part_trg, "][", i*self.max_len,":", ((i+1) * self.max_len), "]=", len(short_msg))
            self.man.sending(self.id, self.reg, part_trg, short_msg)



            self.index += 1



    def upload(self, msg: str, id: int, reg=0):
        if len(msg) < self.max_len:
            self.man.sending(id, reg, 0, msg)
        else:
            self.last = len(msg) % self.max_len
            self.parts = int((len(msg) - self.last) / self.max_len)
            self.id = id
            self.reg = reg
            self.msg = msg
            self.index = 0
            self.sending_process = True

    def close(self):
        pass
