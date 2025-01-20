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
        chat_idx = cparam['idx']
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
        if len(rparam['data']):
            chat = rparam['data'][chat_idx]['chat']
            cparam['curr_chat_len'] = len(chat)
            for i, msg in enumerate(chat):
                if len(trg_chat_msgs) and i in trg_chat_msgs:
                    out.append({'role':msg['role'],'content': cparam['prefix'] + msg['content'] + cparam['suffix']})
                elif len(trg_chat_msgs) == 0:
                    out.append({'role':msg['role'],'content': cparam['prefix'] + msg['content'] + cparam['suffix']})
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
                cparam['count'] = len(rparam['data'])
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
                cparam['count'] = len(rparam['data'])
                return out
            elif cparam['form'] == 'json_dicts':
                out = []
                for i, pack in enumerate(rparam['data']):
                    chat = pack['chat']
                    if ((len(trg_chat_msgs) == 0 and idx < len(chat)) or 
                            (idx < len(chat) and i in trg_chat_msgs)):
                        res, jobj = Ld.Loader.loadJsonFromText( chat[idx]['content'] )
                        if res:
                            out.append( jobj)
                return[{"content" : Ld.Loader.convJsonToText(out), "role" : role}]
    return []
