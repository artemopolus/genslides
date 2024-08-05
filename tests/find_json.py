import json
def find_json(text : str):
    brackets="[]{}"
    opening, closing = brackets[::2], brackets[1::2]
    stack = [] # keep track of opening brackets types
    json_found = False
    found_first = False
    first_index = -1
    last_index = -1
    index = -1;
    for character in text:
        index += 1
        if character in opening: # bracket
            if not found_first:
                found_first = True
                first_index = index
            stack.append(opening.index(character))
        elif character in closing: # bracket
            if stack and stack[-1] == closing.index(character):
                stack.pop()  # remove the matched pair
                last_index = index + 1
            else:
                json_found = False
    if len(stack) == 0 and first_index != -1 and last_index != -1:
        json_found = True
        return text[first_index : last_index]
    return ''

def find_keys(trg_keys, text, out ):
    out = []
    if isinstance(text, dict):
        found = True
        for key in trg_keys:
            if key not in text:
                found = False
        if found:
            return out, True
        else:
            for key in text:
                out,res = find_keys(trg_keys, text[key], out)
                if res:
                    return out, res
            return out, False
    elif isinstance(text, list):
        found = False
        for val in text:
            out, res = find_keys(trg_keys, val, out)
            if res:
                found = True
            else:
                found = False
        if found:
            out = text
        return out, found

# with open('../examples/01info_present1_resp.txt','r') as text:
#     inp = text.read()
#     # print(inp)
#     trg = (find_json(inp))
#     loaded = json.loads(trg)
#     out = []
#     out, res = find_keys(['ratings', 'search'], loaded,out)
#     print('output=',out)

def searchJsonTemplate(json_input, lookup_key):
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if k == lookup_key:
                yield json_input
            else:
                yield from searchJsonTemplate(v, lookup_key)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from searchJsonTemplate(item, lookup_key)
def getJsonByKey(json_input, lookup_key):
    out = []
    for i in searchJsonTemplate(json_input, lookup_key[0]):
        found = True
        for key in lookup_key:
            if key not in i:
                found = False
        if found:
            out.append(i)
    return out

print('test')
tmpl = [{'hello':0, 'bye':'test'},{'hello':1, 'bye':'test'},{'hello':2, 'bye':'test'}]

trg = {'array':tmpl}

def print_gen(trg):
    for i in searchJsonTemplate(trg,'hello'):
        print(i)

print_gen(trg)

trg = {'array':[tmpl]}

print_gen(trg)

trg = [{'array':tmpl}]

print_gen(trg)

print('===============================')

trg = {
    'some':[
        {
            'yes':[
                {
                    'test':
                        [
                        {'array':tmpl}
                        ]
                }
            ],
            'some4':{'hello':9, 'bye':'test'}
        }
        ],
    'done':tmpl,
    'some2':{'hello':7, 'sun':'test'}
        }
print_gen(trg)

print('===============================')

print(getJsonByKey(trg, ['hello','bye']))
print(getJsonByKey(trg, ['hello']))
