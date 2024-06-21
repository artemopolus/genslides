from transformers import GPT2Tokenizer
from transformers import AutoTokenizer
# import openai
# from openai import OpenAI
import json
import tiktoken
import os
import datetime

from genslides.utils.myopenai import openaiGetChatCompletion, openaiGetSmplCompletion, openai_num_tokens_from_messages, openai_decode_token, openai_get_tokens_from_message
from genslides.utils.myollama import ollamaGetChatCompletion
from genslides.utils.myllamacpp import llamacppGetChatCompletion
# from myopenai import openaiGetChatCompletion, openaiGetSmplCompletion

model_to_method = {
    "openai":{
        'default':openaiGetChatCompletion,
        'gpt-3.5-turbo-instruct':openaiGetSmplCompletion
    },
    "ollama":{
        'default':ollamaGetChatCompletion
    },
    "llamacpp":{
        'default':llamacppGetChatCompletion
    }
}


class LLModel():
    def __init__(self, params = None) -> None:
        # print('Start llmodel with params=', params)
        if params == None:
            params = {'type':'model','model':'gpt-3.5-turbo'}
        path_to_config = os.path.join('config','models.json')

        self.temperature = None
        self.active = False 
        self.path = path_to_config
        self.path_to_file = os.path.join("output","openai.json")

        self.get_tokens_from_message = None
        self.tokenizer = None


        model_name = params['model']
        self.params = params
        if 'temperature' in params:
            self.temperature = params['temperature']

        with open(path_to_config, 'r') as config:
            models = json.load(config)
            for name, values in models.items():
                for option in values['prices']:
                    if option['name'] == model_name:
                        # if name == 'openai':
                        #     if model_name == 'gpt-3.5-turbo-instruct':
                        #         self.method = openaiGetSmplCompletion
                        #     else:
                        #         self.method = openaiGetChatCompletion
 
                        if model_name in model_to_method[name]:
                            self.method = model_to_method[name][model_name]
                        else:
                            self.method = model_to_method[name]['default']

                           
                        self.vendor = name
                        self.model = model_name
                        # self.max_tokens = option["max_tokens"]
                        # self.input_price = option["input"]
                        # self.output_price = option["output"]
                        # TODO: выбирать случайный ключ для генерации запроса
                        self.api_key = values['api_key']
                        self.params['api_key'] = values['api_key']
                        self.active = values['active']
                        self.path_to_file = os.path.join('output', name+'.json')
                        # if 'max_tokens' not in self.params:
                            # self.params['max_tokens'] = option['max_tokens']
                        self.params = option
                        self.params.update(params)


    def createChatCompletion(self, messages) -> (bool, str, dict):
        if not self.active:
            return False, '', {}
        token_cnt, _  = self.getPriceFromMsgs(messages)
        # print("Get response[", token_cnt,"]=",msgs[-1]["content"])

        if token_cnt > self.params['max_tokens']:
            return False, '', {}
        # print('Input Chat=', [[msg['role'], len(msg['content'])] for msg in messages])
        out = {
            'type' : 'response',
            'model': self.params['model'],
            'messages': messages
            }
        res, response, p = self.method(messages, self.params)
        if res and 'intok' in p and 'outtok' in p:
            intok = p['intok']
            outtok = p['outtok']
            out.update(p)

            # print('Res param=',p)
            self.addCounterToPromts(intok, self.params['input'])
            self.addCounterToPromts(outtok, self.params['output'])
        return res, response, out


    def addCounterToPromts(self, token_num = 1, price = 0.002):
        sum_price = token_num*price/1000
        print('price= ',sum_price)

        # with open(self.path,'r') as f:
        #     val = json.load(f)
        #     iter = float(val['counter'])
        #     val['counter'] = iter + sum_price
        # with open(self.path,'w') as f:
        #     json.dump(val,f,indent=1)

        cur_date = str(datetime.date.today())
        if os.path.exists(self.path_to_file):
            with open(self.path_to_file, 'r') as f:
                dates = json.load(f)
                found = False
                for dt in dates:
                    if dt["date"] == cur_date:
                        found = True
                        sum = dt["sum"] + sum_price
                        dt["sum"] = sum
                if not found:
                    dates.append({ "date" : cur_date, "sum" : sum_price})
            with open(self.path_to_file, 'w') as f:
                json.dump(dates,f,indent=1)
        else:
            with open(self.path_to_file, 'w') as f:
                val = []
                val.append({ "date" : cur_date, "sum" : sum_price})
                json.dump(val,f,indent=1)


    def getTokensCount(self, text) -> int:
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        token_cnt = len(tokenizer.encode(text))
        return token_cnt
    
    def getPriceFromMsgs(self, msgs):
        tokens = 0
        if self.vendor == 'openai':
            tokens = openai_num_tokens_from_messages(msgs, self.model)
        price = self.params['input']
        return tokens, tokens * price/1000

    
    def getPrice(self, text)-> float:
        tokens = self.getTokensCount(text)
        price = self.params['input']
        return tokens, tokens * price/1000

    def getUserTag(self) -> str:
        return "user"
    
    def getAssistTag(self) -> str:
        return "assistant"
    
    def getSystemTag(self) -> str:
        return "system"

    def checkTokens(self, in_msgs: list):
        msgs = in_msgs.copy()
        token_cnt, _  = self.getPriceFromMsgs(msgs)
        # print("Get response[", token_cnt,"]=",msgs[-1]["content"])

        if token_cnt > self.params['max_tokens']:
            # try divide last
            # it's too many of them!
            idx = 0
            while (idx < 1000 and token_cnt > self.params['max_tokens']):
                msgs.pop(0)
                text = ""
                for msg in msgs:
                    text += msg["content"]
                token_cnt = self.getTokensCount(text)
                idx += 1
        return msgs
    
    def getTokensFromMessage(self,message):
        if self.get_tokens_from_message == None:
            if self.vendor == 'openai':
                self.get_tokens_from_message = openai_get_tokens_from_message
            else:
                if 'pretrained_model_path' in self.params:
                    self.tokenizer = AutoTokenizer.from_pretrained(
                                    self.params['pretrained_model_path'], trust_remote_code=True)
                    self.get_tokens_from_message = self.internalGetTokensFromMessage
                else:
                    return []
        return self.get_tokens_from_message (message=message, model=self.params['model'])
    
    def internalGetTokensFromMessage(self,message, model):
        encoded = self.tokenizer.encode(message, return_tensors='pt', add_special_tokens=False)
        return encoded[0]
    
    
    def decodeToken(self,token):
        return openai_decode_token(token=token, model=self.params['model'])
    