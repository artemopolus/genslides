import requests
from bs4 import BeautifulSoup

import nltk.data
from nltk.tokenize import word_tokenize, sent_tokenize


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re


tokenizer = nltk.data.load('nltk:tokenizers/punkt/russian.pickle')

options = Options()
# options.page_load_strategy = 'normal'
options.add_argument("start-maximized")
options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
)
options.add_experimental_option('excludeSwitches', ['enable-logging'])
path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
options.binary_location = path
driver = webdriver.Chrome(options=options)
print('Done')

driver.get("https://www.google.com")

# # user_id = 12345
# # url = 'http://www.kinopoisk.ru/user/%d/votes/list/ord/date/page/2/#list' % (user_id) # url для второй страницы
url = 'https://yandex.com.am/weather/?lat=55.75581741&lon=37.61764526' 

driver.get(url=url)

page_source = driver.execute_script("return document.body.outerHTML;")

soup = BeautifulSoup(page_source, "html.parser")

text = soup.get_text()

print(text)

result = tokenizer.tokenize(text)
print('Start tokens')
index = 0
tokens = [sent for sent in sent_tokenize(text) ]
for one in tokens:
    print('[', str(index),']\n',one)
    index += 1
    if(index > 5):
        break
input_str = text
matches = re.findall(r'(?<![ \t\n\r\f\v])[А-Я]+', input_str)
# Iterate through matches and add a space before each uppercase letter
for match in matches:
    input_str = input_str.replace(match, ' ' + match)

# Output modified string
print(input_str)  # "This IS a STRING with Some UPPERCASE letters"


print('Done')

