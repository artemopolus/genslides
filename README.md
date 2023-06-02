# Intro

Prompt generator for Language model like GPT (like ChatGPT)

# Quick start


```shell
python -m venv .env
```

## for win:

```shell
.env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m nltk.downloader popular
```

## graphviz win
download and install from here: https://www.graphviz.org/download/

## graphviz ubuntu

```shell
sudo apt-get install graphviz
```
## Get OpenAI API

Here https://platform.openai.com/account/api-keys 

## Get Google API

Use this https://developers.google.com/docs/api/quickstart/python 

# How to use

 - Copy config folder from examples to root and input your api

 - Copy your API in google.json and openai.json

 - Run command below

```shell
python -m genslides
```


# Update (notes)
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

Also, you can check this video:

[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/tOZpFCOcqNA/0.jpg)](http://www.youtube.com/watch?v=tOZpFCOcqNA)

# Contributing 

Contributions are always welcome!

# How to support

Give star to project :)

Like this video https://youtu.be/tOZpFCOcqNA :)

# Key targets

- More examples
- Better user interface
- Add options for model switching
- Add finally logging :)
- Documentation

# Contacts

exactosim@gmail.com
