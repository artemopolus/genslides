# Intro

Prompt generator for Language model like GPT (like ChatGPT)

# How to install

⚠️ Old version, please, don't use it. Also you can look in requirements.txt for manual installation.

pip install python-pptx
pip install gradio
pip install google-api-python-client
pip install bs4
pip install selenium 
pip install webdriver-manager
pip install nltk
python -m nltk.downloader popular
pip install --upgrade openai
pip install tiktoken
pip install transformers

# another way -- environments:

Main version now!

```shell
python -m venv .env
```

# for win:

```shell
.env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m nltk.downloader popular
```

# graphviz win
download and install from here: https://www.graphviz.org/download/

```shell
sudo apt-get install graphviz
```


# How to use

copy config folder from examples to root and input your api

```shell
python -m genslides
```


# update
```shell
python -m pip freeze > requirements.txt
python -m  pip install target_lib
```
# Limitation

Please, be carefull:
- It's just prototype! Report errors, please :)
- Watch your API key limits with OpenAI!

# Documentation

Not done yet.

Use "active" flag in openai.json for disabling debuging. If it is "false", then it will not send request via openai api

In examples you can find examples of projects for exploring: remember, copy this to root.

# Contributing 

Contributions are always welcome!


# How to support


