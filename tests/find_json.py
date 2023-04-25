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

with open('../examples/01info_present1_resp.txt','r') as text:
    inp = text.read()
    # print(inp)
    trg = (find_json(inp))
    loaded = json.loads(trg)
    out = []
    out, res = find_keys(['ratings', 'search'], loaded,out)
    print('output=',out)
