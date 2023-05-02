from transformers import GPT2Tokenizer
import openai
from openai.error import APIError, RateLimitError, APIConnectionError
import json
import tiktoken



class ChatGPT():
    def __init__(self, model_name = "gpt-3.5-turbo") -> None:
        path_to_config = 'config/openai.json'
        self.model = model_name
        with open(path_to_config, 'r') as config:
            values = json.load(config)
            key = values['api_key']
            openai.api_key = key
            print('key=',key)

            models = openai.Model.list()
            for model in models.data:
                if model.id == self.model:
                    print('model=',model)
        self.path = path_to_config

    def add_counter_to_prompts(self, token_num = 1, price = 0.002):
        with open(self.path,'r') as f:
            val = json.load(f)
            iter = float(val['counter'])
            sum_price = token_num*price/1000
            print('price= ',sum_price)
            val['counter'] = iter + sum_price
        with open(self.path,'w') as f:
            json.dump(val,f,indent=1)

    def createChatCompletion(self, messages, model="gpt-3.5-turbo"):
        try:
            completion = openai.ChatCompletion.create(
            model=model,
            messages=messages        
            )
            msg = completion.choices[0].message
            text = msg["content"]
            return True, text
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

class SimpleChatGPT(ChatGPT):
    def __init__(self, model_name="gpt-3.5-turbo") -> None:
        super().__init__(model_name)
    def recvResponse(self, request : str):
        messages=[
            {"role": "user", "content": request}
        ]
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        token_cnt = len(tokenizer.encode(request))
        self.add_counter_to_prompts(token_cnt)
        return self.createChatCompletion(messages=messages)



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
