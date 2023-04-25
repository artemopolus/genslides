from genslides.task.base import BaseTask

import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester

import nltk.data
from nltk.tokenize import word_tokenize

class InformationTask(BaseTask):
    def __init__(self,  parent, reqhelper : ReqHelper, requester :Requester, description) -> None:
        super().__init__(reqhelper, requester, type='Information', prompt=description)
        tokenizer = nltk.data.load('nltk:tokenizers/punkt/english.pickle')
        sents = tokenizer.tokenize(description)
        if len(sents) > 0:
            words = word_tokenize(sents[1])
            if 'presentation' in words or 'Presentation' in words:
                print('Found!!!!!')
