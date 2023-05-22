Presentation generator

#How to install

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

#another way -- environments:

python -m venv .env
#for win:
.env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m nltk.downloader popular

#graphviz win
download and install from here: https://www.graphviz.org/download/

sudo apt-get install graphviz


#How to use

copy config folder from examples to root and input your api

python -m genslides


#update
python -m pip freeze > requirements.txt
python -m  pip install target_lib
