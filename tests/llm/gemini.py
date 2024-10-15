import google.generativeai as genai
import os, json

path_to_config = 'config\models.json'
with open(path_to_config, 'r') as config:
    values = json.load(config)
    key = values['google']['api_key']

print(key)

genai.configure(api_key=key)

model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Write a story about a magic backpack.")
print(response.text)

