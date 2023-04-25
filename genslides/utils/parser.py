

def find_json(text : str):
    brackets="[]{}"
    opening, closing = brackets[::2], brackets[1::2]
    stack = [] # keep track of opening brackets types
    json_found = False
    found_first = False
    first_index = -1
    last_index = -1
    index = 0;
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
                last_index = index
            else:
                json_found = False
    if len(stack) == 0:
        json_found = True
        return text[first_index : last_index]
    return ''