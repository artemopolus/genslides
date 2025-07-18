from genslides.commands.simple import SimpleCommand
from genslides.task.base import TaskDescription, BaseTask
import genslides.utils.loader as Ld

class EditCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)
        self.name = "edit"

    def execute(self) -> None:
        input = self.input
        info = TaskDescription(prompt=input.prompt,prompt_tag=input.prompt_tag, manual=True)
        trg = input.target
        self.info = TaskDescription( prompt=trg.getLastMsgContent(), prompt_tag=trg.getLastMsgRole(), manual=True)
        self.trg = trg
        trg.update(info)
        return super().execute()
    
    def unexecute(self) -> None:
        self.trg.update(self.info)
        return super().unexecute()
    
class AppendParamCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)
        self.name = "append_param"

    def execute(self) -> None:
        task = self.input.target
        p = self.input.params
        task.setParamStruct(p)
        return super().execute()
    
    def unexecute(self) -> None:
        return super().unexecute()
    
class RemoveParamCommand(SimpleCommand):
    def __init__(self, input: TaskDescription) -> None:
        super().__init__(input)
        self.old_param = None
        self.name = "remove_param"
    
    def execute(self) -> None:
        task = self.input.target
        p = self.input.params
        param_name = p['name']
        res, param = task.getParamStruct(param_name, only_current = True)
        if res:
            self.old_param = param
        task.rmParamStructByName(param_name)
        return super().execute()
    
    def unexecute(self) -> None:
        return super().unexecute()
    
class EditParamCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)
        self.name = "edit_param"
    
    def execute(self) -> None:
        task = self.input.target
        p = self.input.params
        res, old_value = task.getCurParamStructValue(p['name'], p['key'])
        value = p['select']
        if p['name'] == 'array' and p['key'] == 'array':
            res, jopt = Ld.Loader.loadJsonFromText(value)
            if res:
                value = jopt
        elif isinstance( value, dict):
            if res and isinstance (old_value, str):
                value = Ld.Loader.convJsonToText( value )
        elif isinstance(value, str) and value.isdigit():
            print(value,'is int')
            value = int(value)
        elif isinstance(value, str) and value.replace('.', '', 1).isdigit():
            print(value,'is float')
            value = float(value)
        # print('Update', p['key'],'for',p['name'],'with', value,'[', task.getName(),']')
        task.updateParamStruct(p['name'], p['key'], value)
        if res:
            value = old_value
        return super().execute()
    
    def unexecute(self) -> None:
        task = self.input.target
        p = self.input.params
        task.updateParamStruct(p['name'], p['key'], p['select'])
        return super().unexecute()
    
class MoveDownTaskCommand( SimpleCommand ):
    def __init__(self, input):
        super().__init__(input)
        self.name = "move_task_down"
        self.task_B : BaseTask = self.input.parent
        self.task_C : BaseTask = self.input.target
        self.task_A : BaseTask = None
        self.task_B_children : list[BaseTask] = []
        self.task_C_children : list[BaseTask] = []
        # move switch parent and target
    def execute(self):
        self._moveTaskDown( self.task_B, self.task_C )
        return super().execute()
    
    def unexecute(self):
        self._moveTaskUp()
        return super().unexecute()

    def _moveTaskDown(self, parent : BaseTask, target : BaseTask):
        task_A : BaseTask = parent.getParent()
        parent_children : list[BaseTask] = parent.getChilds()
        if target in parent_children:
            parent_children.remove( target )
        else:
            return
        target_children : list[BaseTask] = target.getChilds()

        self.task_A = task_A
        self.task_B_children = parent_children
        self.task_C_children = target_children

        if self.task_A == self.task_B or self.task_A == self.task_C or self.task_B == self.task_C:
            return
        target.removeParent()
        parent.removeParent()
        task_A.addChild(target)
        for child in parent_children:
            child.removeParent()
            target.addChild(child)
        target.addChild(parent)
        for child in target_children:
            child.removeParent()
            parent.addChild(child)
        self._saveAllParameters()

    def _saveAllParameters(self):
        self.task_A.saveAllParams()
        self.task_B.saveAllParams()
        self.task_C.saveAllParams()
        for child in self.task_B_children:
            child.saveAllParams()
        for child in self.task_C_children:
            child.saveAllParams()

    def _moveTaskUp( self):
        self.task_B.removeParent()
        self.task_C.removeParent()
        self.task_A.addChild(self.task_B)
        for child in self.task_B_children:
            child.removeParent()
            self.task_B.addChild(child)
        self.task_B.addChild(self.task_C)
        for child in self.task_C_children:
            child.removeParent()
            self.task_C.addChild(child)
        self._saveAllParameters()
        
    

class MoveUpTaskCommand(SimpleCommand):
    def __init__(self, input : TaskDescription) -> None:
        super().__init__(input)
        self.name = "move_task_up"

    def execute(self) -> None:
        task = self.input.target
        self.parent = task.parent
        self.moveTaskUP(task)
        return super().execute()
    
    def unexecute(self) -> None:
        if self.parent:
            self.moveTaskUP(self.parent)
        return super().unexecute()
    
    def moveTaskUP(self, task ):
        # print('Move task', task.getName(),'UP')
        task_A = None
        task_B = task.parent
        task_C = task
        task_trgs = [task_B, task_C]
        # print('Start chain:',[t.getName() for t in task.getAllParents()])
        if task_B is not None:
            if task_B.parent is not None:
                task_A = task_B.parent
                task_trgs.append(task_A)
            childs_C = task_C.getChilds()
            childs_B = task_B.getChilds()
            childs_B.remove(task_C)

            task_B.removeAllChilds()
            task_B.removeParent()
            task_C.removeAllChilds()
            task_C.removeParent()

            # print('Child C:',[t.getName() for t in childs_C])
            # print('child',task_B.getName(),'start:',[t.getName() for t in task_B.getChilds()],'of')
            for child in childs_C:
                task_B.addChild(child)
            # print('CHILDS RESULT:',[t.getName() for t in task_B.getChilds()])

            childs_B.append(task_B)
            task_trgs.extend(childs_B)
            task_trgs.extend(childs_C)

            # print('Child B:',[t.getName() for t in childs_B])
            # print('child start:',[t.getName() for t in task_C.getChilds()])
            for child in childs_B:
                task_C.addChild(child)
            # print('CHILDS RESULT:',[t.getName() for t in task_C.getChilds()])

            if task_A is not None:
                task_A.addChild(task_C)
                task_A.freezeTask()
                # task_A.update()
            else:
                task_C.freezeTask()
                # task_C.update()

            for t in task_trgs:
                t.saveAllParams()
        else:
            print('Nothing to switch')

        
        # if task_A is not None:
        #     print('Task A:',[t.getName() for t in task_A.getAllParents()])
        #     print('ChildA:',[t.getName() for t in task_A.getChilds()])
        # print('Task C:',[t.getName() for t in task_C.getAllParents()])
        # print('ChildC:',[t.getName() for t in task_C.getChilds()])
        # print('Task B:',[t.getName() for t in task_B.getAllParents()])
        # print('ChildB:',[t.getName() for t in task_B.getChilds()])

class InsertTaskCommand(SimpleCommand):
    def __init__(self, input):
        super().__init__(input)
        self.name = "insert_task"
        self.task = input.target
        self.parent = self.task.getParent()
        self.task2 = input.parent

        # print(f"{self.parent.getName()} - {self.task.getName()} - {self.task2.getName()}")
    
    def execute(self):
        self.insertTaskInChain( self.parent, self.task2, self.task )
        return super().execute()
    
    def unexecute(self):
        self.revertInserting( self.parent, self.task2, self.task )
        return super().unexecute()
    
    def insertTaskInChain( self, task1 : BaseTask, task2 : BaseTask, task_12 : BaseTask ):
        if task1 == task2 or task2 == task_12 or task1 == task_12:
            return
        if task1 is not None:
            task1.addChild(task_12)
            task2.removeParent()
            task_12.addChild(task2)
            task1.saveAllParams()
            task2.saveAllParams()
            task_12.saveAllParams()
        else:
            task_12.addChild(task2)
            task2.saveAllParams()
            task_12.saveAllParams()

    def revertInserting( self, task1 : BaseTask, task2 : BaseTask, task_12 : BaseTask):
        if task1 is not None:
            task2.removeParent()
            task1.addChild(task2)

            task1.saveAllParams()
            task2.saveAllParams()
            task_12.saveAllParams()
        else:
            task2.removeParent()

            task2.saveAllParams()
            task_12.saveAllParams()

class ExtractTaskCommand(SimpleCommand):
    def __init__(self, input):
        super().__init__(input)
        self.name = "extract_task"
        self.task = input.target
        self.children = self.task.getChilds()
        self.parent = self.task.getParent()


    def execute(self):
        self.extract ( self.parent, self.task, self.children )
        return super().execute()
    
    def unexecute(self):
        self.revertExtract ( self.parent, self.task, self.children )
        return super().unexecute()
    
    def extract(self, task1 : BaseTask, task2 : BaseTask, task3_list : list[BaseTask]):
        for task in task3_list:
            task.removeParent()
            if task1 is not None:
                task1.removeChild(task2)
                task1.addChild(task)
            task.saveAllParams()
        task1.saveAllParams()
        task2.saveAllParams()

    def revertExtract(self, task1 : BaseTask, task2 : BaseTask, task3_list : list[BaseTask]):
        task1.addChild( task2 )
        for task in task3_list:
            task.removeParent()
            task2.addChild(task)
            task.saveAllParams()
        
        task1.saveAllParams()
        task2.saveAllParams()
