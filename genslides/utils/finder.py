import re
import genslides.utils.loader as Loader
import json

def convertMdToScript(md_text):
    # print('convert md to script')
    code_pattern = r'```python\n(.*?)\n```'
    
    parts = re.split(code_pattern, md_text, flags=re.DOTALL)
    text = ""
    for i, part in enumerate(parts):
        if i % 2 == 0:  # Non-code parts treated as comments
            pass
            # lines = part.strip().split('\n')
            # comment_lines = ['# ' + line for line in lines]
            # text += '\n'.join(comment_lines) + '\n'
        else:  # Code parts
            text += part.strip() + "\n"
    return text


def getMsgTag()-> str:
    return "msg_content"

def getTknTag()-> str:
    return 'tokens_cnt'

def getMngTag()-> str:
    return 'manager'

def getBranchCodeTag(name: str) -> str:
    return '[[' + name + ':' + 'branch_code' + ']]'

def getFromTask(arr : list, res : str, rep_text, task, manager):
        # print('Get from task', task.getName())
        if len(arr) > 5 and 'type' == arr[1]:
                bres, pparam = task.getParamStruct(arr[2])
                if bres and arr[3] in pparam and pparam[arr[3]] == arr[4] and arr[5] in pparam:
                    jtrg_val = pparam[arr[5]]
                    rep_text = rep_text.replace(res, str(jtrg_val))
        elif arr[1] == getMsgTag():
            param = task.getLastMsgContent()
            if len(arr) == 3 and arr[2] == 'json':
                bres, jjson = Loader.Loader.loadJsonFromText(param)
                if bres:
                    rep_text = rep_text.replace(res, json.dumps(jjson, indent=1))
            elif len(arr) > 3 and arr[2] == 'json':
                bres, jjson = Loader.Loader.loadJsonFromText(param)
                try:
                    # print('try find json', j)
                    jtrg_val = jjson[arr[3]]
                    if len(arr) > 4 and isinstance(jtrg_val, list) and arr[4].isdigit() and int(arr[4]) < len(jtrg_val):
                        trg_idx = int(arr[4])
                        if len(arr) > 5 and arr[5] in jtrg_val[trg_idx]:
                            rep_text = rep_text.replace(res, str(jtrg_val[trg_idx][arr[5]]))
                        else:
                            rep_text = rep_text.replace(res, str(jtrg_val[trg_idx]))
                    else:
                        rep_text = rep_text.replace(res, json.dumps(jtrg_val))

                except Exception as e:
                    print("Error:", e,"\nFind json in", task.getName(),':\nTrg json:',param, '\nRes json:',jjson)
            elif len(arr) > 3 and arr[2] == 'json_list':
                bres, jjson = Loader.Loader.loadJsonFromText(param)
                try:
                    jtrg_val = jjson[arr[3]]
                    if isinstance(jtrg_val, list):
                        text  = ''
                        for p in range(len(jtrg_val)):
                            if isinstance(jtrg_val[p], dict):
                                if len(arr) > 4 and arr[4] in jtrg_val[p]:
                                    text_p = jtrg_val[p][arr[4]]
                                else:
                                    text_p = json.dumps(jtrg_val[p])
                            else:
                                text_p = jtrg_val[p]
                            text += str(p+1) + '. ' + str(text_p) + '\n'
                        rep_text = rep_text.replace(res, text)
                    else:
                        rep_text = rep_text.replace(res, str(jtrg_val))
                except Exception as e:
                    print("Erorr find json list in", task.getName(),':',e)
            else:
                # print("Replace", res, "from",task.getName())
                rep_text = rep_text.replace(res, str(param))
        elif arr[1] == getTknTag():
            tkns, price = task.getCountPrice()
            rep_text = rep_text.replace(res, str(tkns))
        elif arr[1] == 'branch_code':
            p_tasks = task.getAllParents()
            # print('Get branch code',[t.getName() for t in p_tasks])
            code_s = ""
            if len(p_tasks) > 0:
                trg = p_tasks[0]
                code_s = manager.getShortName(trg.getType(), trg.getName())
                for i in range(len(p_tasks)-1):
                    code_s += p_tasks[i].getBranchCode( p_tasks[i+1])
            rep_text = rep_text.replace(res, code_s)
        elif arr[1] == 'code':
            rep_text = convertMdToScript(md_text=task.getLastMsgContent())
        elif arr[1] == 'param' and len(arr) > 3:
            pres, pparam = task.getParamStruct(arr[2])
            if pres and arr[3] in pparam:
                value = pparam[arr[3]]
                if isinstance(value, str):
                    rep_text = rep_text.replace(res, pparam[arr[3]])
                else:
                    rep_text = rep_text.replace(res, str(pparam[arr[3]]))
            else:
                # print("No param")
                pass
        return rep_text
# TODO: сменить на квадратные скобки
def findByKey(text, manager , base ):
        #  results = re.findall(r'\{.*?\}', text)
         results = re.findall(r"\[\[.*?\]\]", text)
         n_res = []
         for res in results:
             arr = res[2:-2].split(":")
             tmp_ress = []
             try:
                for res1 in arr:
                    if res1.startswith('parent') and len(res1) > 6:
                        vals = res1.split('_')
                        if len(vals) == 2 and vals[1].isdigit():
                            for idx in range(int(vals[1])):
                                tmp_ress.append('parent')
                        else:
                            tmp_ress.append(res1)
                    else:
                        tmp_ress.append(res1)
             except Exception as e:
                print('error check array:', e)
             n_arr = '[[' + ':'.join(tmp_ress) + ']]' 
             text = text.replace(res, n_arr)
             if res != n_arr:
                n_res.append(n_arr)
             else:
                n_res.append(res)

         results = n_res




        #  print("Find keys=", text)
        #  print("Results=", results)
         rep_text = text
         for res in results:
             arr = res[2:-2].split(":")

                         #  print("Keys:", arr)
             if len(arr) > 1:
                 task = None
                 if arr[0] == 'manager':
                    if len(arr) > 2 and arr[1] == 'path' and arr[2] == 'fld':
                        trg_text = Loader.Loader.getFolderPath(path=manager.getPath())
                        rep_text = rep_text.replace(res, trg_text)
                    elif arr[1] == 'path':
                        trg_text = manager.getPath()
                        rep_text = rep_text.replace(res, trg_text)
                    elif arr[1] == 'current':
                        task = manager.getCurrentTask()
                        arr.pop(0)
                 elif arr[0] == 'parent':
                    task = base.getParent()
                 else:
                    task = base.getAncestorByName(arr[0])
                 if task:
                     while( arr[1] == 'parent'):
                         task = task.getParent()
                         if task is None:
                             return text
                         arr.pop(0)
                     rep_text = getFromTask(arr, res, rep_text, task, manager)
                 else:
                    #  print("No task", arr[0])
                     pass
             else:
                # print("Incorrect len")
                pass
         return rep_text

def getKey(task_name, fk_type, param_name, key_name, manager) -> str:
    if fk_type == 'msg':
        value = task_name + ':msg_content'
    elif fk_type.startswith('json'):
        value = task_name + ':msg_content:'+ fk_type + ':'
    elif fk_type == 'tokens':
        value = task_name + ':' + getTknTag()
    elif fk_type == 'br_code':
        value = task_name + ':' + getBranchCodeTag()
    elif fk_type == 'param':
        value = task_name + ':' + param_name + ':' + key_name 
    elif fk_type == 'code':
        value = task_name + ':code'
    elif fk_type == 'man_path':
        value = "manager:path"
    elif fk_type == 'man_curr':
        value = "manager:current"
    value = '[[' + value + ']]'
    return value

def getKayArray():
    return ['msg','json','json_list','param','tokens','man_path','man_curr','br_code','code']

def getExtTaskSpecialKeys():
    return ['input', 'output', 'stopped', 'check']

