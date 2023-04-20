import nltk.data

tokenizer = nltk.data.load('nltk:tokenizers/punkt/english.pickle')

result = tokenizer.tokenize('Hello. This is a test. It works!')

print(result)

print(result[1])

print(result[1] =='This is a test.' )
print(result[1] =='This is not a test.' )
if "This is a test." in result:
    print('Yes')

if "This is a not test." in result:
    print('Yes2')