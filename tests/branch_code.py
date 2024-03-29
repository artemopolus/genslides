import re

def break_string(s):
    parts = re.findall(r"[0-9]+|[A-Z][a-z]*", s)
    return parts

s = "So28So28Rq246Rq246Cl247Cl254Cl261Cl261Cl281"
result = break_string(s)
print(result)
