from transformers import GPT2Tokenizer
import openai
from openai import OpenAI
import json
import tiktoken
import os
import datetime

from genslides.utils.openai import openaiGetChatCompletion, openaiGetSmplCompletion




class LLModel():
    def __init__(self, params = None) -> None:
        if params == None:
            params = {'type':'model','model':'gpt-3.5-turbo'}
        path_to_config = 'config/models.json'

        self.temperature = None
        self.active = False 
        self.path = path_to_config
        self.path_to_file = "output/openai.json"


        model_name = params['model']
        self.params = params
        if 'temperature' in params:
            self.temperature = params['temperature']

        with open(path_to_config, 'r') as config:
            models = json.load(config)
            for name, values in models.items():
                for option in values['prices']:
                    if option['name'] == model_name:
                        if name == 'openai':
                            if model_name == 'gpt-3.5-instruct':
                                self.method = openaiGetSmplCompletion
                            else:
                                self.method = openaiGetChatCompletion
                        self.vendor = name
                        self.model = model_name
                        self.max_tokens = option["max_tokens"]
                        self.input_price = option["input"]
                        self.output_price = option["output"]
                        self.api_key = values['api_key']
                        self.params['api_key'] = values['api_key']
                        self.active = values['active']
                        self.path_to_file = os.path.join('output', name+'.json')
                        if 'max_tokens' not in self.params:
                            self.params['max_tokens'] = option['max_tokens']


    def createChatCompletion(self, messages) -> (bool, str):
        if not self.active:
            return False, ''
        messages = self.checkTokens(messages)
        res, response, intok, outtok = self.method(messages, self.params)
        self.addCounterToPromts(intok, self.input_price)
        self.addCounterToPromts(outtok, self.output_price)
        return res, response


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
    
    def getPrice(self, text)-> float:
        tokens = self.getTokensCount(text)
        price = self.input_price
        return tokens, tokens * price/1000

    def getUserTag(self) -> str:
        return "user"
    
    def getAssistTag(self) -> str:
        return "assistant"
    
    def getSystemTag(self) -> str:
        return "system"

    def checkTokens(self, in_msgs: list):
        msgs = in_msgs.copy()
        text = ''
        for msg in msgs:
            text += msg["content"]
        token_cnt = self.getTokensCount(text)
        # print("Get response[", token_cnt,"]=",msgs[-1]["content"])

        if token_cnt > self.max_tokens:
            # try divide last
            # it's too many of them!
            idx = 0
            while (idx < 1000 and token_cnt > self.max_tokens):
                msgs.pop(0)
                text = ""
                for msg in msgs:
                    text += msg["content"]
                token_cnt = self.getTokensCount(text)
                idx += 1
        return msgs
    
