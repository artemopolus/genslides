import re
import genslides.utils.loader as Loader

def findByKey(text, manager , base ):
         results = re.findall(r'\{.*?\}', text)
         print("Find keys=", text)
        #  print("Results=", results)
         rep_text = text
         for res in results:
             arr = res[1:-1].split(":")
            #  print("Keys:", arr)
             if len(arr) > 1:
                 task = None
                 if arr[0] == 'manager':
                    if arr[1] == 'path':
                        trg_text = manager.getPath()
                        rep_text = rep_text.replace(res, trg_text)
                 else:
                    task = base.getAncestorByName(arr[0])
                 if task:
                    if len(arr) > 5:
                        if 'type' == arr[1]:
                            bres, pparam = task.getParamStruct(arr[2])
                            if bres and arr[3] in pparam and pparam[arr[3]] == arr[4] and arr[5] in pparam:
                                rep = pparam[arr[5]]
                                rep_text = rep_text.replace(res, str(rep))
                    elif arr[1] == manager.getMsgTag():
                        param = task.getLastMsgContent()
                        if len(arr) > 3 and arr[2] == 'json':
                            bres, j = Loader.loadJsonFromText(param)
                            if bres:
                                rep = j[arr[3]]
                                rep_text = rep_text.replace(res, str(rep))
                            else:
                                print("No json in", task.getName())
                        else:
                            print("Replace", res, "from",task.getName())
                            rep_text = rep_text.replace(res, str(param))
                    elif arr[1] == manager.getTknTag():
                        tkns, price = task.getCountPrice()
                        rep_text = rep_text.replace(res, str(tkns))
                    elif arr[1] == manager.getBranchCodeTag():
                        p_tasks = task.getAllParents()
                        print('Get branch code',[t.getName() for t in p_tasks])
                        code_s = ""
                        if len(p_tasks) > 0:
                            trg = p_tasks[0]
                            code_s = manager.getShortName(trg.getType(), trg.getName())
                            for i in range(len(p_tasks)-1):
                                code_s += p_tasks[i].getBranchCode( p_tasks[i+1])
                        rep_text = rep_text.replace(res, code_s)


                    else:
                        p_exist, param = task.getParam(arr[1])
                        if p_exist:
                            # print("Replace ", res, " with ", param)
                            rep_text = rep_text.replace(res, str(param))
                        else:
                            # print("No param")
                            pass
                 else:
                    #  print("No task", arr[0])
                     pass
             else:
                # print("Incorrect len")
                pass
         return rep_text

