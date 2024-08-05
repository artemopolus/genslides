from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained('NousResearch/Hermes-2-Pro-Llama-3-8B', trust_remote_code=True)

example = "This is a tokenization example"

encoded = tokenizer.encode(example, return_tensors='pt', add_special_tokens=False)
print(encoded[0])
decoded = tokenizer.decode(encoded[0])
print(decoded)
