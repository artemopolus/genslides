import genslides.utils.savedata as savedata
import genslides.utils.loader as Ld
import genslides.task_tools.text as Txt
import json

def getPackForRecord(role: str, content : str, task_name : str) -> dict:
    return {
        "role": role, 
        "content": content,
        "task": task_name
}

def createRecordParam( chat ):
    data = [{
        'chat': chat,
        'time': savedata.getTimeForSaving()
    }]
    return {'type':'records','data':data}

def getDataFromRecordParam( param : dict ):
    if 'type' in param and param['type'] == 'records' and 'data' in param:
        return param['data']
    return []

def getRecordsRow( rparam : dict, cparam : dict ) -> str:
    # TODO: Сделать аналог для возврата массивом строк
    if 'type' in rparam and rparam['type'] == 'records' and 'data' in rparam:
        idx = cparam['idx']
        trg_chat_msgs = []
        if 'range' in cparam:
            chat_range = cparam['range']
            # print('chat range:',chat_range)
            nums = chat_range.split(',')
            for num in nums:
                if num.isdigit():
                    trg_chat_msgs.append(int(num))
                else:
                    str_end = num.split('-')
                    if len(str_end) == 2 and str_end[0].isdigit() and str_end[1].isdigit():
                        msgrange = list( range(int(str_end[0]), int(str_end[1]) + 1))
                        trg_chat_msgs.extend(msgrange)
        if 'form' in cparam and cparam['form'] == 'alone':
            out = cparam['header']
            for i, pack in enumerate(rparam['data']):
                chat = pack['chat']
                if ((len(trg_chat_msgs) == 0 and idx < len(chat)) or 
                        (idx < len(chat) and i in trg_chat_msgs)):
                    if cparam['enum']:
                        out += cparam['prefix'].replace('[[number]]',str(i))
                    else:
                        out += cparam['prefix']
                    out += chat[idx]['content']
                    out += cparam['suffix']
            cparam['count'] = len(rparam['data'])
            out += cparam['footer']
            return out
    return ""

def getRecordsChat( rparam : dict, cparam : dict ) -> list:
    if 'type' in rparam and rparam['type'] == 'records' and 'data' in rparam:
        out = []
        trg_chat_msgs = []
        cparam['chat_count'] = len(rparam['data'])
        if 'range' in cparam:
            chat_range = cparam['range']
            # print('chat range:',chat_range)
            nums = chat_range.split(',')
            for num in nums:
                num = num.replace(" ","")
                if num.isdigit():
                    trg_chat_msgs.append(int(num))
                else:
                    str_end = num.split('-')
                    if len(str_end) == 2 and str_end[0].isdigit() and str_end[1].isdigit():
                        msgrange = list( range(int(str_end[0]), int(str_end[1]) + 1))
                        trg_chat_msgs.extend(msgrange)
        chat_idx = cparam['idx'] if isinstance(cparam['idx'], int) else (len(rparam['data']) - 1)
        if len(rparam['data']):
            chat = rparam['data'][chat_idx]['chat']
            cparam['curr_chat_len'] = len(chat)
            for i, msg in enumerate(chat):
                content = cparam['prefix'] + msg['content'] + cparam['suffix']
                content = content.replace('[[number]]',str(i))
                if len(trg_chat_msgs) and i in trg_chat_msgs:
                    out.append({'role':msg['role'],'content': content})
                elif len(trg_chat_msgs) == 0:
                    out.append({'role':msg['role'],'content': content})
        if len(out):
            out[-1]['content'] = out[-1]['content'] + cparam['footer']
        return out
    return []


def appendDataForRecord(param : dict, chat):
    if 'type' in param and param['type'] == 'records' and 'data' in param:
        data = param['data']
        # print('src data', data)
        if len(data) == 0 or (len(data) and data[-1]['chat'] != chat):
            # print('data=',data[-1]['chat'])
            # print('chat=',chat)
            pack = {
                'chat': chat,
                'time': savedata.getTimeForSaving()
                }
            data.append(pack)
            return True, param
    return False, param

def clearRecordData(param : dict):
    if 'type' in param and param['type'] == 'records' and 'data' in param:
        param['data'] = []
    return param

def getTrgInfoInRecordsByOptions( param : dict, options : list ):
    out = ""
    if options[2] == 'records':
        if 'type' in param and param['type'] == 'records' and 'data' in param:
            for pack in param['data']:
                for idx, msg in enumerate(pack['chat']):
                    try:
                        if options[3] == 'chat':
                            if options[4] == 'json':
                                trg_jsn = json.loads(msg['content'])
                                if options[5] in trg_jsn:
                                    out += trg_jsn[options[5]]
                            elif options[4] == 'msg':
                                num = int(options[5])
                                if num == idx:
                                    out += msg['content']
                            elif options[4] == 'allmsgs':
                                out += msg['content']
                    except Exception as e:
                        print('Record error:',e)
    return out


def getTrgInfoInRecords(param : dict, info_type = "chat"):
    out = ""
    if 'type' in param and param['type'] == 'records' and 'data' in param:
        if info_type == "chat":
            for pack in param['data']:
                chat = pack['chat']
                for msg in chat:
                    out += msg['content']

    return out

def getMsgsRecordsRow( rparam : dict, cparam : dict, role : str ) -> list[dict]:
    # TODO: Сделать аналог для возврата массивом строк
    if 'type' in rparam and rparam['type'] == 'records' and 'data' in rparam:
        idx = cparam['idx']
        trg_chat_msgs = []
        if 'range' in cparam:
            chat_range = cparam['range']
            # print('chat range:',chat_range)
            nums = chat_range.split(',')
            for num in nums:
                if num.isdigit():
                    trg_chat_msgs.append(int(num))
                else:
                    str_end = num.split('-')
                    if len(str_end) == 2 and str_end[0].isdigit() and str_end[1].isdigit():
                        msgrange = list( range(int(str_end[0]), int(str_end[1]) + 1))
                        trg_chat_msgs.extend(msgrange)
        packs = rparam['data']
        dialogs = []
        msgs = 0
        for i, pack in enumerate(packs):
            chat = pack['chat']
            msgs = max(len(chat), msgs)
            dialogs.append( '\\n'.join([m['content'] for m in chat]) )

        hash = Txt.compute_sha256_hash( '\\n'.join( dialogs ) )
        if 'hash' not in cparam or \
              ('hash' in cparam and hash != cparam['hash']):
                cparam['hash'] = hash
                cparam['count'] = len( packs )
                cparam['msgs_count'] = msgs
                
        if 'form' in cparam:
            if cparam['form'] == 'alone':
                out = cparam['header']
                added_content = False
                for i, pack in enumerate(rparam['data']):
                    chat = pack['chat']
                    if ((len(trg_chat_msgs) == 0 and idx < len(chat)) or 
                            (idx < len(chat) and i in trg_chat_msgs)):
                        if cparam['enum']:
                            out += cparam['prefix'].replace('[[number]]',str(i))
                        else:
                            out += cparam['prefix']
                        out += chat[idx]['content']
                        added_content = True
                        out += cparam['suffix']
                out += cparam['footer']
                if added_content:
                    return[{"content" : out, "role" : role}]
                else:
                    return []
            elif cparam['form'] == 'msgs':
                out = []
                for i, pack in enumerate(rparam['data']):
                    chat = pack['chat']
                    text = ""
                    if ((len(trg_chat_msgs) == 0 and idx < len(chat)) or 
                            (idx < len(chat) and i in trg_chat_msgs)):
                        if cparam['enum']:
                            text += cparam['prefix'].replace('[[number]]',str(i))
                        else:
                            text += cparam['prefix']
                        text += chat[idx]['content']
                        text += cparam['suffix']
                    out.append({"content": text, "role": role})    
                return out
            elif cparam['form'] == 'json_filt_list':
                out = []
                for i, pack in enumerate(rparam['data']):
                    chat = pack['chat']
                    if ((len(trg_chat_msgs) == 0 and idx < len(chat)) or 
                            (idx < len(chat) and i in trg_chat_msgs)):
                        res, recjson = Ld.Loader.loadJsonFromText( chat[idx]['content'] )
                        if res and isinstance(recjson, list):
                            out = list(set(out + recjson))
                return[{"content" : Ld.Loader.convJsonToText(out), "role" : role}]
            elif cparam['form'] == 'json_dictionary':
                out = {}
                for i, pack in enumerate(rparam['data']):
                    chat = pack['chat']
                    if ((len(trg_chat_msgs) == 0 and idx < len(chat)) or 
                            (idx < len(chat) and i in trg_chat_msgs)):
                        res, recjson = Ld.Loader.loadJsonFromText( chat[idx]['content'] )
                        if res:
                            out.update( recjson )
                return[{"content" : Ld.Loader.convJsonToText(out), "role" : role}]
            elif cparam['form'] == 'json_dicts':
                out = []
                for i, pack in enumerate(rparam['data']):
                    chat = pack['chat']
                    if ((len(trg_chat_msgs) == 0 and idx < len(chat)) or 
                            (idx < len(chat) and i in trg_chat_msgs)):
                        res, recjson = Ld.Loader.loadJsonFromText( chat[idx]['content'] )
                        out.append( jsonConvertation(cparam, recjson, res, i) )
                return[{"content" : Ld.Loader.convJsonToText(out), "role" : role}]
            elif cparam['form'] in ['json_dict2text','json_format']:
                out = []
                for i, pack in enumerate(rparam['data']):
                    chat = pack['chat']
                    if ((len(trg_chat_msgs) == 0 and idx < len(chat)) or 
                            (idx < len(chat) and i in trg_chat_msgs)):
                        res, recjson = Ld.Loader.loadJsonFromText( chat[idx]['content'] )
                        if res:
                            out.append( recjson )
                out = fill_missing_indices(out)
                outtext = ""
                if cparam['form'] == 'json_dict2text':
                    if "code" in cparam:
                        args = cparam["code"].split(":")
                        if len(args):
                            for out_pack in out:
                                outtext += Txt.convertJsonDictToText(args, out_pack)
                elif cparam['form'] == 'json_format':
                    res, options = Ld.Loader.loadJsonFromText( ( cparam.get("format","") ) )
                    if res:
                        for out_pack in out:
                            outtext += Txt.convertJsonDictToText2( out_pack, options )

                return[{"content" : outtext, "role" : role}]
            elif cparam['form'] == 'json_dict_list':
                out = []
                i = 0
                for pack in rparam['data']:
                    chat = pack['chat']
                    if ((len(trg_chat_msgs) == 0 and idx < len(chat)) or 
                            (idx < len(chat) and i in trg_chat_msgs)):
                        res, recjson = Ld.Loader.loadJsonFromText( chat[idx]['content'] )
                        if res and isinstance( recjson, list ):
                            for trgjson in recjson:
                                out.append( jsonConvertation(cparam, trgjson, res, i) )
                                i += 1
                return[{"content" : Ld.Loader.convJsonToText(out), "role" : role}]
    return []

def jsonConvertation(cparam, recjson, recres, index):
    icc_keys = []
    if 'icc_keys' in cparam and cparam['icc_keys']:
        icc_keys = [t.replace(' ','') for t in cparam['icc_keys'].split(',')]
    if len(icc_keys) == 3:
        try:
            return                {
                    'idx':recjson[icc_keys[0]],
                    'content': recjson[icc_keys[1]],
                    'chck': recjson[icc_keys[2]]
                }
        except Exception as e:
            print('Error replacing keys idx, content, chck:', e)
    elif 'trgjsonkey' in cparam and isinstance(recjson, dict) and cparam['trgjsonkey'] in recjson:
        return {'idx':index, 'content': recjson[cparam['trgjsonkey']], 'chck':False}
    else:
        if recres:
            recjson['idx'] = index
            return recjson

def fill_missing_indices(data, default=None):
    """
    Given a list of dictionaries with an "idx" key, this function returns a new list
    that covers the range from 0 to the max "idx". Missing ranges are filled with a single
    default dictionary.
    
    Args:
        data (list): List of dictionaries, each with an "idx" key.
        default (dict, optional): Default dictionary to insert in gaps.
                                  If None, uses {"default": True}.
    
    Returns:
        list: Sorted list with missing index ranges filled.
    """
    if default is None:
        default = {"default": True}
    
    # Sort the list by the "idx" key.
    sorted_data = sorted(data, key=lambda x: x["idx"])
    result = []
    
    # Start at expected index 0.
    expected = 0
    
    for item in sorted_data:
        # If the current item's idx is greater than expected,
        # there is a gap. Insert a single default dict for that gap.
        if item["idx"] > expected:
            result.append(default)
        
        # Append the current item.
        result.append(item)
        # Update expected to one more than the current idx.
        expected = item["idx"] + 1
    
    return result

def updateProposals(param : dict, proposal : str):
    prop_hash = Txt.compute_sha256_hash(proposal)
    lastprophash = param.get("last_proposal_hash","")
    props : list = param.get("proposals",[])
    if lastprophash != prop_hash:
        max_props = param.get("max_proposals", 10)
        if len(props) < max_props:
            props.append(proposal)
        else:
            props.pop(0)
            props.append(proposal)
        param["proposals"] = props
        param["last_proposal_hash"] = prop_hash
        param["trg_prop_idx"] = 0

def getNextProposal(param : dict ):
    props : list = param.get("proposals",[])
    idx = param.get("trg_prop_idx", 0)
    if len(props):
        idx += 1
        if idx >= len(props):
            idx = 0
        param["trg_prop_idx"] = idx
        return props[idx]
    return ""

def clearProposals( param : dict ):
    param["proposals"] = []
    param["last_proposal_hash"] = ""
    param["trg_prop_idx"] = -1

def getProposals( param : dict) -> list :
    return param.get("proposals",[])

