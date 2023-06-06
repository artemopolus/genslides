from genslides.task.base import TaskDescription
from genslides.task.response import ResponseTask
from genslides.utils.largetext import SimpleChatGPT


class LargeTextResponseTask(ResponseTask):
    def __init__(self, task_info: TaskDescription, type="LargeTextResponse") -> None:
        super().__init__(task_info, type)

    def divide(self, text_part, tok, step=1000, m_tokens=4000) -> str:
        len_part = 0
        i_part = ""
        index = 0
        while index < 1000 and step*index < len(text_part):
            prev_part = i_part
            if (step*(index + 1)) > len(text_part):
                i_part += text_part[step*index:]
            else:
                i_part += text_part[step*index: (step*(index + 1))]
            index += 1
            # len_part = len(tok.encode(i_part))
            len_part = tok(i_part)
            if len_part > m_tokens:
                return prev_part
        return i_part

    def getParts(self, in_text, tok, step=1000, m_tokens=4000):
        i = 0
        parts = []
        while i < 10:
            part = self.divide(in_text, tok, step=step, m_tokens=m_tokens)
            if part == "":
                break
            in_text = in_text[len(part):]
            parts.append(part)
            i += 1
        return parts

    def executeResponse(self):
        chat = SimpleChatGPT()
        text = ""
        for msg in self.msg_list:
            text += msg["content"]
        tokens_all = chat.getTokensCount(text)
        last = self.msg_list[-1]["content"]
        tokens_last = chat.getTokensCount(last)
        if chat.max_tokens < tokens_all:
            print("too many tokens")
            m_tok = chat.max_tokens - tokens_all + tokens_last
            parts = self.getParts(last, chat.getTokensCount, 1000, m_tok)
            if parts:
                print("Parts count=", len(parts))
                msgs = self.msg_list.copy()
                sum = ""
                for p in parts:
                    msgs[-1]["content"] = p
                    res, out = chat.recvRespFromMsgList(msgs)
                    if res:
                        print("From assistant=", out)
                        sum += out +'\n'
                if sum != "":
                    self.msg_list.append({"role" : chat.getAssistTag(), "content": sum})
        else:
            res, out = chat.recvRespFromMsgList(self.msg_list)
            if res:
                # print("out=", out)
                pair = {}
                pair["role"] = chat.getAssistTag()
                pair["content"] = out
                self.msg_list.append(pair)
