import genslides.utils.savedata as savedata
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
        out = cparam['header']
        idx = cparam['idx']
        trg_chat_msgs = []
        if 'range' in cparam:
            chat_range = cparam['range']
            nums = chat_range.split(',')
            for num in nums:
                if num.isdigit():
                    trg_chat_msgs.append(int(num))
                else:
                    str_end = num.split('-')
                    if len(str_end) == 2 and str_end[0].isdigit() and str_end[1].isdigit():
                        msgrange = list( range(int(str_end[0]), int(str_end[1]) + 1))
                        trg_chat_msgs.extend(msgrange)
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

