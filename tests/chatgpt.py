import json

from openai import OpenAI

path_to_config = 'config/openai.json'
with open(path_to_config, 'r') as config:
    values = json.load(config)
    key = values['api_key']


print(key)

# list models
chat = OpenAI(api_key=key)
models = chat.models.list()
print([t.id for t in models])
