from genslides.utils.reqhelper import RequestHelper
from genslides.utils.request import Requester
from genslides.utils.searcher import WebSearcher
from genslides.utils.browser import WebBrowser
import genslides.task.base as Task
import re
import pathlib


import genslides.utils.loader as Loader
import genslides.utils.readfileman as Reader

class Jun():
    def __init__(self, helper: RequestHelper, requester: Requester, searcher: WebSearcher):
        pass

    def onStart(self, path = 'saved'):
        self.task_list = []
        self.task_index = 0
        self.curr_task = None
        self.slct_task = None
        self.cmd_list = []
        self.cmd_index = 0
        self.index = 0
        self.branch_idx = 0
        self.branch_lastpar = None
        self.branch_code = ''
        self.tree_arr = []
        self.tree_idx = 0

        self.endes = []
        self.endes_idx = 0

        self.browser = WebBrowser()

        self.need_human_response = False
        self.path = path
        self.proj_pref = ''
        self.return_points = []
        self.selected_tasks = []
        self.info = None
        self.tc_start = False
        self.tc_stop = False
        self.multiselect_tasks = []
        self.is_loaded = False
        self.renamed_parent = []
        self.is_executing = False

    def setName(self, name : str):
        self.name = name
        if self.info != None:
            self.info['name'] = name

    def getName(self) -> str:
        if self.info and 'name' in self.info:
            return self.info['name']
        return self.name
    
    def updateTreeArr(self, check_list = False):
        self.tree_arr = []
        for task in self.task_list:
            if check_list:
                par = task.parent
                if task.isRootParent() or par not in self.task_list:
                    self.tree_arr.append(task)
            else:
                if task.isRootParent():
                    self.tree_arr.append(task)
        # print('Update tree array with check state:', check_list, [t.getName() for t in self.tree_arr])
        

    def goToNextTreeFirstTime(self):
        self.updateTreeArr()
        if len(self.tree_arr) > 0:
            self.curr_task = self.tree_arr[0]
            self.tree_idx = 1

    def getTreeName(self, task:Task.BaseTask):
        return task.getBranchSummary() + '[' + task.getName() + ']'

    def getTreeNamesForRadio(self):
        names = []
        if len(self.tree_arr) == 0:
            self.sortTreeOrder()
        for task in self.tree_arr:
            names.append(self.getTreeName(task))
        trg = self.getTreeName(self.curr_task)
        return names, trg
        # print('Trg tree:', trg,'out of', names)
        # return gr.Radio(choices=names, value=trg, interactive=True)
    
    def setInitTreeTask(self, tree_task : Task.BaseTask) -> Task.BaseTask:
        target = tree_task
        res, pparam = tree_task.getParamStruct('tree_step')
        if res and 'target' in pparam:
            task = self.getTaskByName(pparam['target'])
            if task != None:
                target = task
        return target

    def goToTreeByName(self, name):
        print('Go to tree by name', name)
        for i in range(len(self.tree_arr)):
            trg = self.getTreeName(self.tree_arr[i])
            if trg == name:
                self.curr_task = self.setInitTreeTask(self.tree_arr[i])
                self.tree_idx = i
                break
        # return self.getCurrTaskPrompts()
        # return self.goToNextBranchEnd()


    def goToNextTree(self):
        print('Current tree was',self.tree_idx,'out of',len(self.tree_arr))
        if len(self.tree_arr) > 0:
            if self.tree_idx + 1 < len(self.tree_arr):
                self.tree_idx += 1
            else:
                self.tree_idx = 0
            self.curr_task = self.tree_arr[self.tree_idx]
        # return self.getCurrTaskPrompts()

    def takeFewSteps(self, dir:str, times : int):
        for idx in range(times):
            if dir == 'child':
                self.goToNextChild()
            elif dir == 'parent':
                self.goToParent()

    # Переключаться между наследованием со спуском вниз: от родителя к потомку. Потомков может быть несколько, поэтому существует неопределенность со следующим наследником.
    # Текущий вариант не отслеживает начальную ветку
    def goToNextChild(self):
        # Список направлений
        prev = self.curr_task
        chs = self.curr_task.getChilds()
        self.curr_task = None

        # Если есть потомки
        if len(chs) > 0:
            # Если потомков нескольно
            if len(chs) > 1:
                self.branch_lastpar = prev
                self.branch_idx = 0
                # С использованием кода
                # Запоминаем место ветвления
                if prev in self.multiselect_tasks:
                    found_childs = []
                    found_task = None
                    for ch in chs:
                        if ch in self.multiselect_tasks:
                            found_task = ch
                            found_childs.append(ch)
                    if len(found_childs) == 1:
                        self.curr_task = found_task
                    elif len(found_childs) == 0:
                        pass
                    else:
                        chs = found_childs

                if self.curr_task == None:
                    for ch in chs:
                        # Перебираем коды потомков
                        ch_tag = ch.getBranchCodeTag()
                        # Если код совпал с кодом в памяти
                        # print('Check', ch_tag,'with',self.branch_code)
                        if ch_tag.startswith(self.branch_code) and ch in self.task_list:
                            # Установить новую текущую
                            self.curr_task = ch
                            break
        else:
            self.curr_task = prev

        # Обычный вариант
        if self.curr_task is None:
            # Выбираем просто нулевую ветку
            self.curr_task = chs[0]
        return 
    
    def goToParent(self):
        if self.curr_task.parent is not None and self.curr_task.getParent() in self.task_list:
            self.curr_task = self.curr_task.parent

    def sortBuds(self, trg : Task.BaseTask):
        tasks = trg.getAllParents()
        prio = 0
        for task in tasks:
            prio += task.getPrio()
        return prio
    
    def iterateNextBranch(self, task :Task.BaseTask, revert = False):
        childs = task.getChilds()
        iter = len(childs)
        if self.branch_idx >= iter:
            self.branch_idx = 0
        if revert:
            for idx in range(iter):
                if self.branch_idx > 0:
                    self.branch_idx -= 1
                else:
                    self.branch_idx = iter - 1
                if childs[self.branch_idx] in self.task_list:
                    return childs[self.branch_idx]
        else:
            for idx in range(iter):
                if self.branch_idx < iter - 1:
                    self.branch_idx += 1
                else:
                    self.branch_idx = 0
                if childs[self.branch_idx] in self.task_list:
                    return childs[self.branch_idx]
        return task


    def goToNextBranch(self, revert = False):
        trg = self.curr_task
        idx = 0
        while(idx < 1000):
            if trg.isRootParent():
                return
                # return self.getCurrTaskPrompts()
            children = [t for t in trg.parent.getChilds() if t in self.task_list]
            if len(children) > 1:
                if self.branch_lastpar is not None and trg.parent == self.branch_lastpar:
                    next_task = self.iterateNextBranch(trg.getParent(), revert)
                    if next_task == trg:
                        next_task = self.iterateNextBranch(trg.getParent(), revert)
                    self.curr_task = next_task
                else:
                    self.branch_lastpar = trg.parent
                    if trg != trg.parent.childs[0]:
                        self.curr_task = trg.parent.childs[0]
                        self.branch_idx = 0
                    else:
                        self.curr_task = trg.parent.childs[1]
                        self.branch_idx = 1
                break
            else:
                trg = trg.parent
            idx += 1
        # print('Find branching on',idx,'step')
        self.branch_code = self.curr_task.getBranchCodeTag()
        j = 0
        trg = self.curr_task
        while j < idx:
            found = False
            for child in trg.getChilds():
                if self.branch_code == child.getBranchCodeTag() and child in self.task_list:
                    trg = child
                    found = True
                    break
            if not found:
                break
            j += 1
        self.setCurrentTask(trg)
        # return self.getCurrTaskPrompts()

    def getSelectedTask(self) ->Task.BaseTask:
        if len(self.selected_tasks):
            return self.selected_tasks[0]
        return None
    
    def getMultiSelectedTasks(self) -> list[Task.BaseTask]:
        return self.multiselect_tasks
    
    def clearMultiSelectedTasksList(self):
        self.multiselect_tasks.clear()

    def addTaskToMultiSelectedByName(self, name : str):
        task = self.getTaskByName(name)
        self.addTaskToMultiSelected(task)

    def addTaskToMultiSelected(self, task : Task.BaseTask):
        if task != None and task not in self.multiselect_tasks and task in self.task_list:
            self.multiselect_tasks.append(task)

    def getCurrentTask(self) -> Task.BaseTask:
        return self.curr_task
    
    def getFrozenTasksCount(self) -> int:
        cnt = 0
        for t in self.task_list:
            if t.is_freeze:
                if t.getRootParent().checkType('ExternalInput'):
                    pass
                else:
                    cnt += 1
        return cnt

    def addTaskToSelectList(self, task :Task.BaseTask):
        if len(self.selected_tasks):
            self.selected_tasks.pop()
        self.selected_tasks.append(task)

    def clearSelectList(self):
        self.selected_tasks.clear()
        return ','.join( self.getSelectList())

    def addCurrTaskToSelectList(self):
        self.addTaskToSelectList(self.curr_task)

        return (','.join( self.getSelectList()), self.curr_task.getLastMsgContent())
    
    def getSelectedContent(self):
        out = self.selected_tasks
        if len(out):
            return out[0].getLastMsgContent()
        return ''

    def getSelectList(self) -> list:
        return [t.getName() for t in self.selected_tasks]

    def moveCurrentTaskUP(self):
        self.moveTaskUP(self.curr_task)
    
    def getSceletonBranchBuds(self, trg_task : Task.BaseTask):
        tree = trg_task.getTree()
        endes = []
        for task in tree:
            if task in self.task_list:
                childs = task.getChilds()
                cnt= 0
                for child in childs:
                    if child in self.task_list:
                        cnt += 1
                if cnt == 0:
                    endes.append(task)
        return endes
    
    def iterateOnBranchEnd(self):
        # Перебираем все возможные варианты листьев/почек деревьев
        if len(self.endes) == 0:
            self.endes = self.getSceletonBranchBuds(self.curr_task)
            self.endes_idx = 0
            self.endes.sort(key=self.sortBuds)
        else:
            endes = self.getSceletonBranchBuds(self.curr_task)
            if set(endes) == set(self.endes):
                if self.endes_idx + 1 < len(self.endes):
                    self.endes_idx += 1
                else:
                    self.endes_idx = 0
            else:
                self.endes = endes
                self.endes.sort(key=self.sortBuds)
                self.endes_idx = 0
        if len(self.endes) > self.endes_idx:
            self.curr_task = self.endes[self.endes_idx]

    def goToNextBranchEnd(self):
        # print('Go to next branch end')
        self.iterateOnBranchEnd()
        self.branch_code = self.curr_task.getBranchCodeTag()
        # print('Get new branch code:', self.branch_code)
    
    def getBranchEndTasksList(self) -> list[Task.BaseTask]:
        self.iterateOnBranchEnd()
        return [task for task in self.endes]

       

    def getBranchEnds(self) -> list[str]:
        # print('Get branch end list', self.getName())
        task = self.curr_task
        self.iterateOnBranchEnd()
        self.curr_task = task


        leaves_list = []
        trg = ''
        # for leave in self.endes:
        found = False
        if len(self.endes):
            pars = self.endes[self.endes_idx].getAllParents()
            if self.curr_task in pars:
                found = True
        for idx in range(len(self.endes)):
            leave = self.endes[idx]
            res, param = leave.getParamStruct('bud')
            name = leave.getName()
            if res:
                name += ':' + leave.findKeyParam (param['text'])
            
            leaves_list.append( name )


            if not found:
                pars = leave.getAllParents()
                if self.curr_task in pars:
                    self.endes_idx = idx
                    trg = name
            else:
                if self.endes_idx == idx:
                    trg = name
        return leaves_list

    def getBranchEndTask(self)-> Task.BaseTask:
        task = None
        trg = self.getCurrentTask()
        try:
            if len(self.endes) == 0:
                self.iterateOnBranchEnd()
            task = self.endes[self.endes_idx]
            if trg not in task.getAllParents():
                for idx, end in enumerate(self.endes):
                    if trg in task.getAllParents():
                        self.endes_idx = idx
                        return end
        except Exception as e:
            print('Error on get branch end:',e)
            task = self.curr_task
        return task
            

    def getBranchEndName(self):
        if len(self.endes) == 0:
            return ''
        leave = self.endes[self.endes_idx]
        res, param = leave.getParamStruct('bud')
        name = leave.getName()
        if res:
            name += ':' + leave.findKeyParam( param['text'])
        return name 
 
    def setCurrTaskByBranchEndName(self, name : str):
        print('Set current task by branch end name', name)
        i_max = len(self.endes)
        i = 0
        while i < i_max:
            self.iterateOnBranchEnd()
            if self.getBranchEndName() == name:
                break
            i += 1

    def goToTaskBud(self, start_task :Task.BaseTask):
        for task in start_task.getAllChildChains():
            if len(task.getChilds()) == 0:
                return task
        return start_task
    
    def getBranchUpFork(self, start_task :Task.BaseTask):
        fork = None
        trg = start_task
        idx = 0
        while(idx < 1000):
            par = trg.getParent()
            if par == None:
                return
            if len(par.getChilds()) > 1:
                fork = par
                fork_root = trg
                break
            else:
                trg = par
            idx +=1
        return fork, fork_root
 
    def getTaskNamesList(self) -> list[str]:
        # print('Get tasks list')
        out = []
        for task in self.task_list:
            out.append(task.getName())
        out.sort()
        return out
    
    def getLinksList(self) -> list:
        out = []
        for task in self.getTasks():
            for holder in task.getHoldGarlands():
                out.append({'from':task.getName(), 'to': holder.getName()})
        return out

    
    def getCurrTaskName(self):
        if self.curr_task:
            return self.curr_task.getName()
        return "None"
    
    def setCurrentTaskByName(self, name):
        task = self.getTaskByName(name)
        if task:
            print("Set current task=", task.getName())
            self.curr_task = task
        
        for i in range(0, len(self.task_list)):
            if self.task_list[i] == task:
                self.task_index = i
        # return self.getCurrTaskPrompts() 
           # in_prompt, in_role, out_prompt = self.curr_task.getMsgInfo()
        # return self.drawGraph(), gr.Dropdown.update(choices= self.getTaskNamesList()), in_prompt, in_role, out_prompt

    def setSelectedTaskByName(self, name):
        task = self.getTaskByName(name)
        if task:
            print("Set current task=", task.getName())
            self.slct_task = task

    def sortTreeOrder(self, check_list = False):
        # print('Tree idx', self.tree_idx, 'out of', len(self.tree_arr))
        self.updateTreeArr(check_list=check_list)
        if self.tree_idx >= len(self.tree_arr):
            self.tree_idx = 0

        if len(self.tree_arr) == 0:
            return
        trg_task = self.tree_arr[self.tree_idx]
        for task in self.tree_arr:
            res, pparam = task.getParamStruct('tree_step', only_current = True)
            if not res:
                self.curr_task = task
                task.setParamStruct({
                    'type':'tree_step',
                    'idx': 6,
                    'target': self.getCurrentTask().getName()
                })
                # self.appendNewParamToTask('tree_step') 
                   
        self.tree_arr.sort(key=self.sortKey)

        i = 0
        for task in self.tree_arr:
            # if trg_task == task:
                # self.tree_idx = i
            i += 1
            task.setTreeQueue()
        # print('Tree idx', self.tree_idx, 'out of', len(self.tree_arr))

    def getChainTaskFileByBranchCode(self, code : str) -> list:
        parts = re.findall(r"[0-9]+|[A-Z][a-z]*", code)
        idx = 0
        tasknames = []
        while idx < len(parts):
            short = parts[idx]
            res, val = self.getAndCheckLongName(short)
            if res:
                name = val + parts[idx + 1]
                if name not in tasknames:
                    tasknames.append(name)
            idx += 2
        return tasknames

    def getTaskFileNamesByBranchCode(self, code : str, name :str, projpath : str):
        man = self
        path = pathlib.Path( projpath )
        tasknames = man.getChainTaskFileByBranchCode(code)
        print('Get task file names by branch code [',code,']:', tasknames)
        fname = tasknames[0] +'.json'
        idx = 0
        allchaintasknames = [tasknames[0]]
        while( idx < 1000):
            fpath = path / fname
            info = Reader.ReadFileMan.readJson(Loader.Loader.getUniPath(fpath))
            if 'params' in info:
                childs_names = []
                found = False
                tname = ''
                for param in info['params']:
                    if 'type' in param and param['type'] == 'child':
                        childs_names.append(param['name'])
                        if param['name'] in tasknames:
                            found = True
                            tname = param['name']

                # print(fname,'childs:', len(childs_names))
                if name in childs_names:
                    allchaintasknames.append(name)
                    break
                elif len(childs_names) == 1:
                    fname = childs_names[0] + '.json'
                    allchaintasknames.append(childs_names[0])
                elif found:
                    fname = tname + '.json'                 
                    allchaintasknames.append(tname)   
                else:
                    print('Get chain in',idx,'iteration')
                    break
            idx += 1
        return allchaintasknames
    
    def getTaskFileNamesByBudName(self, budname : str, path : str) -> list[str]:
        print('Target bud', budname, 'by path', path)
        info= self.getFileContentByTaskName(budname, path)
        code = ''
        if 'params' in info:
            found = False
            for param in info['params']:
                if param['type'] == 'branch':
                    found = True
                    code = param['code']
            if not found:
                print('No branch code')
                return []
        else:
            print('No params in target file')
            return []
        return self.getTaskFileNamesByBranchCode(code, budname, path)

    def getTasks(self) -> list[Task.BaseTask]:
        return self.task_list.copy()

    def goBackByLink(self):
        task = self.getCurrentTask()
        trgs = task.getGarlandPart()
        if len(trgs) > 0:
            self.setCurrentTask(trgs[0])

    def getCurrentTreeRootTask(self) ->Task.BaseTask:
        return self.tree_arr[ self.tree_idx ]

    def isRelationTaskName(self, name : str):
        if name.startswith('GroupCollect'):
            return True
        if name.startswith('Collect'):
            return True
        if name.startswith('Garland'):
            return True
        return False

    def getRelatedTaskChains(self, starttaskname : str, project_path : str, max_idx = 1000) -> list[str]:
        taskchain = self.getTaskFileNamesByBudName(starttaskname, project_path)
        reltasknames = []
        for tname in taskchain:
            if self.isRelationTaskName(tname):
                reltasknames.append(tname)
        idx = 0
        while idx < max_idx:
            nreltasknames = []
            for rname in reltasknames:
                    info = self.getFileContentByTaskName(rname, project_path)
                    if 'linked' in info and len(info['linked']) > 0:
                        for link in info['linked']:
                            linkchain = self.getTaskFileNamesByBudName(link, project_path)
                            for lname in linkchain:
                                if self.isRelationTaskName(lname):
                                    nreltasknames.append(lname)
                            taskchain.extend(linkchain)
            if len(nreltasknames) > 0:
                reltasknames = nreltasknames
            else:
                return taskchain
            idx += 1
        print('Done in', idx,'range:',[t for t in taskchain])
        return taskchain

    def getBackwardRelatedTaskChain(self, trg_task : Task.BaseTask, max_idx : int):
        related = [t for t in trg_task.getAllParents() if t in self.task_list]
        idx = 0
        trgs = related.copy()
        while idx < max_idx:
            linked = []
            for task in trgs:
                linked.extend(task.getGarlandPart())
                related.extend(task.getGarlandPart())
            if len(linked) > 0:
                trgs = []
                for task in linked:
                    par = [t for t in task.getAllParents() if t in self.task_list]
                    trgs.extend(par)
                    related.extend(par)
            else:
                break
            idx += 1
        for task in related:
            self.addTaskToMultiSelected(task)

    def getForwardRelatedTaskChain(self, trg_task : Task.BaseTask, max_idx : int):
        childs = trg_task.getAllChildChains()
        out_tasks = childs
        idx = 0
        while idx < max_idx:
            new_childs = []
            for child in childs:
                for linked in child.getHoldGarlands():
                    linked_childs = linked.getAllChildChains()
                    new_childs.extend(linked_childs)
                    out_tasks.extend(linked_childs)
            if len(new_childs) == 0:
                break
            else:
                childs = new_childs
            idx += 1
        print('Done in', idx,'range:',[t.getName() for t in out_tasks])
        for task in out_tasks:
            self.addTaskToMultiSelected(task)


    def getFileContentByTaskName(self, name : str, path : str) -> dict:
        fpath = pathlib.Path(path) / (name + '.json')
        info =  Reader.ReadFileMan.readJson(Loader.Loader.getUniPath(fpath))
        if isinstance(info, dict):
            return info
        return {}
 
    def getBranchList(self):
        man = self
        task = man.curr_task
        out = []
        if task.getParent() == None:
            return out
        if len(task.getParent().getChilds()) < 2:
            return out
        task.getParent().sortChilds()
        for child in task.getParent().getChilds():
            name = str(child.getPrio()) + ':' + child.getName() + '\n'
            if task == child:
                out.append([name,'target'])
            else:
                out.append([name,'common'])
        return out

    def getBranchMessages(self):
        man = self
        task = man.curr_task
        out = ''
        if task.getParent() == None:
            return out
        task.getParent().sortChilds()
        for child in task.getParent().getChilds():
            res, val_src, _ = child.getLastMsgAndParent()
            if res and len(val_src):
                val = val_src[0]['content']
                if task == child:
                    out += '\n\n---\n\n'
                    out += '\n' + 5*'\\ --- \/ \\ --- \/ \\ --- \/' + ' \n'
                    out += '## ' + child.getName() + '\n'
                    # out += '\n\n---\n\n'
                    out += val 
                    # out += '\n\n---\n\n'
                    out += '\n' + 5*'\/ --- \\ \/ --- \\ \/ --- \\' + '\n'
                    out += '\n\n---\n\n'
                else:
                    out += '## ' + child.getName() + '\n'
                    out += val + '\n'
        return out
  
    def getTreesList(self, check = False):
        man = self
        task = man.curr_task
        out = []
        cur_tree = task.getRootParent()
        man.sortTreeOrder(True)
        for tree in man.tree_arr:
            sres, sparam = tree.getParamStruct('tree_step', True)
            name = tree.getBranchSummary()
            if sres:
                name +='[' + str( sparam['idx'] ) +']'
            name += '\n'
            if cur_tree == tree:
                out.append([name,'target'])
            else:
                out.append([name,'common'])
        return out
    
    def getChatRecord(self, idx : int):
        data = self.curr_task.getChatRecords()
        if idx < len(data):
            msgs = data[idx]['chat']
            return self.convertMsgsToChat(msgs=msgs)
        return []

    def getChatRecordRow(self, idx : int):
        data = self.curr_task.getChatRecords()
        out = []
        for i, pack in enumerate(data):
            chat = pack['chat']
            if idx < len(chat):
                out.append(chat[idx])
        return self.convertMsgsToChat(msgs=out)

    def getTaskByBranchCode(self, code: str):
        if code == "":
            return []
        out = []
        for task in self.task_list:
            if task.getBranchCodeTag() == code:
                out.append(task)
        return out

    def getMiniChainsFromMultiSelected(self):
        man = self
        # Я люблю опасность
        # for task in man.multiselect_tasks: 
        #     if len(task.getChilds() > 0):
        #         print('Try to copy fork')
        #         return act.updateUIelements()
        mtasks = man.getMultiSelectedTasks().copy()
        return self.getMiniChainsFromTasksList(mtasks)

    def getMiniChainsFromTasksList(self, mtasks):
        minichains = []
        for trg in mtasks:
            minichain = [t for t in trg.getAllParents() if t in mtasks]
            if len(minichain) > 0:
                minichains.append(minichain)
        chain_to_delete = []
        for i, trg_chain in enumerate( minichains ):
            for j, cmp_chain in enumerate( minichains ):
                if i != j and len(cmp_chain) < len(trg_chain):
                    for task in cmp_chain:
                        same = True
                        if task not in trg_chain:
                            same = False
                            break
                        if same and cmp_chain not in chain_to_delete:
                            chain_to_delete.append(cmp_chain)
        
        for chain in chain_to_delete:
            minichains.remove(chain)
        
        for chain in minichains:
            print('Branch:',[t.getName() for t in chain])
        return minichains

    def getSeparateTreesFromTaskList(self, tasks : list[ Task.BaseTask ]):
        treetasks = []
        for task in tasks:
            if task.getParent() is None or task.getParent() not in tasks:
                treetasks.append(task)
        return treetasks

    def setCurrentTask(self, task : Task.BaseTask):
        buds = task.getAllBuds()
        if self.endes_idx < len(self.endes) and self.endes[self.endes_idx] not in buds:
            for i, end in enumerate(self.endes):
                if end in buds:
                    self.endes_idx = i
        self.curr_task = task

    def getGlobalKeys(self):
        if 'global_vars' in self.info:
            return [t['key'] for t in self.info['global_vars']]
        return []
    
    def getGlobalValue(self, key : str):
        if 'global_vars' in self.info:
            for t in self.info['global_vars']:
                if t['key'] == key:
                    return True, t['value']
        return False, ""


# --------------------------------------------------------------------------------------------
    
    def appendGlobalVariables(self, key : str, value : str):
        pass

    def deleteGlobalVariable(self, key : str):
        pass
    
    def enableOutput2(self):
        pass

    def disableOutput2(self):
        pass
   
    def getColor(self) -> str:
        pass

    def setParam(self, param_name, param_value):
        pass

    def getParam(self, param_name):
        pass
    
    def getParamsLst(self):
        out = []
        return out
   
    def createCollectTreeOnSelectedTasks(self, action_type):
        return self.createTreeOnSelectedTasks(action_type,"Collect")

    def createTreeOnSelectedTasks(self, action_type : str, task_type : str):
        pass

    def moveTaskUP(self, task : Task.BaseTask):
        pass

    def getPath(self) -> str:
        return self.path
    
    def setPath(self, path : str):
        pass

    def getTaskExtention(self) -> str:
        return '.json'

    def getProjPrefix(self) -> str:
        return self.proj_pref

    def loadTasksList(self, safe = False, trg_files = []):
        pass
  
   
    def setBranchEndName(self, summary):
        pass
   
    def getCopyTasks(self, start_task : Task.BaseTask) ->list[ Task.BaseTask]:
        return []

    def getCopyBranch(self, start_task: Task.BaseTask) ->list[ Task.BaseTask]:
        return []
    

    def updateEditToCopyBranch(self, start_task : Task.BaseTask):
        pass
    
    def getTextFromFile(self, text, filenames):
        pass
    
    def addRenamedPair(self, stdtaskname : str, chgtaskname : str):
        pass

    def clearRaenamedList(self):
        pass
    
    def checkParentName(self, task_info, parent : Task.BaseTask) -> bool:
        return False
        
    def getParentSavingName(self, task : Task.BaseTask):
        pass

    def createTaskByFile(self, parent : Task.BaseTask = None, files = []):
        pass
   
    def applyLinks(self,linklist):
        pass

    def loadTasksListFileBased(self, files = []):
        pass

    def createTask(self, prnt_task = None, safe = False, trg_tasks = []):
        pass

    def setNextTask(self, input):
        pass

    def updateGraph(self, image):
        pass
    
    def getActionTypes(self):
        pass
    
    def getRoleTypes(self):
        pass

    def getTaskJsonStr(self):
        pass

    def getTaskParamRes(self, task, param) -> bool:
        pass
    
    def drawSceletonBranches(self):
        pass
    
    def drawGraph(self, only_current= True, max_index = -1, path = "output/img", hide_tasks = True, add_multiselect = False, max_childs = 3, add_linked=False, all_tree_task = False):
        pass

    def updatePromptForTask(self, task_name, task_prompt):
        pass
    def getOutputDataSum(self):
        pass
    def updateAndGetOutputDataSum(self):
        pass

    def getFlagTaskLst(self):
        pass
   
    def getMainCommandList(self):
        pass
    def getSecdCommandList(self):
        pass
    
    def makeRequestAction(self, prompt, selected_action, selected_tag):
        pass
        
       
        
    def makeResponseAction(self, selected_action):
        pass
        
 
    def makeTaskAction(self, prompt, type, creation_type, creation_tag, params = [], trgtaskname = ''):
        pass
    
 
    def makeTaskActionPro(self, prompt, type, creation_type, creation_tag, params = []):
        pass
    def updateTaskParam(self, param):
        pass
    
    def makeTaskActionBase(self, prompt, type, creation_type, creation_tag, params = [], trgtaskname = ''):
        pass
       
    def createOrAddTask(self, prompt, type, tag, parent, params = [], trgtaskname = ''):
        pass
        
    def makeLink(self, task_in : Task.BaseTask, task_out : Task.BaseTask):
        pass
    
    def getTaskByName(self, name : str) -> Task.BaseTask:
        for task in self.task_list:
            if task.getName() == name:
                return task
        # print('Can\'t get task by name', name)
        return None
    
    def updateSetOption(self, task_name, param_name, key, value):
        pass
    def getFromSetOptions(self, task : Task.BaseTask):
        pass
       
 
    def updateTaskParams(self, initparams : list, addparams : list):
        pass
    def createOrAddTaskByInfo(self,task_type, info : Task.TaskDescription):
        pass
    def runCmdList(self) -> Task.BaseTask:
        pass
    def runIteration(self, prompt = ''):
        pass
   
    def updateCurrent(self):
        pass
    
    def update(self):
        pass
    def updateSteppedSelectedInternal(self, info : Task.TaskDescription = None, update_task = True):
        pass
    def resetCurTaskQueue(self):
        pass
    
    def fixTasks(self):
        pass
    
    def updateAndExecuteStep(self, msg):
        pass
    def executeStep(self):
        pass
    
    def executeSteppedBranch(self, msg):
        pass
    def updateSteppedTrgBranch(self, info = None):
        pass

    
    def updateSteppedTree(self, info = None):
        pass
   
    
    def getCurTaskLstMsg(self) -> str:
        pass
    
    def getCurTaskLstMsgRaw(self) -> str:
        pass
    
    def getCurTaskRole(self) -> str:
        pass
        
    
    


    def convertMsgsToChat(self, msgs):
        pass
    
    def getByTaskNameParamListInternal(self, task : Task.BaseTask):
        pass
   
    
    def getPathToFolder(self):
        pass
   
    def getPathToFile(self):
        pass
 
    def getShortName(self, n_type : str, n_name : str) -> str:
        pass
   
    def getAndCheckLongName(self, short_name : str) -> list[bool,str]:
        pass
 
    
   
    def setTaskKeyValue(self, param_name, key, mnl_value):
        pass
    def getAppendableParam(self):
        pass

    def appendNewParamToTask(self, param_name):
        pass
   
    def removeParamFromTask(self, param_name):
        pass
 
    def updateSteppedSelected(self):
        pass
    def processCommand(self, json_msg,  tasks_json):
        pass

    def syncCommand(self, send_task_list):
        pass
 
   
    def beforeRemove(self, remove_folder = False, remove_task = True):
        pass

    def createExtProject(self, filename, prompt, parent) -> bool:
        pass
    def copyChildChainTask(self, change_prompt = False, edited_prompt = '',
                           trg_type_t = '', src_type_t = '', 
                           forced_parent = False
                           ):
        pass
    
    def copyTasksChain(self, tasks_chains, change_prompt = False, 
                       edited_prompt = '',trg_type_t = '', src_type_t = '', 
                       forced_parent = False):

        pass
    def copyTaskByInfoInternal(self):
        pass

    def getTasksChainsFromCurrTask(self, param):
        pass

    def copyTasksByInfo(self, tasks_chains, change_prompt = False, edited_prompt = '', switch = [], new_parent = None, ignore_conv = [], param = {}):
        pass

    def copyTasksByInfoStart(self, tasks_chains, change_prompt = False, edited_prompt = '',switch = [], new_parent = None, ignore_conv = [], param = {}):
        pass
               
    def copyTasksByInfoExe(self):
        pass

    def copyTasksByInfoStep(self):
        pass
    def copyTasksByInfoStop(self):
        pass
    def getCopyedTask(self, tasks_chans, task):
        pass


    def copyChildChains(self, change_prompt = False, edited_prompt = '',
                        trg_type = '', src_type = '', 
                        apply_link = False, remove_old_link = False, 
                        copy = False, subtask = False):
        pass


    def saveInfo(self, check = False):
        pass

    def addActions(self, action = '', prompt = '', tag = '', act_type = '', param = {}):
        pass
    def remLastActions(self):
        pass

    def initInfo(self, method, task : Task.BaseTask = None, path = 'saved', act_list = [], repeat = 3, limits = 1000, params = {}):
        # print(self.info)
        pass
   

    def addTask(self, task : Task.BaseTask):
        pass
    
    def rmvTask(self, task: Task.BaseTask):
        pass
 

    def addTasks(self, tasks: list):
        pass
    
   
    def removeTaskList(self, del_tasks):
        pass


   
    def copyTasksIntoManager(self, tasks : list[ Task.BaseTask]):
        pass
    def allowUpdateInternalArrayParam(self):
        pass
    
   
    def copyTree(self, branch_infos):
        pass
    
    def copyBranchPartByInfo(self, branch, start_parent: Task.BaseTask):
        pass

    def forceUnFreezeParentTasks( self, task : Task.BaseTask ):
        pass
    