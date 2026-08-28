import genslides.task_tools.text as TextTool
import genslides.utils.loader as Ld
# import genslides.task.text as Txt
import logging

logger = logging.getLogger(__name__)


def checkContextWindow( text: str, size : int):
    if len(text) > size:
        return False
    return True

def divideArray(task  , param : dict):
    logger.debug('Divide array')
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
    elif parse_type == 'manual':
        return True, []
    elif parse_type == 'json':
        if 'manual_target' in param and param['manual_target'] != "":
            msg_content = task.findKeyParam( param['manual_target'] )
        else:
            msg_content = task.getLastMsgContent2()
        res, targets = Ld.Loader.loadJsonFromText(msg_content)
        if res and isinstance(targets, list):
            arr = []
            check_context_window_on = param.get("context_window_check_on",False)
            if check_context_window_on:
                context_win_size = param.get("context_window_size", 100)
                use_marker = param.get("context_window_addmarker","none")
                starting_text = ""
                starting_names = []
                for msg in targets:
                    if "content" in msg and "priority" in msg and "name" in msg:
                        if msg["priority"] == "high":
                            message_name = msg["name"]
                            if use_marker == "taskname":
                                starting_text += f"[{message_name}] " + msg["content"]
                            else:
                                starting_text += msg["content"]
                            starting_names.append(message_name)
                msg_content = [starting_text]
                msg_names = []
                for idx, msg in enumerate(targets):
                    if "content" in msg and "name" in msg:
                        message_name = msg["name"]
                        logger.debug("Current %s", message_name)
                        if message_name not in starting_names:
                            if use_marker == "taskname":
                                msg_content.append( f"[{message_name}] " + msg["content"] )
                            else:
                                msg_content.append( msg["content"] )
                            msg_names.append(message_name)
                            if len("".join(msg_content)) < context_win_size:
                                logger.debug("Append small text %s", message_name)
                            else:
                                logger.debug("Append BIG %s", message_name)
                                
                                arr_value = {
                                    "content" : "".join( msg_content),
                                    "name" : ",".join(msg_names)
                                }
                                arr_idx = len(arr)
                                arr.append(
                                    {
                                        'idx' : arr_idx,
                                        "size":len("".join( msg_content)),
                                        'chck':False,
                                        'content': Ld.Loader.convJsonToText(arr_value)
                                    }
                                )
                                msg_content = [starting_text]
                                msg_names = []
                #
                if len(msg_names):
                    arr_value = {
                        "content" : "".join( msg_content),
                        "name" : ",".join(msg_names)
                    }
                    arr_idx = len(arr)
                    arr.append(
                        {
                            'idx' : arr_idx,
                            "size":len("".join( msg_content)),
                            'chck':False,
                            'content': Ld.Loader.convJsonToText(arr_value)
                        }
                    )
                else:
                    logger.debug("All  msgs are added")
                   
            else:
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
            logger.debug('No list in target json key')
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
    elif parse_type.startswith("task_names"):
        excl = param.get("exclude_tasktypes","")
        prefix = param.get("part_prefix","")
        suffix = param.get("part_suffix","")
        arr = []
        if parse_type == "task_names_inv":
            names : list[str] = task.getAllParentNames(exclude = excl, revert_dir = True)
        else:
            names : list[str] = task.getAllParentNames(exclude = excl)
        for idx, name in enumerate(names):
            arr.append({"content": prefix + name + suffix, "idx": idx, "chck": False})
        return True, arr
    return False, []

def getArrayByIndexPlusPlus( param, task  ):
    logger.debug('Get array index ++')
    index = param['idx']
    array = param['array']
    if param['parse'] == 'manual':
        logger.debug('manual')
        idx_excld = param.get('idx_excl', [])
        while( index < param['len']):
            if 'step' in param and param['step']:
                index += int(param['step'])
            else:
                index +=1
            if index not in idx_excld:
                break
        param['idx'] = index
        out =  getPartByParam(task,param)
        return out
        

    if index < len(array) - 1:
        if not array[index]['chck']:
            param['idx'] = index
            return getPartByParam(task,param)
        index += 1
        logger.debug('Index: %s', index)
        while index < len(array):
            if not array[index]['chck']:
                param['idx'] = index
                return getPartByParam(task,param)
            index += 1
    else:
        return getPartByParam(task,param)
    return param

ArrayStdTypesList = ['std','json','msgs','task_names','task_names_inv']

def getPartByParam(task, param):
    logger.debug('getPartByParam')
    parse_type = param['parse']
    index = param['idx']
    if parse_type == 'manual' and 'manual_format' in param:
        param['curr'] = task.findKeyParam( param['manual_format'] )
        return param
    array = param['array']
    array[index]['chck'] = True
    if parse_type in ArrayStdTypesList:
        param['curr'] = array[index]["content"]
    elif parse_type == 'text_split':
        src_data = task.getLastMsgContent2()
        start = array[index]['start']
        end = array[index]['end']
        param['curr'] = src_data[start:end]
    return param



def getArrayByIndex(array, index, param, task  ):
    parse_type = param['parse']
    if parse_type in ArrayStdTypesList:
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
    if parse_type in ArrayStdTypesList:
        return current != array[index]["content"]
    elif parse_type == 'text_split':
        src_data = task.getLastMsgContent2()
        start = array[index]['start']
        end = array[index]['end']
        return current != src_data[start:end]
    return True

def getSHAfromTask(task, param):
    data = ''
    if param['parse'] in ['std','text_split','json']:
        if 'manual_target' in param and param['manual_target'] != "":
            data = task.findKeyParam( param['manual_target'] )
        else:
            data = task.getLastMsgContent2()
    elif param['parse'] == 'manual':
        if 'manual_target' in param:
            data = task.findKeyParam( param['manual_target'] )
    elif param['parse'] == 'msgs' or param['parse'].startswith("task_names"):
        messages = task.getMsgs()
        for msg in messages:
            data += msg['content'] 
    return TextTool.compute_sha256_hash(data)
 

def saveArrayToParams(task  , param : dict):
    logger.debug('Save array for %s', task.getName())
   
    # print('param',param)
    idx = param ['idx']
    if 'parse' in param:
        res, arr = divideArray(task, param)
        if isinstance(arr, list) and len(arr) > 0 and res:
            curr = getArrayByIndex(arr, 0, param, task)
            if param['parse'] == 'manual' and 'start' in param:
                exclude = param.get("manual_excl","")
                try:
                    if isinstance(exclude, int):
                        param['idx_excl'] = [exclude]
                    else:
                        param['idx_excl'] = [int(num) for num in exclude.split(",")]
                except Exception as e:
                    logger.debug("Error for idx excl: %s", e)
                    param['idx_excl'] = []
                idx = param['start']
                array_len = 0
                try:
                    if isinstance(param['manual_len'], int):
                        array_len = idx + param['manual_len']
                    else:
                        array_len = idx + int(task.findKeyParam(param['manual_len']))
                except Exception as e:
                    logger.debug("Error for len: %s", e)
                param['len'] = array_len
            else:
                idx = 0
        else:
            logger.debug('Cant divide into array')
            return False, param
    else:
        logger.debug('No parse parameter')
        return False, param
    # out = {}
    setArrayParamValues(param, arr, curr, idx)
    param ['src_data' ]= getSHAfromTask(task, param)
    param = getPartByParam( task, param )
    # param.update(out)
    return True, param

def getArrayIdx( param, idx):
    if 'idx_excl' in param:
        while(idx in param['idx_excl']):
            idx += 1
    return idx

def setArrayParamValues(param, array, current, idx):
    param['array'] = array
    param['curr'] = current 
    param['idx'] = getArrayIdx( param, idx)

    if param['parse'] != 'manual':
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
        logger.debug('Update array param error: %s', e)
    return param

def iterateOverArrayFromParam(task  , param: dict):
    logger.debug('iterateOverArrayFromParam')
    # print('Iterate over array from param', param)
    if 'type' in param and param['type'] == 'array':
        if 'array' in param and 'curr' in param and 'idx' in param:
            # idx = param["idx"]
            # if idx == 0 and checkCurrentArrayElem( param, task):
            #     pass
            # else:
            param = getArrayByIndexPlusPlus(param, task)
    return param

def needToUpdate( task ,param):
    if 'parse' in param and param['parse'] == 'manual' \
        and param['src_data'] == getSHAfromTask(task, param):
        return True
    elif 'src_data' in param and param['src_data'] == getSHAfromTask(task, param) :
        return True
    return False



def checkArrayIteration(task  , param : dict):
    report = []
    report.append('checkArrayIteration')
    if 'type' in param and param['type'] == 'array':
        if needToUpdate( task, param):
            report.append('Update array')
            if task.manager.allowUpdateInternalArrayParam(task):
                return iterateOverArrayFromParam(task, param)
            else:
                report.append('Manager deny update')
        else:
            report.append('Src data is changed')
            res, out = saveArrayToParams(task, param)
            if res:
                report.append('Success save array')
                return out
            else:
                report.append('Error on save array')
    param["report"] = "\n".join(report)
    return param

def resetArrayParam( task, param : dict):
    logger.debug('Reset array params for %s', task.getName())
    if param['parse'] == 'manual' and 'start' in param:
        idx = param['start']
        idx = getArrayIdx( param, idx)
    else:
        idx = 0
    param['idx'] = idx
    param['src_data'] = ''
    # res, out = saveArrayToParams(task, param)
    # if res:
        # return out
    return param


def createArrayParam(manual_target = ""):
    param = {
      "type":"array",
      "parse":"None",
      "idx":0,
      "curr":"",
      "parts":1,
      "part_smbl_cnt":5000,
      "smbl_before":0,
      "smbl_after":0,
      "src_data":"",
      "manual_len" : "0",
      "manual_format":"",
      "manual_target": manual_target,
      "manual_excl":"",
      "len": 0,
      "step": 1,
      "start": 0
    }
    return param