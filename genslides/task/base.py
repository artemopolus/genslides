import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester
import genslides.utils.loader as Loader

# import genslides.commands.create as create
from genslides.helpers.singleton import Singleton

import os
from os import listdir
from os.path import isfile, join

import json



class TaskManager(metaclass=Singleton):
    def __init__(self) -> None:
        self.task_id = 0
        self.task_list = []
        self.model_list = []
        self.setDefaultProj()

    def getListBasedOptionsDict(self, param):
        with open(os.path.join('config','options.json')) as f:
            opt_params = json.load(f)
        if 'type' in param:
            for p in opt_params:
                if p['type'] == param['type']:
                    return [k for k,v in p.items() if k != 'type']
        return []

    def getParamOptBasedOptionsDict(self):
        with open(os.path.join('config','options.json')) as f:
            opt_params = json.load(f)
        return [p['type'] for p in opt_params]
 

    def getParamBasedOptionsDict(self, param_name):
        with open(os.path.join('config','options.json')) as f:
            opt_params = json.load(f)
        for p in opt_params:
            if p['type'] == param_name:
                for k, v in p.items():
                    if k == 'path_to_trgs' and param_name == 'script':
                        p[k] = v
                    elif isinstance(v,list):
                        if len(v) > 0:
                            p[k] = v[0]
                        else:
                            p[k] = v
                return p
        return None
     
    def getOptionsBasedOptionsDict(self, param_name, param_key):
        with open('config\\options.json') as f:
            opt_params = json.load(f)
        for p in opt_params:
            if p['type'] == param_name and param_key in p:
                if isinstance(p[param_key], list):
                    return p[param_key]
                else:
                    return [p[param_key]]
        return []

        

    def getId(self, task, manager = None) -> int:
        id = self.task_id
        name = task.getType() + str(id)
        # Учитывать информацию от менеджера, управляющего задачей: использовать его конкретный путь, а не стандартный
        if manager is not None:
            mypath = manager.getPath()
        else:
            mypath = 'saved'
        onlyfiles = [f.split('.')[0] for f in listdir(mypath) if isfile(join(mypath, f))]
        while name in onlyfiles:
            id += 1
            name = task.getType() + str(id)
        self.task_id = id + 1
        if task not in self.task_list:
            self.task_list.append(task)
        return id
    
    def setDefaultProj(self):
        self.cur_task_path = 'saved/'
        self.cur_proj_name = ''
        self.proj_pref = ''
    
    def setPath(self, path: str):
        self.cur_task_path = path

    def setProjPrefix(self, proj_name):
        self.cur_proj_name = proj_name
        self.proj_pref = proj_name + '_'

    def getProjPrefix(self) -> str:
        return self.proj_pref
    

    def getTaskExtention(self) -> str:
        return '.json'
    
    def getPath(self) -> str:
        if not os.path.exists(self.cur_task_path):
            os.makedirs(self.cur_task_path)
        return self.cur_task_path
    
    def getLinks(self,mypath):
        # mypath = self.getPath()
        # print('Get links by path', mypath)
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        out = []
        for filename in onlyfiles:
            path = join(mypath,filename)
            try:
                with open(path, 'r') as f:
                    rq = json.load(f)
                if 'linked' in rq:

                    pair = {}
                    pair['name'] = filename.split('.')[0]
                    pair['linked'] = rq['linked']
                    out.append(pair)
            except Exception as e:
                pass
        return out

    def getTaskPrompts(self,mypath, trg_path = "", ignore_safe = False):
        mypath = Loader.Loader.getUniPath(mypath)
        # print('Get task prompts in folder', mypath, 'with path', trg_path, 'ignore_safe=', ignore_safe)
        pr_ch = []
        if trg_path != "":
            trg_path = Loader.Loader.getUniPath(trg_path)
            with open(trg_path, 'r') as f:
                pr_fl = json.load(f)
                if 'params' in pr_fl:
                    for param in pr_fl['params']:
                        if 'type' in param and param['type'] == 'child' and 'name' in param:
                            pr_ch.append(param['name'] + self.getTaskExtention())
            # print('Childs:', pr_ch)
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        for child in pr_ch:
            if child in onlyfiles:
                onlyfiles.insert(0, onlyfiles.pop(onlyfiles.index(child)))
        out = []
        idx = 0
        # print('Get available tasks from',len(onlyfiles),'files')
        for filename in onlyfiles:
            idx += 1
            path = join(mypath,filename)
            # print('Check path=',path)
            try:
                with open(path, 'r') as f:
                    rq = json.load(f)
                if 'parent' in rq:
                    # print(path)
                    path_from_file = rq['parent']
                    parent_path = ""
                    # print(path_from_file.split('/'))
                    if len(path_from_file.split('/')) > 1:
                        print('Load from old style')
                        parent_path = path_from_file
                    else:
                        # path_from_file = path_from_file.split('/')[-1]
                        if path_from_file != "":
                            parent_path = os.path.join(mypath , path_from_file + self.getTaskExtention())
                    # print('Check path:',parent_path,'=',trg_path)
                    if parent_path == trg_path and 'chat' in rq and 'type' in rq:
                        # print("Get propmt from=",path)
                        # if rq['type'].endswith("RichText") or rq['type'].endswith("Response"):
                        if len(rq['chat']) == 0:
                            elem = {'role': 'user','content': ''}
                        else:
                            if rq['type'] == "RichText":
                                elem = rq['chat'].pop()
                            elem = rq['chat'].pop()
                        pair = {}
                        # pair['type'] = rq['type']
                        pair['type'] =filename.split('.')[0] 
                        pair['content'] = elem['content']
                        pair['role'] = elem['role']

                        out.append(pair)
                        
                        # for elem in rq['chat']:
                        #     if elem['role'] == 'user':
                        #         pair = {}
                        #         pair['type'] = rq['type']
                        #         pair['content'] = elem['content']
                        #         out.append(pair)
            except json.decoder.JSONDecodeError as e:
                print("Get json error on task prompts=", e,"using", path)
            except Exception as e:
                print("Task prompts error=", type(e),"using", path)
            if  ignore_safe and trg_path != "" and len(out) == len(pr_ch):
                break
        print('Target files count:',len(pr_ch),'from',len(onlyfiles),'for', trg_path,'in', idx, 'iter')
        return out




class TaskDescription():
    def __init__(self, prompt = "", method = None, parent=None, helper=None, 
                 requester=None, target=None, manager=None, id = 0, type = "", 
                 prompt_tag = "user", filename = "", enabled = False, 
                 params = [], manual = False, stepped = False) -> None:
        self.manager = manager
        self.prompt = prompt
        self.prompt_tag = prompt_tag
        self.method = method
        self.parent = parent
        self.helper = helper
        self.requester = requester
        self.target = target
        self.id = id
        self.type = type
        self.filename = filename
        self.enabled = enabled
        self.params = params
        self.manual = manual
        self.stepped = stepped

class BaseTask():
    def __init__(self, task_info : TaskDescription, type = 'None') -> None:
        self.manager = task_info.manager
        self.childs = []
        self.is_solved = False
        self.reqhelper = task_info.helper
        self.requester = task_info.requester
        self.crtasklist = []

        type = task_info.type
        self.type = type
        self.init = self.reqhelper.getInit(type)
        self.endi = self.reqhelper.getEndi(type)

        self.prompt = task_info.prompt
        self.prompt_tag = task_info.prompt_tag
        
        self.method = task_info.method
        task_manager = TaskManager()
        self.id = task_manager.getId(self, self.manager)
        self.name =  ""
        self.pref = self.manager.getProjPrefix()
        self.parent = None
        self.affect_to_ext_list = []
        self.by_ext_affected_list = []
        self.queue = []
        self.is_freeze = False
        self.setName( self.type + str(self.id))
        request = self.init + self.prompt + self.endi
        self.task_description = "Task type = " + self.type + "\nRequest:\n" + request
        self.task_creation_result = "Results of task creation:\n"

        self.setParent(task_info.parent)
            # if self.parent.is_freeze:
                # self.is_freeze = True
        
        self.target = task_info.target
        self.filename = task_info.filename


    def getBranchCodeTag(self) -> str:
        p_tasks = self.getAllParents()
        # print('Get branch code',[t.getName() for t in p_tasks])
        code_s = ""
        if len(p_tasks) > 0:
            trg = p_tasks[0]
            code_s = self.manager.getShortName(trg.getType(), trg.getName())
            for i in range(len(p_tasks)-1):
                code_s += p_tasks[i].getBranchCode( p_tasks[i+1])
        return code_s


    def getManager(self):
        return self.manager
    
    def setManager(self, manager):
        self.manager = manager

    def getParent(self):
        return self.parent
    
    def freezeTask(self):
        self.is_freeze = True
        # self.update()

    def unfreezeTask(self):
        self.is_freeze = False
        # self.update()

    def getRichPrompt(self) -> str:
        out = self.prompt
        if not out.startswith(self.init):
            out = self.init + out
        if not out.endswith(self.endi):
            out += self.endi
        for task in self.by_ext_affected_list:
            out += " " + task.prompt
        return out
    
    def getJson(self):
        return None
    

    def getIdStr(self) -> str:
        return str(self.id)
    
    
    def setName(self, name : str):
        name = self.pref + name
        if name == self.name:
            return
        old_name = self.name
        self.name = name
        # print("My new name is", self.name,", was", old_name)

        if self.parent:
            self.parent.updateNameQueue(old_name, name)

        for info in self.by_ext_affected_list:
            info.parent.updateNameQueue(old_name, name)

    def getClearName(self) -> str:
        return self.name.replace(self.pref, "")

    
    def getName(self) -> str:
        return self.name
    
    def getType(self) -> str:
        return self.type

    def checkType(self, trg: str) -> bool:
        return self.type.endswith(trg)

    def isInputTask(self):
        return True
    
    def isRootParent(self):
        return self.parent is None
    
    def getRootParent(self):
        par = self
        index = 0
        while(index < 1000):
            if par.parent:
                par = par.parent
            else:
                break
            index += 1
        return par

    def getTree(self, max_childs = -1):
        par = self.getRootParent()
        out = par.getAllChildChains(max_childs=max_childs)
        return out

    def getAllParents(self, max_index = -1):
        par = self
        index = 0
        out = [self]
        while(index < 1000):
            if par.parent:
                if par not in par.parent.getChilds(): #ExtProject issue
                    found = False
                    for child in par.parent.getChilds():
                        if child.checkType( 'ExtProject') and child.isTaskInternal(par):
                            p = [par.parent, child]
                            out.pop(0)
                            p.extend(out)
                            out = p
                            found = True
                            break
                    # TODO: Ошибка возникает при удалении набора задач, связанных друг с другом. Для исправлении ошибки надо создать отдельную функцию удаления пакетов задач
                    # if not found:
                    #     raise Exception('Parent',par.parent.getName(),'task not connected with target', par.getName())
                else:
                    p = [par.parent]
                    p.extend(out)
                    out = p
                par = par.parent
            else:
                if par.caretaker is not None:
                    out.pop(0)
                    p = [par.caretaker]
                    p.extend(out)
                    out = p
                break
            index += 1
            if max_index != -1 and index > max_index:
                break
        # print('Parent list:', [t.getName() for t in out])
        return out

    def getChildChainList(self):
        index = 0
        branch_list = [{'branch':[self],'done':False,'parent':None,'i_par':None,'idx':[]}]
        while(index < 1000):
            childs_to_add = []
            for branch in branch_list:
                trg = branch['branch'][-1]
                j = 0
                while (j < 1000 and not branch['done']):
                    childs = trg.getChilds()
                    if len(childs) == 1:
                        branch['branch'].append(childs[0])
                        trg = childs[0]
                    elif len(childs) > 1:
                        childs_to_add.extend(childs)
                        branch['done'] = True
                        break
                    else:
                        branch['done'] = True
                        break
                    j += 1
            if len(childs_to_add) == 0:
                break
            for child in childs_to_add:
                branch_list.append({'branch':[child],'done':False,'parent':None,'i_par':None,'idx':[]})

            index += 1
        
        for j in range(len(branch_list)):
            trg = branch_list[j]['branch'][-1]
            childs = trg.getChilds()
            i_out = []
            for i in range(len(branch_list)):
                if branch_list[i]['branch'][0] in childs:
                    i_out.append(i)
                    branch_list[i]['parent'] = trg
                    branch_list[i]['i_par'] = j
            print(i_out)
            branch_list[j]['idx'] = i_out
        return branch_list
    
    def getLinkedTaskFromBranches(self, branches):
        linked_task = []
        for branch in branches:
            for link in branch['links']:
                if link['dir'] == 'in':
                    linked_task.extend([link['in']])
        return linked_task

    def getTasksFullLinks(self, pparam):
        branches = self.getChildAndLinks(self, pparam)
        if not pparam['link']:
            return branches
        idx = 0
        linked_task = self.getLinkedTaskFromBranches(branches)
        while(idx < 1000):
            tmp = []
            start_idx = len(branches)
            for task in linked_task:
                new_b = self.getChildAndLinks(task, pparam, start_j=start_idx)
                branches.extend(new_b)
                tmp.extend(new_b)
            linked_task = self.getLinkedTaskFromBranches(tmp)
            idx += 1
        return branches
    
    # Возвращает можно ли вообще копировать наследников ветки 
    def isLinkForCopy(self):
        return True
    
    def getTrgLinkInfo(self, trg):
        return False, {'out': trg, 'in': self, 'dir': 'in'}

    # Копирует информацию о связях между задачами в переменную trg_links, 
    # переменная copy_in запрашивает информацию о входящих
    # переменная copy_out запрашивае информацию о исходящих 
    def getLinkCopyInfo(self, trg_links:list, copy_in = True, copy_out = True):
    # TODO: разделить между обычными задачами и задачами типа Прием обработку исходящих и входящих
        # print('Get link copy info from',self.getName())
        if len(self.getHoldGarlands()) and copy_out:
            for ll in self.getHoldGarlands():
                res, val = ll.getTrgLinkInfo(self)
                if res:
                    print('Append:',val['out'].getName(),'->', val['in'].getName())
                    trg_links.append(val)
        if len(self.getGarlandPart()) and copy_in:
            for ll in self.getGarlandPart():
                trg_links.append( {'out': ll, 'in': self, 'dir':'out'})

    def getChildAndLinks(self, task, pparam, start_j = 0):
        print('Get child and links for', task.getName())
        index = 0
        branch_list = [{'branch':[task],'done':False,'parent':task.parent,'i_par':None,'idx':[],'links':[]}]
        while(index < 1000):
            childs_to_add = []
            for branch in branch_list:
                trg = branch['branch'][-1]
                j = 0
                while (j < 1000 and not branch['done']):
                    # print('Task', trg.getName())
                    childs = trg.getChilds()
                    trg.getLinkCopyInfo(branch['links'], pparam['in'], pparam['out'])
                    # if len(trg.getHoldGarlands()) and pparam['out']:
                    #     for ll in trg.getHoldGarlands():
                    #         branch['links'].append( {'out': trg, 'in': ll, 'dir': 'in'})
                    # if len(trg.getGarlandPart()) and pparam['in']:
                    #     for ll in trg.getGarlandPart():
                    #         branch['links'].append( {'out': ll, 'in': trg, 'dir':'out'})
                    # print('Links:')
                    # for ll in branch['links']:
                    #     print(ll['out'].getName(),'->', ll['in'].getName())
                    if len(childs) == 1:
                        branch['branch'].append(childs[0])
                        trg = childs[0]
                    elif len(childs) > 1:
                        childs_to_add.extend(childs)
                        branch['done'] = True
                        break
                    else:
                        branch['done'] = True
                        break
                    j += 1
            if len(childs_to_add) == 0:
                break
            for child in childs_to_add:
                print('Add child', child.getName())
                branch_list.append({'branch':[child],'done':False,'parent':None,'i_par':None,'idx':[],'links':[]})

            index += 1
        
        for j in range(len(branch_list)):
            trg = branch_list[j]['branch'][-1]
            print('Apply branch:',[t.getName() for t in branch_list[j]['branch']])
            childs = trg.getChilds()
            i_out = []
            for i in range(len(branch_list)):
                if branch_list[i]['branch'][0] in childs:
                    i_out.append(i)
                    branch_list[i]['parent'] = trg
                    branch_list[i]['i_par'] = start_j + j
            branch_list[j]['idx'] = i_out
        return branch_list


    def getAllChildChains(self, max_index = -1, max_childs = -1):
        index = 0
        out = [self]
        trgs = [self]
        while(index < 1000):
            n_trgs = []
            found = False
            for trg in trgs:
                if max_childs > 0:
                    childs_cnt = 0
                    for ch in trg.childs:
                        found = True
                        n_trgs.append(ch)
                        out.append(ch)
                        childs_cnt += 1
                        if childs_cnt >= max_childs:
                            break
                else:
                    for ch in trg.childs:
                        found = True
                        n_trgs.append(ch)
                        out.append(ch)
            if not found:
                break
            trgs = n_trgs
            index += 1
            if max_index != -1 and index > max_index:
                break
        return out
    
    def getAllBuds(self):
        childs = self.getAllChildChains()
        out = []
        for task in childs:
            if len(task.getChilds()) == 0:
                out.append(task)
        return out
    
    def getChainBeforeBranching(self):
        out = self.getAllChildChains()
        par = self
        index = 0
        while(index < 1000):
            if par.parent and len(par.parent.childs) == 1:
                par = par.parent
                out.append(par)
            else:
                break
            index += 1
        return out

    def getAncestorByName(self, trg_name):
        if self.getName() == trg_name:
            return self
        index = 0
        task = self
        while(index < 1000):
            if  task.parent != None:
                if task.parent.getName() != trg_name:
                    task = task.parent
                else:
                    return task.parent
            else:
                break
            index += 1
        return None

    def getNewID(self) -> int:
        task_manager = TaskManager()
        self.id = task_manager.getId(self)
        return self.id


    def addChildToCrList(self, task : TaskDescription):
        self.crtasklist.append(task)

    def isSolved(self):
        return self.is_solved
    
    def checkChilds(self):
        for child in self.childs:
            if not child.isSolved():
                return False
        return True

    def getDefCond(self) -> dict:
        return {"cond" : "None", "cur": "None", "trg": "used", "str": "None","idx":0}

    def getChildQueuePack(self, child) ->dict:
        val = {  "type":"child", "used":False ,"name": child.getName()}
        val.update(self.getDefCond())
        return val

    def getLinkQueuePack(self, info: TaskDescription) -> dict:
        val = { "name": info.target.getName(), "id":info.id,"method":info.method, "type":"link","used":False}
        val.update(self.getDefCond())
        # print(val)
        return val
    
    def getJsonQueue(self, pack : dict) -> dict:
        if not pack:
            return {}
        if pack["type"] == "child" or pack["type"] == "link":
            # print("val:",pack)
            # if "name" not in pack:
            #     pack["name"] = val.getName()
            if 'method' in pack:
                del pack['method']
            return pack
        return {}
    
    def setParent(self, parent):
        if parent is None:
            # print('Remove parent')
            self.parent = None
            return
        else:
            pass
            # print('Set',self.getName(),'parent', parent.getName())
        if self.parent:
            self.parent.removeChild(self)

        parent.addChild(self)
        self.freezeTask()
        # self.parent = parent

    def addChild(self, child) -> bool:
        # print('Add child',child.getName())
        if child not in self.childs:
            # child.setParent(self)
            child.parent = self
            self.childs.append(child)
            info = self.getChildQueuePack(child)
            self.onQueueReset(info)
            self.queue.append(info)
            return True
        return False
    
    def getPrio(self):
        return 0
    
    def setPrio(self, idx : int):
        pass
    
    def getChildByName(self, child_name):
        for ch in self.getChilds():
            if ch.getName() == child_name:
                return ch
            
    def getLinkedByName(self, linked_name):
        for info in self.affect_to_ext_list:
            if info.target.getName() == linked_name:
                return info.target
    
    
    def fixQueueByChildList(self):
        print('Fix queue of', self.getName(),'by childs and links list')
        to_del = []
        for child in self.childs:
            found = False
            for q in self.queue:
                if q['name'] == child.getName() and q['type'] == 'child':
                    if found:
                        to_del.append(q)
                    else:
                        found = True
            if not found:
                info = self.getChildQueuePack(child)
                self.onQueueReset(info)
                self.queue.append(info)
        for q in self.queue:
            found = False
            for child in self.childs:
                if q['name'] == child.getName() and q['type'] == 'child':
                    found = True
            for link in self.affect_to_ext_list:
                if q['name'] == link.target.getName() and q['type'] == 'link':
                    found = True
            if not found and q not in to_del:
                to_del.append(q)
        
        for q in to_del:
            self.queue.remove(q)

        for trg in self.queue:
            if 'idx' not in trg:
                trg['idx'] = 0



    def getHoldGarlands(self):
        return [t.target for t in self.affect_to_ext_list]
    
    def getGarlandPart(self):
        return [t.parent for t in self.by_ext_affected_list]


    def setLinkToTask(self, info : TaskDescription) -> bool:
        # print('Set link to', info.target.getName())
        self.affect_to_ext_list.append(info)
        info1 = self.getLinkQueuePack(info)
        self.onQueueReset(info1)
        found = False
        for pack in self.queue:
            if pack['type'] == 'link' and pack['name'] == info1['name']:
                found = True
        if not found:
            self.queue.append(info1)
        return True

    def resetLinkToTask(self, info : TaskDescription) -> None:
        print('Reset link to task by', self.getName())
        # print(self.queue)
        self.affect_to_ext_list.remove(info)

    def getChilds(self):
        return self.childs.copy()

    # Возвращает пару символов для точек ветвления
    def getBranchCode(self, second) -> str:
        code_s = ""
        if len(self.getChilds()) > 1:
            # Если ветвится в точке с потомком записи в файл, то это ветвление игнорируется
            if second.checkType( 'WriteToFileParam'):
                return code_s
            # else:
            trg1 = self
            code_s += self.manager.getShortName(trg1.getType(), trg1.getName())
            trg1 = second
            code_s += self.manager.getShortName(trg1.getType(), trg1.getName())
        return code_s

    # TODO: возвращать список задач для создания, а не просто копирования. Например,
    # если задача содержит список, то создать дочерние задачи по списку
    # Это может быть востребовано для перебора файлов в папке
    # Перебор результатов поиска в Гугл или Яндексе
    # Список действий, перечисленных ГПТ

    # def getCmd(self):
    #     if len(self.crtasklist) > 0:
    #         task = self.crtasklist.pop()
    #         print('Register command:' + str(task.method))
    #         return create.CreateCommand( task)
    #     return None
    
    def stdProcessUnFreeze(self, input=None):
            if self.parent:
                self.is_freeze = self.parent.is_freeze
            else:
                pass

    def updateIternal(self, input : TaskDescription = None):
        pass
   
    def update(self, input : TaskDescription = None):
        self.stdProcessUnFreeze(input)

       
        # print("Update=",self.getName(), "|frozen=", self.is_freeze)
        self.updateIternal(input)

        if input is None:
            # print('No input')
            self.useLinksToTask()
            for child in self.childs:
                child.update()
        elif input and input.stepped:
            # print('Input stepped')
            self.useLinksToTask(stepped=True)
        else:
            print('Input no stepped')
            self.is_freeze = True
            self.useLinksToTask()
            for child in self.childs:
                child.update()

        return "","",""
    
    def setupQueue(self):
        if self.queue and not self.isQueueComplete():
            pass
        else:
            # print("Setup queue:",self.queue)
            pass


    def resetTreeQueue(self):
        trgs = [self]
        index = 0
        while(index < 1000):
            n_trgs = []
            for trg in trgs:
                trg.resetQueue()
                for ch in trg.childs:
                    n_trgs.append(ch)
            trgs = n_trgs
            index += 1

    def setTreeQueue(self):
        trgs = [self]
        index = 0
        while(index < 1000):
            n_trgs = []
            for trg in trgs:
                trg.setQueue()
                for ch in trg.childs:
                    n_trgs.append(ch)
            trgs = n_trgs
            index += 1

    def updateNameQueue(self, old_name : str, new_name : str):
        pass

    def resetQueue(self):
        if self.queue:
            for info in self.queue:
                self.onQueueReset(info)
    
    def onQueueReset(self, info):
        # print('Reset queue from', self.getName(),'=',info)
        # print('Reset queue from', self.getName())
        info["used"] = False
        info["cur"] = info["str"]

    def setQueue(self):
        if self.queue:
            for info in self.queue:
                self.onQueueSet(info)


    def onQueueSet(self, info):
        info["used"] = True

    def printQueueInit(self):
        pass

    def onQueueCheck(self, param) -> bool:
        # print("React on condition:",param)
        # self.printQueueInit()

        if param['cond'] in ['>','<','=','!=']:
            res = True
            if isinstance(param['trg'], str):
                cur = self.findKeyParam(param['cur'])
                if param['cond'] == '=' and cur != param['trg']:
                    res = False
                elif param['cond'] == '!=' and cur == param['trg']:
                    res = False
                elif param['cur'] == 'None':
                    res = False
            elif isinstance(param['trg'], int):
                try:
                    cur = param['cur']
                    if isinstance(cur, str):
                        cur = int(self.findKeyParam(cur))
                    else:
                        cur = int(cur)   
                except:
                    print('Can\'t get value from',param['cur'],'and', self.findKeyParam(param['cur']))   
                    return False
                trg = param['trg']
                if param['cond'] == '>' and cur < trg:
                    res = False
                elif param['cond'] == '<' and cur > trg:
                    res = False
                elif param['cond'] == '=' and cur != trg:
                    res = False
                elif param['cond'] == '!=' and cur == trg:
                    res = False
                print('Check',cur,param['cond'],trg)

            if not res:
                return False
            else:
                if 'endless' in param and param['endless']:
                    print('Infinity loop!')
                    param['cur'] = param['str'] # Или возврат к исходному?

  


        # if param['cond'] == '=' or param['cond'] == '!=':
        #     if isinstance(param['cur'], str):
        #         cur = self.findKeyParam(param['cur'])
        #         print('Cond', self.getName(),':',cur,param['cond'],param['trg'])
        #         if param['cond'] == '=':
        #             if cur != param['trg'] or param['cur'] == 'None':
        #                 return False
        #             else:
        #                 if 'endless' not in param or not param['endless']:
        #                     param['cur'] = 'None'
        #         elif param['cond'] == '!=':
        #             if cur == param['trg'] or param['cur'] == 'None':
        #                 return False
        #             else:
        #                 if 'endless' not in param or not param['endless']:
        #                     param['cur'] = 'None'
        # elif isinstance(param['trg'], int) and isinstance(param['cur'], int):
        #     cur = int(param['cur'])
        #     trg = int(param['trg'])
        #     if param['cond'] == '>' and cur < trg:
        #         return False
        #     elif param['cond'] == '<' and cur > trg:
        #         return False
        #     elif param['cond'] == '=' and cur != trg:
        #         return False
        elif param['cond'] == 'None':
            if param['cur'] == param['trg']:
                return False
            else:
                param['cur'] = "used"
        if param['cond'] == 'for':
            print('Cond for:', param['cur'])
            try:
                if self.getName() == param['target']:
                    jp = json.loads(self.getLastMsgContent())
                else:
                    jp = json.loads(self.getAncestorByName(param['target']).getLastMsgContent())
                if not "data" in param:
                    param['data'] = jp['data']
                    param['value'] = param['data'][0]
                    param['trg'] = len(param['data'])
                    param['cur'] = 0
                    param['str'] = 0
                else:
                    if jp['data'] != param['data']:
                        param['data'] = jp['data']
                        param['value'] = param['data'][0]
                        param['trg'] = len(param['data'])
                        param['cur'] = 0
                        param['str'] = 0
                    else:
                    # print(param)
                        index = param['cur'] + 1
                        param['value'] = param['data'][index]
                        param['cur'] = index
                    # print(param)
                # else:
                    # return False
            except Exception as e:
                print("Some go wrong:", e)
                return False
        # print("React on condition:",param)
        param["used"] = True
        return True
    

    def syncQueueToParam(self):
        pass

    def sortKey(self, trg):
        return trg['idx']

    def sortQueue(self):
        self.queue.sort(key=self.sortKey)
        # print([[q['name'], q['idx']] for q in self.queue])

    def findNextFromQueue(self, only_check = False):
        # print("Search for next from queue", self.getName(),':',[q['name'] for q in self.queue if 'name' in q ])
        self.sortQueue()
        if self.queue:
            for info1 in self.queue:
                if only_check:
                    info = info1.copy()
                else:
                    info = info1
                if info["type"] == "child":
                    # print("info:", info)
                    if self.onQueueCheck(info):
                        return self.getChildByName(info['name'])
                # if info["type"] == "link":
                #     if self.onQueueCheck(info):
                #         input = TaskDescription(
                #             prompt=self.findKeyParam(self.getLastMsgContent()), 
                #             id=info["id"], stepped=True, 
                #             parent=self, enabled= not self.is_freeze)
                #         # info["method"](input)
                #         # print('Use link to', info['name'])
                #         for affected in self.affect_to_ext_list:
                #             if affected.target.getName() == info['name']:
                #                 input.id = affected.id
                #                 affected.method(input)
                #         return self.getLinkedByName(info['name'])
        return None
    
    def useLinksToTask(self, stepped = False):
        print('Use links',[t.getName() for t in self.getHoldGarlands()])
        input = TaskDescription(prompt=self.prompt, parent=self)
        for task in self.affect_to_ext_list:
            input.id = task.id
            task.method(input)


    def isQueueComplete(self):
        if len(self.queue) > 0:
            return False
        return True

    def getNextFromQueue(self):
        res = self.findNextFromQueue()
        # print("Get next from",self.getName(),"queue:", res)
        if res:
            return res
        return self.getNextFromQueueRe()
        # if self.isQueueComplete():
        #     return self.getNextFromQueueRe()
        # return None
        
    def getNextFromQueueRe(self):
        # print("Get recursevly")
        trg = self
        index = 0
        while(index < 1000):
            if trg.isRootParent() or trg.caretaker is not None:
                return trg
            else:
                trg = trg.parent
                res = trg.findNextFromQueue()
                if res:
                    # print('Reset from task=', res.getName())
                    res.resetTreeQueue()
                    return res
            index +=1
        return None   
    
    def getMsgInfo(self):
        return "","",""
    
    def replaceImMsgs(self, trg_old, trg_new):
        pass
    
    def getInfo(self, short = True) -> str:
        return "Some description"


    def beforeRemove(self):
        print('Before remove')
        self.removeLinkToTask()
        if self.isRootParent():
            print('Task',self.getName(),'is Root')
            # Последняя задача для дерева
            pass #Только проектер решает об удалении менеджера
        else:
            self.parent.removeChild(self)
        print('Task',self.getName(),'have',len(self.childs),'childs')
        for child in self.childs:
            child.whenParentRemoved()

    def whenParentRemoved(self):
        # self.setParent(None)
        self.removeParent()

    def removeParent(self):
         if self.parent:
            self.parent.removeChild(self)
            self.setParent(None)

    def removeAllChilds(self):
        childs_list = self.getChilds()
        for child in childs_list:
            self.removeChild(child)
       
    def removeChild(self,child) -> bool:
        if child in self.childs:
            print("Remove child", child.getName(),"from", self.getName())
            self.childs.remove(child)
            trg = None
            for q in self.queue:
                if q['name'] == child.getName() and q['type'] == 'child':
                    trg = q
                    break
            if trg is not None:
                self.queue.remove(trg)
            # self.queue.remove(self.getChildQueuePack(child))
            return True
        return False

    def getCountPrice(self):
        return 0,0
    
    def affectedTaskCallback(self, input : TaskDescription):
        pass

    def createLinkToTask(self, task) -> TaskDescription:
        pass
        # id = len(self.by_ext_affected_list)
        # out = TaskDescription(method=self.affectedTaskCallback, id=id, parent=task )
        # self.by_ext_affected_list.append(out)
        # task.setLinkToTask(out)
        # return out
    
    def removeLinkToTask(self):
        while len(self.by_ext_affected_list) > 0:
            input = self.by_ext_affected_list.pop()
            input.parent.resetLinkToTask(input)
        for task in self.getHoldGarlands():
            task.removeLinkToTask()
    

    def completeTask(self) -> bool:
        # print(self.getName(),"=Complete Task")
        return False 
    
    def setParam(self, param):
        pass
    
    def getParam(self, param_name):
        return None
    
    def setParamStruct(self, param):
        pass
    
    def getParamList(self):
        return None
    
    def updateParamStruct(self, param_name, key,val):
        pass
    
    def updateParam2(self, param_vals : dict):
        pass

    def getParamStruct(self, param_name):
        return False, None
    
    def copyAllParams(self, copy_info = False):
        return {}
    
    def getAllParams(self):
        return ""
    
    def saveAllParams(self):
        pass
    
    def getRawMsgs(self):
        return None
    
    def getMsgs(self, except_task = []):
        return None
    
    def findKeyParam(self, text: str):
        return text
    
    def getAffectingOnTask(self) -> list:
        out = []
        for pack in self.by_ext_affected_list:
            out.append(pack.parent)
        return out
    
    def getAffectedTasks(self) -> list:
        out = []
        for pack in self.affect_to_ext_list:
            out.append(pack.target)
        return out

    def checkTask(self):
        return True
    
    def getTextInfo(self, param):
        return [],'Not Response Task'
    
    def resaveWithID(self, id : int):
        pass
    
    def getLastMsgContentRaw(self):
        return "No any content"
    
    def getLastMsgContent(self):
        return ""
    
    def setBranchSummary(self, summary : str):
        pass

    def getBranchSummary(self) -> str:
        return ''
    
    def getExeCommands(self):
        return False, {}
    
    def setManagerParamToTask(self, param):
        pass

    def extractTask(self):
        task1 = self.parent
        task2 = self
        task3_list = task2.getChilds()
        for task in task3_list:
            task.removeParent()
            if task1 is not None:
                task1.removeChild(self)
                task1.addChild(task)

    def extractTaskList(self, del_tasks):
        buds = []
        for task in del_tasks:
            childs = task.getChilds()
            count = 0
            for c in childs:
                if c in del_tasks:
                    count +=1
            if count == 0:
                buds.append(task)
        for bud in buds:
            b_idx = 0
            trg = bud
            while (b_idx < 1000):
                if trg not in del_tasks:
                    break
                elif trg.getParent() == None:
                    break
                else:
                    trg.extractTask()
                    trg = trg.getParent()
                b_idx +=1


    def readyToGenerate(self) -> bool:
        return False

