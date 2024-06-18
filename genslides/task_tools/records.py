import genslides.utils.savedata as savedata


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

