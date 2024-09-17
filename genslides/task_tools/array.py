import json
import genslides.task_tools.text as TextTool

def divideArray(data, param):
    print('Divide array')
    parse_type = param['parse']
    if parse_type == 'std':
        arr = data.split(';')
        for idx, word in enumerate( arr ):
            if len(word) > 0:
                if word[0] == ' ':
                    word = word[1:]
                if word[-1] == ' ':
                    word = word[:-1]
                arr[idx] = word
        if len(arr) > 0:
            return True, arr
    elif parse_type == 'text_split' and 'parts' in param and 'smbl_before' in param and 'smbl_after' in param:
        if 'part_smbl_cnt' in param and param['parts'] == 0:
            cuts = TextTool.split_text_with_context(data, param['part_smbl_cnt'],param['smbl_before'], param['smbl_after'])
        else:
            cuts = TextTool.cut_text_into_parts(data, param['parts'],param['smbl_before'], param['smbl_after'])
        if len(cuts) > 0:
            return True, [{'start':cut['Start Index of Text'],'end':cut['End Index of Text']} for cut in cuts]
    return False, []

def getArrayByIndex(array, index, param, src_data):
    parse_type = param['parse']
    if parse_type == 'std':
        return array[index]
    elif parse_type == 'text_split':
        start = array[index]['start']
        end = array[index]['end']
        return src_data[start:end]
    return ''

def checkCurrentArrayElem(array, index, param, current, src_data):
    parse_type = param['parse']
    if parse_type == 'std':
        return current != array[index]
    elif parse_type == 'text_split':
        start = array[index]['start']
        end = array[index]['end']
        return current != src_data[start:end]
    return True

def saveArrayToParams(data : str, param : dict):
    print('Save array to params', param)
    param ['src_data' ]= TextTool.compute_sha256_hash(data)

    if 'parse' in param:
        res, arr = divideArray(data, param)
        if res:
            curr = getArrayByIndex(arr, 0, param, data)
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

def updateArrayParam(data, param :dict):
    try:
        res, arr = divideArray(data, param)
        if res:
            param['array'] = arr
            param['curr'] = getArrayByIndex(arr, 0, param, data)
            param['idx'] = 0
        else:
            param['array'] = []
            param['curr'] = ""
            param['idx'] = 0
    except Exception as e:
        print('Update array param error:', e)
    return param

def iterateOverArrayFromParam(param: dict, data):
    print('Iterate over array from param', param)
    if 'type' in param and param['type'] == 'array':
        if 'array' in param and 'curr' in param and 'idx' in param:
            idx = param["idx"]
            if idx < len(param["array"]) - 1:
                if idx == 0 and checkCurrentArrayElem(param['array'], idx, param, param['curr'], data):
                    pass
                else:
                    idx += 1
                param["curr"] = getArrayByIndex(param['array'], idx, param, data)
                param["idx"] = idx
    return param

def checkArrayIteration(data : str, param : dict):
    if 'type' in param and param['type'] == 'array':
        if 'src_data' in param and param['src_data'] == TextTool.compute_sha256_hash( data ) :
            return iterateOverArrayFromParam(param, data)
        else:
            res, out = saveArrayToParams(data, param)
            if res:
                return out
    return param
        
