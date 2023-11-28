from genslides.commands.simple import SimpleCommand
from genslides.task.base import TaskDescription


class EditCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)

    def execute(self) -> None:
        input = self.input
        info = TaskDescription(prompt=input.prompt,prompt_tag=input.creation_tag, manual=True)
        self.info = TaskDescription( prompt=trg.getLastMsgContent(), prompt_tag=trg.getLastMsgRole(), manual=True)
        trg = input.target
        self.trg = trg
        trg.update(info)
        return super().execute()
    
    def unexecute(self) -> None:
        self.trg.update(self.info)
        return super().unexecute()
    
class AppendParamCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)

    def execute(self) -> None:
        task = self.input.target
        p = self.input.params
        task.setParamStruct(p)
        return super().execute()
    
    def unexecute(self) -> None:
        return super().unexecute()
    
class EditParamCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)
    
    def execute(self) -> None:
        task = self.input.target
        p = self.input.params
        res, val = task.getCurParamStructValue(p['name'], p['key'])
        task.updateParamStruct(p['name'], p['key'], p['select'])
        if res:
            p['select'] = val
        return super().execute()
    
    def unexecute(self) -> None:
        task = self.input.target
        p = self.input.params
        task.updateParamStruct(p['name'], p['key'], p['select'])
        return super().unexecute()
    

class MoveUpTaskCommand(SimpleCommand):
    def __init__(self, input) -> None:
        super().__init__(input)

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
        print('Move task', task.getName(),'UP')
        task_B = task.parent
        task_C = task
        task_trgs = [task_B, task_C]
        print('Start chain:',[t.getName() for t in task.getAllParents()])
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

            print('Child C:',[t.getName() for t in childs_C])
            print('child',task_B.getName(),'start:',[t.getName() for t in task_B.getChilds()],'of')
            for child in childs_C:
                task_B.addChild(child)
            print('CHILDS RESULT:',[t.getName() for t in task_B.getChilds()])

            childs_B.append(task_B)
            task_trgs.extend(childs_B)
            task_trgs.extend(childs_C)

            print('Child B:',[t.getName() for t in childs_B])
            print('child start:',[t.getName() for t in task_C.getChilds()])
            for child in childs_B:
                task_C.addChild(child)
            print('CHILDS RESULT:',[t.getName() for t in task_C.getChilds()])

            if task_A is not None:
                task_A.addChild(task_C)
                task_A.update()
            else:
                task_C.update()

            for t in task_trgs:
                t.saveAllParams()
        else:
            print('Nothing to switch')

        
        print('Task A:',[t.getName() for t in task_A.getAllParents()])
        print('ChildA:',[t.getName() for t in task_A.getChilds()])
        print('Task C:',[t.getName() for t in task_C.getAllParents()])
        print('ChildC:',[t.getName() for t in task_C.getChilds()])
        print('Task B:',[t.getName() for t in task_B.getAllParents()])
        print('ChildB:',[t.getName() for t in task_B.getChilds()])


    