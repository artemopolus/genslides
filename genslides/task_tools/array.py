import json

def saveArrayToParams(data : str, param : dict):
    print('Save array to params', param)
    if 'parse' in param:
        if param['parse'] == 'std':
            arr = data.split(';')
            if len(arr) > 0:
                curr = arr[0]
                idx = 0
            else:
                return False, {}
        else:
            return False, {}
    else:
        return False, {}
    out = {
        "src_data" : data,
        "curr": curr,
        "idx": idx,
        "array": arr
    }
    param.update(out)
    return True, param

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
        
