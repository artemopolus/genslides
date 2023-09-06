from transformers import GPT2Tokenizer
import openai
from openai.error import APIError, RateLimitError, APIConnectionError, ServiceUnavailableError
import json
import tiktoken
import os
import datetime

class ChatGPT():
    def __init__(self, model_name="gpt-3.5-turbo") -> None:
        path_to_config = 'config/openai.json'

        self.temperature = None

        self.active = False 
        with open(path_to_config, 'r') as config:
            values = json.load(config)
            key = values['api_key']
            openai.api_key = key
            self.active = values['active']

        if not key and not self.active:
            print("chat gpt model not active")
            return

        models = openai.Model.list()
        mdl_found = False
        # print("model name=", model_name)
        for mdl in models.data:
            if mdl.id == model_name:
                mdl_found = True
                # print('Use model =',mdl)

        if mdl_found:
            self.model = model_name
        else:
            raise ValueError("Model name not found")
        
        with open(path_to_config, 'r') as config:
            values = json.load(config)
            key = values['prices']
            found = False
            for price_info in key:
                if price_info["name"] == self.model:
                    found = True
                    self.max_tokens = price_info["max_tokens"]
                    self.input_price = price_info["input"]
                    self.output_price = price_info["output"]
                    break
            if not found:
                raise ValueError("Specify prices plz")
             
        self.path = path_to_config
        self.path_to_file = "output/openai.json"

    def getModelList(self):
        out = []
        with open(self.path, 'r') as config:
            values = json.load(config)
            key = values['prices']
            for price_info in key:
                out.append(price_info["name"])
        return out
 

    def getMaxTokensNum(self) -> int:
        return self.max_tokens

    def setTemperature(self, temp : float):
        if temp >= 0 and temp <= 2:
            self.temperature = temp

    def getModelNames(self):
        models = openai.Model.list()
        model_names = []
        for model in models.data:
            model_names.append(model.id)
        return model_names
    
    def getTokensCountFromChat(self, msgs):
        text = ""
        for msg in msgs:
            text += msg["content"]
        return self.getTokensCount(text)
  
    def getTokensCount(self, text) -> int:
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        token_cnt = len(tokenizer.encode(text))
        return token_cnt
    
    def getPrice(self, text)-> float:
        tokens = self.getTokensCount(text)
        price = 0.002
        return tokens, tokens * price/1000
 
    
    def getDefaultName(self):
        return "gpt-3.5-turbo"

    def addCounterToPromts(self, token_num = 1, price = 0.002):
        sum_price = token_num*price/1000
        print('price= ',sum_price)

        with open(self.path,'r') as f:
            val = json.load(f)
            iter = float(val['counter'])
            val['counter'] = iter + sum_price
        with open(self.path,'w') as f:
            json.dump(val,f,indent=1)

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

    def getSpentToday(self):
        with open(self.path_to_file, 'r') as f:
            cur_date = str(datetime.date.today())
            days = json.load(f)
            for day in days:
                if 'date' in day and day['date'] == cur_date and 'sum' in day:
                    return day['sum']
        return 0

        

    def createChatCompletion(self, messages, model="gpt-3.5-turbo"):
        if not self.active:
            raise ValueError("ChatGPT is not active!")
            # return False, ""
        try:
            print("use model=", self.model)
            print("Send msgs=",len(messages))
            if not self.temperature:
                completion = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages     
                )
            else:
                print("Cur temp=", self.temperature)
                completion = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature     
                )
            msg = completion.choices[0].message
            # text = msg["content"]
            print("Get Chat response=",len(completion.choices[0].message))
            return True, msg
        except RateLimitError as e:
            print('fuck rate')
            print(e)
            print('status==>', e.http_status)
            return False, ""
        except APIError as e:
            print('fuck api')
            print(e)
            print('status==>', e.http_status)
            return False, ""
        except APIConnectionError as e:
            print('fuck api')
            print(e)
            print('status==>', e.http_status)
            return False, ""
        except ServiceUnavailableError as e:
            return False, ""
        except TimeoutError as e:
            print('timeot error')
            return False, ""

class SimpleChatGPT(ChatGPT):
    def __init__(self, model_name="gpt-3.5-turbo") -> None:
        # print("model name=", model_name)
        super().__init__(model_name)
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

    def recvResponse(self, request : str) -> str:
        messages=[
            {"role": "user", "content": request}
        ]
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        token_cnt = len(tokenizer.encode(request))
        self.addCounterToPromts(token_cnt)
        res, out = self.createChatCompletion(messages=messages)
        if res:
            token_cnt = len(tokenizer.encode(out["content"]))
            self.addCounterToPromts(token_cnt)
            return True, out["content"]
        else:
            return False, ""
        
    def getTokensCount(self, text) -> int:
        return len(self.tokenizer.encode(text))
        
    def chatCompletion(self, msgs):
            self.addCounterToPromts(token_cnt)
            res, out = self.createChatCompletion(messages=msgs)

            if res:
                token_cnt = self.getTokensCount(out["content"])
                self.addCounterToPromts(token_cnt)
                return True, out["content"]        
            return False, ""
    
    
    def recvRespFromMsgList(self, msgs):
        text = ""
        for msg in msgs:
            text += msg["content"]
        token_cnt = self.getTokensCount(text)
        # print("Get response[", token_cnt,"]=",msgs[-1]["content"])

        if token_cnt > self.max_tokens:
            # try divide last
            # it's too many of them!
            pass
        else:
            self.addCounterToPromts(token_cnt,price=self.input_price)
            res, out = self.createChatCompletion(messages=msgs)

            if res:
                token_cnt = self.getTokensCount(out["content"])
                self.addCounterToPromts(token_cnt, price= self.output_price)
                return True, out["content"]        
        return False, ""

    def getUserTag(self):
        return "user"
    def getAssistTag(self):
        return "assistant"



class Summator(ChatGPT):
    def __init__(self, model_name="gpt-3.5-turbo") -> None:
        super().__init__(model_name)

    def processText(self, text=""):
        print('Process text=',len(text))
        chunks = text.split('\n\n')
        ntokens = []
        print('init array=',len(chunks))
        max_len_chunk = 0
        for chunk in chunks:
            max_len_chunk = max(max_len_chunk, len(chunk))
        print('max token=',max_len_chunk)
        max_len = 800
        new_chunks = []
        for chunk in chunks:
            if(len(chunk) > max_len):
                index = 0
                while(len(chunk) > index + max_len):
                    new_chunks.append(chunk[index : index + max_len])
                    index += max_len
                if len(chunk) - index >= 0:
                    new_chunks.append(chunk[index::])
            else:
                new_chunks.append(chunk)
        chunks = new_chunks
        print('init array=',len(chunks))
        max_len_chunk = 0
        for chunk in chunks:
            max_len_chunk = max(max_len_chunk, len(chunk))
        print('max token=',max_len_chunk)
        del new_chunks
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        token_sum = 0
        for chunk in chunks:
            token_sum += len(tokenizer.encode(chunk))
            ntokens.append(len(tokenizer.encode(chunk)))
        print('max tokens=',max(ntokens))
        chunks = self.group_chunks(chunks, ntokens)
        print('array len=',len(chunks))
        max_len_chunk = 0
        for chunk in chunks:
            max_len_chunk = max(max_len_chunk, len(chunk))
        print('max token=',max_len_chunk)
        print('price=', "{:.2f}".format(token_sum/1000*0.002),'$')
        return chunks
        # return chunks, ntokens

    def group_chunks(self, chunks, ntokens, max_len=1000):
       #  """
       #  Group very short chunks, to form approximately a page long chunks.
       #  """
        batches = []
        cur_batch = ""
        cur_tokens = 0

    # iterate over chunks, and group the short ones together
        for chunk, ntoken in zip(chunks, ntokens):
            cur_tokens += ntoken + 2  # +2 for the newlines between chunks

        # if adding this chunk would exceed the max length, finalize the current batch and start a new one
            if ntoken + cur_tokens > max_len:
                batches.append(cur_batch)
                cur_batch = chunk
            else:
                cur_batch += "\n\n" + chunk
        batches.append(cur_batch)
        return batches
