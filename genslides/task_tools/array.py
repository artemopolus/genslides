import genslides.task_tools.text as TextTool
import genslides.utils.loader as Ld
# import genslides.task.text as Txt

def divideArray(task  , param):
    # print('Divide array')
    parse_type = param['parse']
    if parse_type == 'std':
        data = task.getLastMsgContent2()
        arr = data.split(';')
        out = []
        for idx, word in enumerate( arr ):
            if len(word) > 0:
                if word[0] == ' ':
                    word = word[1:]
                if word[-1] == ' ':
                    word = word[:-1]
                arr[idx] = word
            out.append({"content": arr[idx], "idx": idx, "chck": False})
        if len(arr) > 0:
            return True, out
    elif parse_type == 'json':
        res, targets = Ld.Loader.loadJsonFromText(task.getLastMsgContent2())
        if res and isinstance(targets, list):
            arr = []
            for idx, content in enumerate( targets ):
                trg_idx  = idx
                chck = False
                if 'idx' in content:
                    trg_idx = content['idx']
                    del content['idx']
                if 'chck' in content:
                    chck = content['chck']
                    del content['chck']
                if 'content' in content:
                    text = content['content']
                else:
                    text = Ld.Loader.convJsonToText( content )
                arr.append(
                    {
                        'idx' : trg_idx,
                        'chck':chck,
                        'content': text
                    }
                )
                
            return True, arr
        else:
            print('No list in target json key')
    elif parse_type == 'text_split' and 'parts' in param and 'smbl_before' in param and 'smbl_after' in param:
        data = task.getLastMsgContent2()
        if 'part_smbl_cnt' in param and param['parts'] == 0:
            cuts = TextTool.split_text_with_context(data, param['part_smbl_cnt'],param['smbl_before'], param['smbl_after'])
        else:
            cuts = TextTool.cut_text_into_parts(data, param['parts'],param['smbl_before'], param['smbl_after'])
        if len(cuts) > 0:
            return True, [{'start':cut['Start Index of Text'],'end':cut['End Index of Text'], "idx": idx, "chck": False} for idx, cut in enumerate(cuts)]
    elif parse_type == 'msgs':
        messages = task.getMsgs()
        arr = []
        for idx, msg in enumerate(messages):
            arr.append({"content": msg["content"], "idx": idx, "chck": False})
        if len(arr) > 0:
            return True, arr
    return False, []

def getArrayByIndexPlusPlus( param, task  ):
    index = param['idx']
    array = param['array']

    if index < len(array) - 1:
        if not array[index]['chck']:
            param['idx'] = index
            return getPartByParam(task,param)
        index += 1
        while index < len(array):
            if not array[index]['chck']:
                param['idx'] = index
                return getPartByParam(task,param)
            index += 1
    else:
        return getPartByParam(task,param)
    return param

def getPartByParam(task, param):
    parse_type = param['parse']
    index = param['idx']
    array = param['array']
    array[index]['chck'] = True
    if parse_type in ['std','json','msgs']:
        param['curr'] = array[index]["content"]
    elif parse_type == 'text_split':
        src_data = task.getLastMsgContent2()
        start = array[index]['start']
        end = array[index]['end']
        param['curr'] = src_data[start:end]
    return param



def getArrayByIndex(array, index, param, task  ):
    parse_type = param['parse']
    if parse_type in ['std','json','msgs']:
        return array[index]["content"]
    elif parse_type == 'text_split':
        src_data = task.getLastMsgContent2()
        start = array[index]['start']
        end = array[index]['end']
        return src_data[start:end]
    return ''

def checkCurrentArrayElem(param : dict, task  ):
    current = param['curr']
    parse_type = param['parse']
    index = param['idx']
    array = param['array']
    if parse_type in ['std','json','msgs']:
        return current != array[index]["content"]
    elif parse_type == 'text_split':
        src_data = task.getLastMsgContent2()
        start = array[index]['start']
        end = array[index]['end']
        return current != src_data[start:end]
    return True

def getSHAfromTask(task, param):
    data = ''
    if param['parse'] == 'std' or param['parse'] == 'text_split':
        data = task.getLastMsgContent2()
    elif param['parse'] == 'msgs':
        messages = task.getMsgs()
        for msg in messages:
            data += msg['content'] 
    return TextTool.compute_sha256_hash(data)
 

def saveArrayToParams(task  , param : dict):
    print('Save array for', task.getName())
   
    # print('param',param)
    idx = param ['idx']
    if 'parse' in param:
        res, arr = divideArray(task, param)
        if res:
            curr = getArrayByIndex(arr, 0, param, task)
            idx = 0
        else:
            print('Cant divide into array')
            return False, param
    else:
        print('No parse parameter')
        return False, param
    out = {}
    setArrayParamValues(out, arr, curr, idx)
    param ['src_data' ]= getSHAfromTask(task, param)
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
            param ['src_data' ]= getSHAfromTask(task, param)
        else:
            setArrayParamValues(param, [], "", 0)
    except Exception as e:
        print('Update array param error:', e)
    return param

def iterateOverArrayFromParam(task  , param: dict):
    # print('Iterate over array from param', param)
    if 'type' in param and param['type'] == 'array':
        if 'array' in param and 'curr' in param and 'idx' in param:
            # idx = param["idx"]
            # if idx == 0 and checkCurrentArrayElem( param, task):
            #     pass
            # else:
            param = getArrayByIndexPlusPlus(param, task)
    return param

def checkArrayIteration(task  , param : dict):
    if 'type' in param and param['type'] == 'array':
        if 'src_data' in param and param['src_data'] == getSHAfromTask(task, param) :
            if task.manager.allowUpdateInternalArrayParam():
                return iterateOverArrayFromParam(task, param)
        else:
            res, out = saveArrayToParams(task, param)
            if res:
                return out
    return param

def resetArrayParam( task, param : dict):
    print('Reset array params for', task.getName())
    param['idx'] = 0
    param['src_data'] = ''
    # res, out = saveArrayToParams(task, param)
    # if res:
        # return out
    return param


