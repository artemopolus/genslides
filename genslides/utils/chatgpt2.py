import llmodel as llm
import json


path_to_config = 'config/openai.json'

with open(path_to_config, 'r') as config:
    values = json.load(config)
    key = values['api_key']


chat = llm.LLModel({'type':'model','model':'gpt-3.5-turbo'})

res, msg, p = chat.createChatCompletion([{"role": "user", "content": "Hello!"}])

print(p)

print(json.dumps(p))



