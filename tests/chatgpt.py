import openai
from openai.error import APIError, RateLimitError, APIConnectionError
import json
import tiktoken







def addCounterToPromts(path, token_num = 1, price = 0.002):
    with open(path,'r') as f:
        val = json.load(f)
        iter = float(val['counter'])
        val['counter'] = iter + token_num*price/1000
    with open(path,'w') as f:
        json.dump(val,f,indent=1)


def num_tokens_from_messages(messages : list, model : str="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        print("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        print("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

def createChatCompletion(messages, model="gpt-3.5-turbo", path = "chatgpt_out.txt", config_path = "../config/openai.json"):
    try:
        completion = openai.ChatCompletion.create(
        model=model,
        messages=messages        
        )
        addCounterToPromts(path=config_path, token_num=num_tokens_from_messages(messages=messages, model=model))
        msg = completion.choices[0].message
        text = msg["content"]
        with open(path, 'w') as out:
          out.write(text)
        return True
    except RateLimitError as e:
        print('fuck rate')
        print(e)
        print('status==>', e.http_status)
        return False
    except APIError as e:
        print('fuck api')
        print(e)
        print('status==>', e.http_status)
        return False
    except APIConnectionError as e:
        print('fuck api')
        print(e)
        print('status==>', e.http_status)
        return False



path_to_config = '../config/openai.json'
with open(path_to_config, 'r') as config:
    values = json.load(config)
    key = values['api_key']


openai.api_key = key
print(key)

# list models
models = openai.Model.list()
# print(models.data)
for model in models.data:
   #  print(model.id)
    if model.id == "gpt-3.5-turbo":
        print(model)
   #  break

# prompt = "I understand only clear and strict instructions. Give me json list of search actions to improve my request and formatted as: name is short name, ratings is  necessity of action for improving from 1 to 10, search is prompt for searching and browsing action for improving creation, web is true if you can use search result directly in creation. I want to create: Bisness presentation for investors. My idea is presentation creation automatization. You just type your idea then y software propose your steps to create presentation and try to automatize it."
prompt = ''
# trg_req_name = '01info_present2'
# trg_req_name = '01info_present1'
# trg_req_name = '02slides_present1'
# trg_req_name = '02slides_present2'
# trg_req_name = '03parts_slide1'
# trg_req_name = '04text_parts_slides1'
# trg_req_name = '05table_parts_slides1'
trg_req_name = '06plot_parts_slides1'

with open('../examples/' + trg_req_name + '_req.txt','r') as f:
    prompt = f.read()
path_resp = '../examples/' + trg_req_name + '_chat.txt'

print(prompt)

messages=[
            {"role": "user", "content": prompt}
]
chatgpt_model="gpt-3.5-turbo"

# addCounterToPromts(path=path_to_config, token_num=num_tokens_from_messages(messages=messages, model=chatgpt_model))


print('Done=', createChatCompletion(messages, chatgpt_model, path_resp, path_to_config))

