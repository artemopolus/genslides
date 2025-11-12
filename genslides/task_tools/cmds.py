import genslides.commanager.man as Manager
import genslides.task_tools.text as TextTool

def parseEditInsert( targettaskname, man : Manager.Jun, edit_type : str, direct_cmd_update : str, copy_to_dict, reason : str, batch, next_stage_actions):
    print(f"Target task: {targettaskname}")
    updatetask = man.getTaskByName( targettaskname)
    roottreetask = updatetask.getRootParent()
    print(f"Root task: {roottreetask.getName()}")
    if roottreetask.checkTags("srcdoctree"):
        print("Add doc tree task")
    # if updatetask and updatetask.checkType("Request"):
        if edit_type == "Insertion":
            if direct_cmd_update: 
                updttskchilds : list[Manager.BaseTask] = updatetask.getChilds()
                updtaskchild = updatetask 
                if len(updttskchilds):
                    for child in updttskchilds:
                        if child.checkTags(["insert","autogenerate"]) or child.checkTags(["node"]):
                            updtaskchild = child
                            break
                targettaskname = updtaskchild.getName()
                cmd = {"action":"insertingToTaskAction","kwargs":{"taskname":targettaskname,"prompt":batch, "task_params" : [
                    {"type":"tag","text":"insert,autogenerate","key":""}
                    ]},"reason":reason}
                cmd, report = addSupportInformation( cmd, man )
                updtaskchild.updateAutoCommand2param(cmd)
            if copy_to_dict:
                updatetask.saveDictBuffer({"action":"insertingToTaskAction","taskname":targettaskname,"prompt":batch, "task_params":[
                    {"type":"tag","text":"insert,autogenerate","key":""}
                ]})
            # command_to_execute.append({"action":"insertingToTaskAction","kwargs":{"taskname":targettaskname,"prompt":batch}})
        elif edit_type == "Replacement":
            if direct_cmd_update:
                cmd = {"action":"editingToTaskAction","kwargs":{"taskname":targettaskname,"prompt":batch},"reason":reason}
                cmd, report = addSupportInformation( cmd, man )
                updatetask.updateAutoCommand2param(cmd)
            if copy_to_dict:
                updatetask.saveDictBuffer({"action":"editingToTaskAction","taskname":targettaskname,"prompt":batch})
            # command_to_execute.append({"action":"editingToTaskAction","kwargs":{"taskname":targettaskname,"prompt":batch}})
        else:
            print("Unknown edit type")
    elif roottreetask.checkTags("intertree"):
    # elif updatetask and updatetask.checkType("Listener"):
        print("Add INTER tree task")
        next_stage_actions.append({"action":"createSecondStageLink","kwargs":{"taskname":targettaskname},"reason":reason})
        # updatetask.updateAutoCommand2param({"action":"createSecondStageLink","kwargs":{"taskname":targettaskname}})
        # listener_to_up.append({"action":"createSecondStageLink","kwargs":{"taskname":targettaskname}})
    else:
        print("Unknown action")

def addSupportInformation( command : dict, manager : Manager.Jun):
    print("add support information")
    result = []
    action_type = command.get("action", "")
    kwargs = command.get("kwargs",{})
    
    if action_type == "uniteTwoTaskByName":
        united_name = kwargs.get("task_marker1","")
        removed_name = kwargs.get("task_marker2","")
        result.append({"status":"divider","content":f"==={action_type}:{united_name}, {removed_name}============>\n\n"})
        united = manager.getTaskByAnyName(united_name)
        removed = manager.getTaskByAnyName(removed_name)
        if united != None and removed != None:
            if united in removed.getAllParents():
                pass
            else:
                tmp = united
                united = removed
                removed = tmp
            uptext = ""
            upmark = ""
            if united.getParent() != None:
                uptext = united.getParent().getLastMsgContentRaw()
                upmark = united.getParent().getName()
                result.append({"status":"stay","content":uptext,"marker":upmark})
            result.append({"status":"target","content":united.getLastMsgContentRaw(),"marker":united.getName()})
            result.append({"status":"append","content":removed.getLastMsgContentRaw(),"marker":removed.getName()})
            united_child = united.getFirstChild()
            if united_child == removed and len(removed.getChilds()):
                result.append({"status":"stay","content":removed.getFirstChild().getLastMsgContentRaw(),"marker":removed.getName()})
            elif united_child != None and united_child != removed:
                result.append({"status":"stay","content":united.getFirstChild().getLastMsgContentRaw(),"marker":united.getName()})
        else:
            return command, f"No tasks for {united_name}, {removed_name}"
    elif action_type == "moveTask":
        target_name = kwargs.get("marker","")
        target = manager.getTaskByAnyName(target_name)
        direction = kwargs.get("direction","")
        result.append({"status":"divider","content":f"==={action_type}:{target_name}, {direction}============>\n\n"})
        text  = target.getLastMsgContentRaw()
        uptext  = ""
        dwtext  = ""
        if direction == "UP":
            uptask = None if target.getParent() else target.getParent().getParent()
            uptext = "" if uptask == None else uptask.getLastMsgContentRaw()
            upmark = "" if uptask == None else uptask.getName()
            dwtext = "" if target.getParent() == None else target.getParent().getLastMsgContentRaw()
            dwmark = "" if target.getParent() == None else target.getFirstChild().getName()
        elif direction == "DOWN":
            if len(target.getChilds()) > 0:
                uptask : Manager.Task.BaseTask = target.getFirstChild()
                uptext = "" if uptask == None else uptask.getLastMsgContentRaw()
                upmark = "" if uptask == None else uptask.getName()
                dwmark = ""
                if uptask != None and len(uptask.getChilds()) > 0 and uptask.getFirstChild() != None:
                    dwtext = uptask.getFirstChild().getLastMsgContentRaw()
                    dwmark = uptask.getFirstChild().getName()
                else:
                    dwtext = ""
                    # return command, f"Error on move"
        # if uptask != None and dwtask != None:
        if direction == "DOWN":
            result.append({"status":"delete","content":text,"marker":target_name})
        result.append({"status":"stay","content":uptext,"marker":upmark})
        result.append({"status":"append","content":text,"marker":target_name})
        result.append({"status":"stay","content":dwtext,"marker":dwmark})
        if direction == "UP":
            result.append({"status":"delete","content":text,"marker":target_name})
        # else:
            # return command, f"Error on move"
    elif action_type == "deleteTask":
        target_name = kwargs.get("marker","")
        target = manager.getTaskByAnyName(target_name)
        result.append({"status":"divider","content":f"==={action_type}:{target_name}============>\n\n"})
        if target != None:
            uptask : Manager.Task.BaseTask = target.getParent()
            uptext  = "" if uptask == None else uptask.getLastMsgContentRaw()
            upmark = "" if uptask == None else uptask.getName()
            dwtext  = "" if len(target.getChilds()) == 0 else target.getFirstChild().getLastMsgContentRaw()
            dwmark  = "" if len(target.getChilds()) == 0 else target.getFirstChild().getName()
            result.append({"status":"stay","content":uptext,"marker":upmark})
            result.append({"status":"delete","content":target.getLastMsgContentRaw(),"marker":target_name})
            result.append({"status":"stay","content":dwtext,"marker":dwmark})
    elif action_type == "insertingToTaskAction":
        target_name = kwargs.get("taskname","")
        result.append({"status":"divider","content":f"==={action_type}:{target_name}============>\n\n"})
        insert_text = kwargs.get("prompt","")
        target = manager.getTaskByAnyName(target_name)
        if target != None:
            uptask : Manager.Task.BaseTask = target.getParent()
            uptext  = "" if uptask == None else uptask.getLastMsgContentRaw()
            upmark = "" if uptask == None else uptask.getName()
            # dwtext  = "" if len(target.getChilds()) == 0 else target.getFirstChild().getLastMsgContentRaw()
            result.append({"status":"stay","content":uptext,"marker":upmark})
            result.append({"status":"append","content":insert_text,"marker":"NewRequest"})
            result.append({"status":"stay","content":target.getLastMsgContentRaw(),"marker":target_name})
    elif action_type == "editingToTaskAction":
        target_name = kwargs.get("taskname","")
        result.append({"status":"divider","content":f"==={action_type}:{target_name}============>\n\n"})
        insert_text = kwargs.get("prompt","")
        target = manager.getTaskByAnyName(target_name)
        if target != None:
            uptask : Manager.Task.BaseTask = target.getParent()
            uptext  = "" if uptask == None else uptask.getLastMsgContentRaw()
            upmark = "" if uptask == None else uptask.getName()
            dwtext  = "" if len(target.getChilds()) == 0 else target.getFirstChild().getLastMsgContentRaw()
            dwmark  = "" if len(target.getChilds()) == 0 else target.getFirstChild().getName()
            result.append({"status":"stay","content":uptext,"marker":upmark})
            result.append({"status":"append","content":insert_text,"marker":target_name})
            result.append({"status":"delete","content":target.getLastMsgContentRaw(),"marker":target_name})
            result.append({"status":"stay","content":dwtext,"marker":dwmark})


    elif action_type == "divideTaskBasedOnPrompt":
        print("divide task")
        target_name = kwargs.get("taskname","")
        result.append({"status":"divider","content":f"==={action_type}:{target_name}============>\n\n"})
        text_before = kwargs.get("text_before","")
        text_after = kwargs.get("text_after","")
        target = manager.getTaskByAnyName(target_name)
        if target != None:
            print("task found")
            found_max_score = 0
            found_task = None
            for task in target.getAllParents():
                text = task.getLastMsgContentRaw()
                res, parts, score = TextTool.divide_based_on_texts_above_below(  text, text_before, text_after )
                print(f"Task {task.getName()} score: {score}")
                if res and score > found_max_score:
                    found_max_score = score
                    divided_parts = parts
                    found_task = task
            if found_task != None and found_max_score > 0:
                print("add divided")
                uptask : Manager.Task.BaseTask = found_task.getParent()
                uptext  = "" if uptask == None else uptask.getLastMsgContentRaw()
                upmark = "" if uptask == None else uptask.getName()
                dwtext  = "" if len(found_task.getChilds()) == 0 else target.getFirstChild().getLastMsgContentRaw()
                dwmark  = "" if len(target.getChilds()) == 0 else target.getFirstChild().getName()
                result.append({"status":"stay","content":uptext,"marker":upmark})
                result.append({"status":"target","content":divided_parts[0],"marker":found_task.getName()})
                result.append({"status":"append","content":divided_parts[1],"marker":"NewRequest"})
                result.append({"status":"stay","content":dwtext,"marker":dwmark})
            else:
                result.append({"status":"stay","content":target.getLastMsgContentRaw(),"marker":target_name})

        else:
            print(f"No task with marker {target_name}")
    if len(result):
        result.append({"status":"divider","content":"\n\n********\n\n"})
        command["aa_info"] = result
    return command, f"Added {len(result)} batches"

def highlightCmdResult(command : dict):
    out = []
    if "aa_info" in command:
        results : list[dict] = command.get("aa_info",[])
        for res in results:
            status = res.get("status","")
            text = res.get("content","")
            if status == "append":
                out.append([text, "add"])
            elif status == "delete":
                out.append([text, "del"])
            elif status == "target":
                out.append([text, "trg"])
            elif status == "divider":
                out.append([text, "div"])
            else:
                out.append([text, None])
    return out

def getMarkDownResult( command : dict ):
    out_text = ""
    if "aa_info" in command:
        results : list[dict] = command.get("aa_info",[])
        for res in results:
            status = res.get("status","")
            text = res.get("content","")
            marker = res.get("marker","")
            if status == "append":
                out_text += f"**{marker}** {text}"
            elif status == "delete":
                out_text += f"**{marker}** ~~{text}~~"
            elif status == "target":
                out_text += f"**{marker}** {text}"
            elif status == "divider":
                pass
            else:
                out_text += f"**{marker}** {text}"
    return out_text
