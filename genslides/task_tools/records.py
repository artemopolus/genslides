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
    if 'type' in rparam and rparam['type'] == 'records' and 'data' in rparam:
        out = cparam['header']
        idx = cparam['idx']
        for i, pack in enumerate(rparam['data']):
            chat = pack['chat']
            if idx < len(chat):
                if cparam['enum']:
                    out += cparam['prefix'].replace('[[number]]',str(i))
                else:
                    out += cparam['prefix']
                out += chat[idx]['content']
                out += cparam['suffix']
        out += cparam['footer']
        return out
    return ""

def appendDataForRecord(param : dict, chat):
    if 'type' in param and param['type'] == 'records' and 'data' in param:
        data = param['data']
        if len(data) == 0 or (len(data) and data[-1]['chat'] != chat):
            print('data=',data[-1]['chat'])
            print('chat=',chat)
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

