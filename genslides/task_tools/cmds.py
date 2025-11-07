import genslides.commanager.man as Manager

def parseEditInsert( man : Manager.Jun, edit_type : str, direct_cmd_update : str, copy_to_dict, reason : str, batch, next_stage_actions):
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
                updtaskchild.updateAutoCommand2param({"action":"insertingToTaskAction","kwargs":{"taskname":targettaskname,"prompt":batch, "task_params" : [
                    {"type":"tag","text":"insert,autogenerate","key":""}
                    ]},"reason":reason})
            if copy_to_dict:
                updatetask.saveDictBuffer({"action":"insertingToTaskAction","taskname":targettaskname,"prompt":batch, "task_params":[
                    {"type":"tag","text":"insert,autogenerate","key":""}
                ]})
            # command_to_execute.append({"action":"insertingToTaskAction","kwargs":{"taskname":targettaskname,"prompt":batch}})
        elif edit_type == "Replacement":
            if direct_cmd_update:
                updatetask.updateAutoCommand2param({"action":"editingToTaskAction","kwargs":{"taskname":targettaskname,"prompt":batch},"reason":reason})
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
    result = []
    if command.get("action", "") == "uniteTwoTaskByName":
        united = manager.getTaskByName(command.get("task_marker1",""))
        removed = manager.getTaskByName(command.get("task_marker2",""))
        if united != None and removed != None:
            if united in removed.getAllParents():
                result.append({"status":"stay","content":united.getLastMsgContentRaw()})
                result.append({"status":"append","content":removed.getLastMsgContentRaw()})
                if united.getChilds() > 0:
                    result.append({"status":"stay","content":united.getChilds[0].getLastMsgContentRaw()})
            else:
                result.append({"status":"stay","content":removed.getLastMsgContentRaw()})
                result.append({"status":"append","content":united.getLastMsgContentRaw()})
                if removed.getChilds() > 0:
                    result.append({"status":"stay","content":removed.getChilds[0].getLastMsgContentRaw()})

    if len(result):
        command["aa_info"] = result
    return command
