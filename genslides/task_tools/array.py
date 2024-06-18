import json

def divideArray(data, parse_type):
    print('Divide array')
    if parse_type == 'std':
        arr = data.split(';')
        for idx, word in enumerate( arr ):
            last_char_str = 0
            last_char_end = len(word) - 1
            if last_char_end > 1:
                if word[0] == ' ':
                    word = word[1:]
                if word[-1] == ' ':
                    word = word[:-1]
                arr[idx] = word
        if len(arr) > 0:
            return True, arr
    return False, []


def saveArrayToParams(data : str, param : dict):
    print('Save array to params', param)
    param ["src_data" ]= data

    if 'parse' in param:
        res, arr = divideArray(data, param['parse'])
        if res:
            curr = arr[0]
            idx = 0
        else:
            return False, param
    else:
        return False, param
    out = {
        "curr": curr,
        "idx": idx,
        "array": arr
    }
    param.update(out)
    return True, param

def updateArrayParam(param :dict):
    try:
        res, arr = divideArray(param['src_data'], param['parse'])
        if res:
            param['array'] = arr
            param['curr'] = arr[0]
            param['idx'] = 0
    except Exception as e:
        print('Update array param error:', e)
    return param

def iterateOverArrayFromParam(param: dict):
    print('Iterate over array from param', param)
    if 'type' in param and param['type'] == 'array':
        if 'array' in param and 'curr' in param and 'idx' in param:
            idx = param["idx"]
            if idx < len(param["array"]) - 1:
                if idx == 0 and param['curr'] != param['array'][idx]:
                    pass
                else:
                    idx += 1
                param["curr"] = param["array"][idx]
                param["idx"] = idx
    return param

def checkArrayIteration(data : str, param : dict):
    if 'type' in param and param['type'] == 'array':
        if 'src_data' in param and param['src_data'] == data:
            return iterateOverArrayFromParam(param)
        else:
            res, out = saveArrayToParams(data, param)
            if res:
                return out
    return param
        
