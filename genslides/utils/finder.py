import re
import genslides.utils.loader as Loader
import genslides.utils.reqhelper as Helper
import genslides.utils.filemanager as FileMan
import genslides.utils.parser as Parser
import json
import genslides.task_tools.records as rd
import genslides.task_tools.array as toolarr

def convertTextPartToMsg(md_text):
    code_pattern = r'```\n(.*?)\n```'
    parts = re.split(code_pattern, md_text, flags=re.DOTALL)
    text = ""
    for i, part in enumerate(parts):
        if i % 2 == 0:  # Non-code parts treated as comments
            pass
        else:  # Code parts
            text += part.strip()
    return text

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

def getFromTask(arr : list, res : str, rep_text, task, manager, index = 0):
        # print('Get from task', task.getName())
        if len(arr) > 5 and 'type' == arr[1]:
                bres, pparam = task.getParamStruct(arr[2])
                if bres and arr[3] in pparam and pparam[arr[3]] == arr[4] and arr[5] in pparam:
                    jtrg_val = pparam[arr[5]]
                    rep_text = rep_text.replace(res, str(jtrg_val))
        elif arr[1] == 'allmsgs':
            msgs = task.getMsgs()
            out_text = ""
            for msg in msgs:
                out_text += msg['content'] + '\n\n'
            rep_text = rep_text.replace(res, out_text)
        elif arr[1] == 'name':
            rep_text = rep_text.replace(res, task.getName())
        elif arr[1] == getMsgTag():
            param = task.getLastMsgContent()
            if len(arr) == 3 and arr[2] == 'json_dump':
                jdump = json.dumps(param)
                rep_text = rep_text.replace(res, jdump)

            elif len(arr) == 3 and arr[2] == 'json':
                bres, jjson = Loader.Loader.loadJsonFromText(param)
                if bres:
                    rep_text = rep_text.replace(res, json.dumps(jjson, indent=1))
            elif len(arr) > 3 and arr[2] == '---':
                text = str(param)
                if arr[3].isdigit():
                    i_vert = int(arr[3])
                    verticaldiv = text.split('[[---]]')
                    if i_vert < len(verticaldiv):
                        text =  verticaldiv[i_vert]
                rep_text = rep_text.replace(res, text)

            elif len(arr) > 3 and arr[2] == 'json2':
                text = res
                bres, jjson = Loader.Loader.loadJsonFromText(param, report=True)
                if bres:
                    # print('arr',arr)
                    tmparg = arr.copy()
                    tmparg.pop(0) # - link
                    tmparg.pop(0) # - msg
                    tmparg.pop(0) # - json2
                    conv = tmparg.pop(0)
                    for i, arg in enumerate(tmparg):
                        if arg == 'index':
                            tmparg[i] = str(index)
                    # print('tmp arg',tmparg)
                    trgjson = Parser.parseJsonKeys(tmparg, jjson)

                    if conv == 'dict_v' and isinstance(trgjson, dict):
                        text = '[[,]]'.join([Loader.Loader.convJsonToText(v) for k,v in trgjson.items()])
                    elif conv == 'list' and isinstance(trgjson, list):
                        text = '[[,]]'.join([Loader.Loader.convJsonToText(v) for v in trgjson])
                    else:
                        text = Loader.Loader.convJsonToText(trgjson)
                rep_text = rep_text.replace(res, text)
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
                        if isinstance(jtrg_val, str):
                            rep_text = rep_text.replace(res, jtrg_val)
                        else:
                            rep_text = rep_text.replace(res, json.dumps(jtrg_val))

                except Exception as e:
                    # print("Error:", e,"\nFind json in", task.getName(),':\nTrg json:',param, '\nRes json:',jjson)
                    pass
            elif len(arr) > 3 and arr[2] == 'json_list':
                bres, jjson = Loader.Loader.loadJsonFromText(param, report = True)
                try:
                    if arr[3] == "_":
                        jtrg_val = jjson
                    else:
                        jtrg_val = jjson[arr[3]]
                    # print("json:", jtrg_val)
                    # print("arg:", len(arr))
                    # print("arg:", arr)
                    # print("Index", index)

                    if isinstance(jtrg_val, list):
                        text  = ''
                        index_max = len(jtrg_val)
                        if len(arr) > 4 and arr[4] == "index" and index < index_max:
                            val_index = jtrg_val[index - 1]
                            if len(arr) > 5 and arr[5] == "str" and isinstance(val_index, list):
                                text = '[[,]]'.join([Loader.Loader.convJsonToText(v) for v in val_index])
                            elif len(arr) > 5 and arr[5] == "str" and isinstance(val_index, dict):
                                text = '[[,]]'.join([Loader.Loader.convJsonToText(v) for k,v in val_index.items()])

                            else:
                                text = Loader.Loader.convJsonToText(val_index)
                        else:
                            for p in range(len(jtrg_val)):
                                if isinstance(jtrg_val[p], dict):
                                    if len(arr) > 4 and arr[4] in jtrg_val[p]:
                                        text_p = jtrg_val[p][arr[4]]
                                    else:
                                        text_p = Loader.Loader.convJsonToText(jtrg_val[p])
                                else:
                                    text_p = jtrg_val[p]
                                text += str(p+1) + '. ' + str(text_p) + '\n'
                        rep_text = rep_text.replace(res, text)
                    else:
                        rep_text = rep_text.replace(res, Loader.Loader.convJsonToText(jtrg_val))
                except Exception as e:
                    print("Erorr find json list in", task.getName(),':',e)
            elif len(arr) > 3 and arr[2] == 'filenamesbypath':
                names = FileMan.getFilesInFolder(param)
                rep_text = rep_text.replace(res, ';'.join(names))
            elif len(arr) > 3 and arr[2] == 'filepathsbypath':
                names = FileMan.getFilenamesFromFilepaths(param)
                rep_text = rep_text.replace(res, ';'.join(names))
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
            script_text = convertMdToScript(md_text=task.getLastMsgContent())
            rep_text = rep_text.replace(res, script_text)
        elif arr[1] == 'text_ins':
            script_text = convertTextPartToMsg(md_text=task.getLastMsgContent())
            rep_text = rep_text.replace(res, script_text)
        elif arr[1] == 'param' and len(arr) > 3:
            pres, pparam = task.getParamStruct(arr[2])
            if pres:
                if arr[2] == 'records':
                    records = rd.getTrgInfoInRecordsByOptions(pparam, arr)
                    if records != "":
                        rep_text = rep_text.replace(res, records)
                elif arr[2] == 'array' and len(arr) > 4 and arr[3] == "array":
                    try:
                        value = int(arr[4])
                        text = toolarr.getArrayByIndex(pparam["array"], value, pparam, task)
                        rep_text = rep_text.replace(res, text)
                    except:
                        pass
                elif arr[3] in pparam:
                    value = pparam[arr[3]]
                    if isinstance(value, str):
                        rep_text = rep_text.replace(res, pparam[arr[3]])
                    else:
                        rep_text = rep_text.replace(res, str(pparam[arr[3]]))
            else:
                # print("No param")
                pass
        return rep_text

def shiftParentTags( text : str, shift : int ):
    results = re.findall(r"\[\[.*?\]\]", text)
    for res in results:
        tags_arr = res[2:-2].split(":")
        for tag in tags_arr:
            index = 0
            found = False
            if tag.startswith('parent') and len(tag) > 6:
                parent_tag = tag.split('_')
                if len(parent_tag) == 2 and parent_tag[1].isdigit():
                    index = int(parent_tag[1])
                    index += shift
                    found = True
            elif tag == 'parent':
                index = 1 + shift
                found = True
            if found:
                if index > 1:
                    change_parent = '_'.join([ parent_tag[0], str(index)])
                elif index == 1:
                    change_parent = parent_tag[0]
                if index > 0:
                    target_parent = tag
                    text = text.replace(target_parent, change_parent)
    return text



def findByKey(text, manager , base, reqhelper : Helper.RequestHelper):
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




         rep_text = text
         for res in results:
             arr = res[2:-2].split(":")

                         #  print("Keys:", arr)
             if len(arr) > 1:
                 task = None
                 if arr[0] == 'manager':
                    if len(arr) > 2 and arr[1] == 'path':
                        if arr[2] == 'fld':
                            trg_text = Loader.Loader.getFolderPath(path=manager.getPath())
                        elif arr[2] == 'spc':
                            trg_text = Loader.Loader.getFolderPath(path=manager.getPath(), to_par_fld = False)
                        else:
                            trg_text = res
                        if len(arr) > 3 and arr[3] == 'name':
                            trg_text = FileMan.getFileName(trg_text)
                        rep_text = rep_text.replace(res, trg_text)
                    elif arr[1] == 'path':
                        trg_text = manager.getPath()
                        trg_text = Loader.Loader.getUniPath(trg_text)
                        rep_text = rep_text.replace(res, str(trg_text))
                    elif arr[1] == 'current':
                        task = manager.getCurrentTask()
                        arr.pop(0)
                 elif arr[0] == 'parent':
                    task = base.getParent()
                 elif arr[0] == 'project':
                    if len(arr) > 2:
                        rres, rvalue = reqhelper.getValue(arr[1], arr[2])
                        if rres:
                            rep_text = rep_text.replace(res, str(rvalue))
                 elif arr[0] == 'global':
                    if len(arr) > 1:
                        if arr[1] == 'path':
                            rep_text = rep_text.replace(res, Loader.Loader.getProgramFolder())
                 else:
                    task = base.getAncestorByName(arr[0])
                 if task:
                     while( arr[1] == 'parent'):
                         task = task.getParentForFinder()
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

def findByKey2(text, manager , base):
        reqhelper = manager.helper
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
        rep_text = text
        out_results_cnt = len(results)
        out_target_task = base
        for res in results:
            arr = res[2:-2].split(":")
            if len(arr) > 1:
                task = None
                if arr[0] == 'manager':
                    if len(arr) > 2 and arr[1] == 'path':
                        if arr[2] == 'fld':
                            trg_text = Loader.Loader.getFolderPath(path=manager.getPath())
                        elif arr[2] == 'spc':
                            trg_text = Loader.Loader.getFolderPath(path=manager.getPath(), to_par_fld = False)
                        else:
                            trg_text = Loader.Loader.restorePathUsingManPath(arr[2],manager.getPath())
                        if len(arr) > 3 and arr[3] == 'name':
                            trg_text = FileMan.getFileName(trg_text)
                        rep_text = rep_text.replace(res, trg_text)
                    elif arr[1] == 'path':
                        trg_text = manager.getPath()
                        trg_text = Loader.Loader.getUniPath(trg_text)
                        rep_text = rep_text.replace(res, str(trg_text))
                    elif arr[1] == 'current':
                        task = manager.getCurrentTask()
                        arr.pop(0)
                elif arr[0] == 'parent':
                    task = base.getParent()
                elif arr[0] == 'project':
                    if len(arr) > 2:
                        rres, rvalue = reqhelper.getValue(arr[1], arr[2])
                        if rres:
                            rep_text = rep_text.replace(res, str(rvalue))
                elif arr[0] == 'global':
                    if len(arr) > 1:
                        if arr[1] == 'path':
                            rep_text = rep_text.replace(res, Loader.Loader.getProgramFolder())
                elif arr[0] == 'current':
                    rep_text = getFromTask(arr, res, rep_text, base, manager)
                    base.freeTaskByParentCode()
                else:
                    pass
                if task:
                    index = 0
                    while( arr[1] == 'parent'):
                        task = task.getParentForFinder()
                        if task is None:
                             return text, out_target_task, out_results_cnt
                        arr.pop(0)
                        index +=1
                    out_target_task = task
                    rep_text = getFromTask(arr, res, rep_text, task, manager, index)
                    task.freeTaskByParentCode()
                else:
                    #  print("No task", arr[0])
                    index, task = base.getIdxAncestorTaskByName(arr[0])
                    if task:
                        rep_text = getFromTask(arr, res, rep_text, task, manager, index)
                        task.freeTaskByParentCode()

            elif len(arr) == 1:
                if arr[0] == 'name':
                    rep_text = rep_text.replace(res, base.getName())
            else:
                # print("Incorrect len")
                pass
        return rep_text, out_target_task, out_results_cnt

