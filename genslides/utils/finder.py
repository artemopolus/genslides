import re
import genslides.utils.loader as Loader

def convertMdToScript(md_text):
    print('convert md to script')
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
        if len(arr) > 5:
            if 'type' == arr[1]:
                bres, pparam = task.getParamStruct(arr[2])
                if bres and arr[3] in pparam and pparam[arr[3]] == arr[4] and arr[5] in pparam:
                    rep = pparam[arr[5]]
                    rep_text = rep_text.replace(res, str(rep))
        elif arr[1] == getMsgTag():
            param = task.getLastMsgContent()
            if len(arr) > 3 and arr[2] == 'json':
                bres, j = Loader.Loader.loadJsonFromText(param)
                if bres:
                    rep = j[arr[3]]
                    rep_text = rep_text.replace(res, str(rep))
                else:
                    print("No json in", task.getName())
            else:
                print("Replace", res, "from",task.getName())
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
        else:
            p_exist, param = task.getParam(arr[1])
            if p_exist:
                # print("Replace ", res, " with ", param)
                rep_text = rep_text.replace(res, str(param))
            else:
                # print("No param")
                pass
        return rep_text
# TODO: сменить на квадратные скобки
def findByKey(text, manager , base ):
        #  results = re.findall(r'\{.*?\}', text)
         results = re.findall(r"\[\[.*?\]\]", text)
        #  print("Find keys=", text)
        #  print("Results=", results)
         rep_text = text
         for res in results:
             arr = res[2:-2].split(":")
            #  print("Keys:", arr)
             if len(arr) > 1:
                 task = None
                 if arr[0] == 'manager':
                    if arr[1] == 'path':
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
    elif fk_type == 'json':
        value = task_name + ':msg_content:json:'
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
    return ['msg','json','param','tokens','man_path','man_curr','br_code','code']

def getExtTaskSpecialKeys():
    return ['input', 'output', 'stopped', 'check']

