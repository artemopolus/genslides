import os
import json
from pathlib import Path

def writeToFile(path, text, ctrl = 'w'):
    if not os.path.exists(path):
        lst_path = os.path.split(path)
        if not os.path.exists( lst_path[0]):
            Path(lst_path[0]).mkdir(parents=True, exist_ok=True)
        
    with open(path, ctrl, encoding='utf8') as f:
        f.write(text)

def writeJsonToFile(path, text, ctrl = 'w', indent = 1):
    if not os.path.exists(path):
        lst_path = os.path.split(path)
        if not os.path.exists( lst_path[0]):
            Path(lst_path[0]).mkdir(parents=True, exist_ok=True)
        
    with open(path, ctrl, encoding='utf8') as f:
        json.dump(obj=text, fp=f, indent=indent)

