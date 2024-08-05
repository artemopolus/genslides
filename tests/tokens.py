from transformers import AutoTokenizer

# tokenizer = AutoTokenizer.from_pretrained("mistralai/Mixtral-8x7B-Instruct-v0.1")
tokenizer = AutoTokenizer.from_pretrained("openchat/openchat-3.5-1210")

chat = [
  {"role": "user", "content": "Hello, how are you?"},
  {"role": "assistant", "content": "I'm doing great. How can I help you today?"},
  {"role": "user", "content": "I'd like to show off how chat templating works!"},
]

# tokenizer.apply_chat_template(chat, tokenize=False)
print(tokenizer.apply_chat_template(chat, tokenize=False))


# Generate