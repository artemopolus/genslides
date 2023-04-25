import os
import openai
from openai.error import APIError, RateLimitError, APIConnectionError
import json

path_to_config = '../config/openai.json'


def add_counter_to_prompts():
    with open(path_to_config,'r') as f:
        val = json.load(f)
        iter = val['counter']
        val['counter'] = iter + 1
    with open(path_to_config,'w') as f:
        json.dump(val,f)

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
trg_req_name = '01info_present1'

with open('../examples/' + trg_req_name + '_req.txt','r') as f:
    prompt = f.read()
path_resp = '../examples/' + trg_req_name + '_chat.txt'
print(prompt)

response = False

# try:
#     completion = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "user", "content": prompt}
#         ]
#     )
#     print(completion.choices[0])
#     msg = (completion.choices[0].message)
#     print(msg)
#     text = msg["content"]
#     print(text)
#     with open('chatgpt_out.txt', 'w') as out:
#         out.write(text)
#     response = True
add_counter_to_prompts()
# except RateLimitError as e:
#     print('fuck rate')
#     print(e)
#     print('status==>', e.http_status)
# except APIError as e:
#     print('fuck api')
#     print(e)
#     print('status==>', e.http_status)
# except APIConnectionError as e:
#     print('fuck api')
#     print(e)
#     print('status==>', e.http_status)

print('Done=', response)

# print the first model's id
# print(models.data[0].id)

# # create a completion
# completion = openai.Completion.create(model="ada", prompt="Hello world")

# # print the completion
# print(completion.choices[0].text)
# response = openai.Completion.create(
#   model="text-davinci-003",
#   prompt="Convert this text to a programmatic command:\n\nExample: Ask Constance if we need some bread\nOutput: send-msg `find constance` Do we need some bread?\n\nReach out to the ski store and figure out if I can get my skis fixed before I leave on Thursday",
#   temperature=0,
#   max_tokens=100,
#   top_p=1.0,
#   frequency_penalty=0.2,
#   presence_penalty=0.0,
#   stop=["\n"]
# )
