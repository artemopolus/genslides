import genslides.task_tools.text as TextTool
# import genslides.task.text as Txt

def divideArray(task  , param):
    print('Divide array')
    parse_type = param['parse']
    if parse_type == 'std':
        data = task.getLastMsgContent2()
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
        data = task.getLastMsgContent2()
        if 'part_smbl_cnt' in param and param['parts'] == 0:
            cuts = TextTool.split_text_with_context(data, param['part_smbl_cnt'],param['smbl_before'], param['smbl_after'])
        else:
            cuts = TextTool.cut_text_into_parts(data, param['parts'],param['smbl_before'], param['smbl_after'])
        if len(cuts) > 0:
            return True, [{'start':cut['Start Index of Text'],'end':cut['End Index of Text']} for cut in cuts]
    elif parse_type == 'msgs':
        messages = task.getMsgs()
        arr = []
        for msg in messages:
            arr.append( msg['content'] )
        if len(arr) > 0:
            return True, arr
    return False, []

def getArrayByIndex(array, index, param, task  ):
    parse_type = param['parse']
    if parse_type == 'std':
        return array[index]
    elif parse_type == 'text_split':
        src_data = task.getLastMsgContent2()
        start = array[index]['start']
        end = array[index]['end']
        return src_data[start:end]
    elif parse_type == 'msgs':
        return array[index]
    return ''

def checkCurrentArrayElem(array : list, index : int, param : dict, current, task  ):
    parse_type = param['parse']
    if parse_type == 'std':
        return current != array[index]
    elif parse_type == 'text_split':
        src_data = task.getLastMsgContent2()
        start = array[index]['start']
        end = array[index]['end']
        return current != src_data[start:end]
    elif parse_type == 'msgs':
        return current != array[index]
    return True

def saveArrayToParams(task  , param : dict):
    print('Save array to params', param)
    if param['parse'] == 'std' or param['parse'] == 'text_split':
        data = task.getLastMsgContent2()
    elif param['parse'] == 'msgs':
        messages = task.getMsgs()
        data = ''
        for msg in messages:
            data += msg['content'] 
    else:
        return False, param
    
    param ['src_data' ]= TextTool.compute_sha256_hash(data)

    if 'parse' in param:
        res, arr = divideArray(task, param)
        if res:
            curr = getArrayByIndex(arr, 0, param, task)
            idx = 0
        else:
            return False, param
    else:
        return False, param
    out = {}
    setArrayParamValues(out, arr, curr, idx)
    param.update(out)
    return True, param

def setArrayParamValues(param, array, current, idx):
    param['array'] = array
    param['curr'] = current 
    param['idx'] = idx
    param['len'] = len(array)


def updateArrayParam(task  , param :dict):
    try:
        res, arr = divideArray(task, param)
        if res:
            setArrayParamValues(param, arr, getArrayByIndex(arr, 0, param, task), 0)
        else:
            setArrayParamValues(param, [], "", 0)
    except Exception as e:
        print('Update array param error:', e)
    return param

def iterateOverArrayFromParam(task  , param: dict):
    print('Iterate over array from param', param)
    if 'type' in param and param['type'] == 'array':
        if 'array' in param and 'curr' in param and 'idx' in param:
            idx = param["idx"]
            if idx < len(param["array"]) - 1:
                if idx == 0 and checkCurrentArrayElem(param['array'], idx, param, param['curr'], task):
                    pass
                else:
                    idx += 1
                param["curr"] = getArrayByIndex(param['array'], idx, param, task)
                param["idx"] = idx
    return param

def checkArrayIteration(task  , param : dict):
    if 'type' in param and param['type'] == 'array':
        if 'src_data' in param and param['src_data'] == TextTool.compute_sha256_hash( task ) :
            return iterateOverArrayFromParam(task, param)
        else:
            res, out = saveArrayToParams(task, param)
            if res:
                return out
    return param
        
