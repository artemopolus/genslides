import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes
from typing import Iterable

from genslides.task.base import TaskManager
from genslides.commanager.jun import Manager
from genslides.commanager.sen import Projecter

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher

# from genslides.utils.mliner import Mliner

from PIL.Image import Image
import sys
import time
import json
import os

class Seafoam(Base):
    def __init__(
        self,
        *,
        primary_hue: colors.Color | str = colors.emerald,
        secondary_hue: colors.Color | str = colors.blue,
        neutral_hue: colors.Color | str = colors.gray,
        spacing_size: sizes.Size | str = sizes.spacing_md,
        radius_size: sizes.Size | str = sizes.radius_md,
        text_size: sizes.Size | str = sizes.text_lg,
        font: fonts.Font
        | str
        | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("Quicksand"),
            "ui-sans-serif",
            "sans-serif",
        ),
        font_mono: fonts.Font
        | str
        | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("IBM Plex Mono"),
            "ui-monospace",
            "monospace",
        ),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            spacing_size=spacing_size,
            radius_size=radius_size,
            text_size=text_size,
            font=font,
            font_mono=font_mono,
        )


def moveUp( img, H_pos):
    out = img['image']
    print("sz=",out.size[0])
    max_h = out.size[1]
    step = 500
    win_h = 1000

    if H_pos + step + win_h > max_h:
        H_pos = max_h - win_h
        point_m = max_h
    else:
        H_pos = H_pos + step
        point_m = H_pos + win_h
    (left, upper, right, lower) = (0, H_pos, out.size[0], point_m)
    im_crop = out.crop((left, upper, right, lower))
    return im_crop, H_pos

def moveDown( img, H_pos):
    out = img['image']
    print("sz=",out.size[0])
    max_h = out.size[1]
    step = -500
    win_h = 1000

    if H_pos + step < 0:
        H_pos = 0
        point_m = win_h
    else:
        H_pos = H_pos + step
        point_m = H_pos + win_h
    (left, upper, right, lower) = (0, H_pos, out.size[0], point_m)
    im_crop = out.crop((left, upper, right, lower))
    return im_crop, H_pos




def gr_body(request, manager : Manager, projecter : Projecter) -> None:

    seafoam = Seafoam()
    with gr.Blocks(theme=seafoam) as demo:

        types = [t for t in manager.helper.getNames()]

        task_man = TaskManager()

        if manager.getParam("mode") == "base":



            with gr.Row() as r:
                with gr.Column():
                    next_tree_btn = gr.Button(value='Next tree')
                    next_branch_btn = gr.Button(value='Next branch')
                    next_brend_bt = gr.Button(value='Next final')
                with gr.Column():
                    go_parnt_btn = gr.Button(value='Go up')
                    go_child_btn = gr.Button(value='Go down')
                with gr.Column():
                    task_list = gr.Dropdown(choices=manager.getTaskList())
                    sel_task_btn = gr.Button(value="Select")

            with gr.Row():
                with gr.Column():
                    sec_msg = gr.Chatbot(height=500)
                    with gr.Row():
                        gr.Button("Copy dial").click(fn=manager.copyToClickBoardDial)
                        gr.Button("Copy lst msg").click(fn=manager.copyToClickBoardLstMsg)
                        gr.Button("Copy tokens").click(fn=manager.copyToClickBoardTokens)
                # sec_msg.style(height=500)
                with gr.Column():
                    graph_img = gr.Image(tool="sketch", interactive=True, source="upload", type="pil", height=500)
                    with gr.Row():
                        res_step_btn = gr.Button(value='Reset Q')
                        step_task_btn = gr.Button(value="Step Q")
                        step_branch_btn = gr.Button(value='Branch Q')


                # graph_img.style(height=500)

            with gr.Row():
                with gr.Column():
                    base_action_list = gr.Radio(choices=["New","SubTask","Edit"], label="Select actions", value="New")
                    name_info = gr.Text(value="None", label="Task")
                    prompt = gr.Textbox(label="Prompt", lines=4, value=request)
                    roles_list = gr.Radio(choices=["user","assistant"], label="Tag type for prompt", value="user")
                    with gr.Row():
                        request_btn = gr.Button(value='Request')
                        response_btn = gr.Button(value='Response',interactive=False)
                        custom_list_data = projecter.getFullCmdList()
                        custom_list = gr.Dropdown(label='Custom actions', choices=custom_list_data, value=custom_list_data[0])
                        custom_btn = gr.Button(value='Custom')

                   
                    base_action_list.change(fn=manager.actionTypeChanging, inputs=base_action_list, outputs=[prompt, request_btn, response_btn, custom_btn, roles_list])
                    
                    with gr.Row():
                        with gr.Column():
                            param_type = gr.Dropdown(choices=[],label="Params")
                            param_key = gr.Dropdown(choices=[],label="Key")
                            param_type.select(fn=manager.getTaskKeys, inputs=param_type, outputs=param_key)
                            param_slcval = gr.Dropdown(choices=[],label="Value")
                            param_key.select(fn=manager.getTaskKeyValue, inputs=[param_type, param_key], outputs=[param_slcval])
                            param_mnlval = gr.Textbox(label='value',info='manual')
                        with gr.Column():
                            param_edit = gr.Button("Edit param")
                            param_opt = gr.Dropdown(choices=manager.getAppendableParam(),label='Params to append')
                            param_apnd = gr.Button('Append new')
                           
                with gr.Column():
                    with gr.Row():
                        selected_tasks_list = gr.Textbox(label='Selected:',value=','.join(manager.getSelectList()))
                        select_to_list_btn = gr.Button(value='Select').click(fn=manager.addCurrTaskToSelectList, outputs=[selected_tasks_list])
                        clear_select_list_btn = gr.Button(value='Clear Select').click(fn=manager.clearSelectList, outputs=[selected_tasks_list])
                        generate_tree_btn = gr.Button(value='Gen from Select')


                    with gr.Row():
                        moveup_btn = gr.Button(value='MoveUP')
                        parent_btn = gr.Button(value='Parent')
                        unparent_btn = gr.Button(value='Unparent')
                        link_btn = gr.Button(value='Link')
                        unlink_btn = gr.Button(value='Unlink')
                        delete_btn = gr.Button(value='Delete')
                        extract_btn = gr.Button(value='Extract')
                        copy_brnch_btn = gr.Button(value='Copy branch')
                        rm_branch_btn = gr.Button(value='Remove Branch')
                        rm_tree_btn = gr.Button(value='Remove Tree')

                   

                    parents_list = gr.Dropdown(label="Parent tasks:")
                    find_key_type = gr.Dropdown(choices=['msg','json','param','tokens','man_path','br_code'], value='msg', interactive=True)
                    with gr.Row():
                        trg_params_list = gr.Dropdown(label='List of params')
                        trg_keys_list = gr.Dropdown(label='List of keys')
                    parents_list.select(fn=manager.getByTaskNameParamList, inputs=[parents_list], outputs=[trg_params_list])
                    trg_params_list.select(fn=manager.getByTaskNameTasksKeys, inputs=[parents_list, trg_params_list], outputs=[trg_keys_list])
                    gr.Button('Copy').click(fn=manager.getFinderKeyString, inputs=[parents_list, find_key_type, trg_params_list, trg_keys_list])
 

            with gr.Row() as r:
                project_name = gr.Textbox(value = projecter.current_project_name, label="Project name")
                project_save = gr.Button(value="save")
                projects_list = gr.Dropdown(choices=projecter.loadList(), label="Available projects:")
                project_load = gr.Button(value = "load")
                project_clear = gr.Button(value="clear")

            param_info = gr.Textbox(label="Params", lines=4)
            param_updt = gr.Button(value="Edit param")

            
            creation_types_radio_list = manager.getMainCommandList()
            creation_types_radio_list += manager.getSecdCommandList()
            for param in manager.vars_param:
                creation_types_radio_list.append(param)
                creation_types_radio_list.append("un" + param)
            # print("list=", creation_types_radio_list)
            # creation_types_radio = gr.Radio(choices=creation_types_radio_list, label="Type of task creation",value="New")
            creation_types_radio = gr.Dropdown(choices=creation_types_radio_list, label="Type of task creation",value="New")
            task_type_list = gr.Dropdown(choices = types,label="Task to create", value=types[0])
            with gr.Row():
                action_to_task_btn = gr.Button(value="Make action!")
                copy_tree = gr.Button(value='Copy')

            # task_type_list = gr.Radio(choices = types,label="Task to create", value=types[0])
            prompt_tag_list = gr.Radio(choices=["user","assistant"], label="Tag type for prompt",info="Only for request", value="user")
            extpr_list = gr.Dropdown(choices=projecter.loadList(), label="Available projects:")
            with gr.Row():
                extpr_new = gr.Button(value='new')
                extpr_append = gr.Button(value='append')



            with gr.Column():
                prev_task_btn = gr.Button(value="Prev task")
                next_task_btn = gr.Button(value="Next task")
            next_task_val = gr.Textbox(value="1",label='Iteration next value')
            prev_task_val = gr.Textbox(value="-1", label='Iteration prev value')

            base_img = gr.Image(tool="sketch", interactive=True, source="upload", type="pil",height=800)
            # base_img.style(height=800)

           

            with gr.Row() as r:
                update_task_btn = gr.Button(value="Update")
                run_iter_btn = gr.Button(value="Step run")
                fix_task_btn = gr.Button(value = 'Fix Tasks')
                with gr.Column():
                    l_set_btn = gr.Button("Up")
                    h_set_btn = gr.Button("Down")
            


            fst_msg = gr.Textbox(label="Current", lines=4, value=request)
            # sec_msg = gr.Textbox(label="Previous", lines=4)
            # sec_msg = gr.HighlightedText(label="Previous", color_map={"assistant":"green"},adjacent_separator="\n",show_legend=True,combine_adjacent=True)
            # info = gr.Markdown()
            output = gr.Textbox(label="Output Box")
            # file_input.change(fn=manager.getTextFromFile, inputs=[input,file_input], outputs = [input])


            dropdown = gr.Dropdown(choices=task_man.model_list, label="Available models list")

            with gr.Column():
                with gr.Row():
                    checkbox = gr.CheckboxGroup(["test1","1111", "val"])
                with gr.Row():
                    gr.Button("Evaluate").click(fn=projecter.getEvaluetionResults, inputs=checkbox)

            
            # graph_img.edit(fn=manager.updateGraph, inputs=[graph_img], outputs=[graph_img])
            gr.Button("Clear mask").click(fn=manager.updateGraph, inputs = [graph_img], outputs = [graph_img])

            with gr.Row():
                x_value_txt = gr.Number(value=0, precision=0)
                y_value_txt = gr.Number(value=0, precision=0)


            h_set_btn.click(fn=moveUp, inputs=[graph_img, y_value_txt], outputs=[base_img, y_value_txt])
            l_set_btn.click(fn=moveDown, inputs=[graph_img, y_value_txt], outputs=[base_img, y_value_txt])

            # graph_img.render(fn=moveUp, inputs=[graph_img, y_value_txt], outputs=[base_img, y_value_txt],)
            std_output_list = [sec_msg, output, graph_img, fst_msg, prompt_tag_list, checkbox, name_info, param_info, prompt, task_list, param_type, parents_list]

            request_btn.click(fn=manager.makeRequestAction, inputs=[prompt, base_action_list, roles_list], outputs=std_output_list)
            response_btn.click(fn=manager.makeResponseAction, inputs=[base_action_list], outputs=std_output_list)
            custom_btn.click(fn=projecter.makeCustomAction, inputs=[prompt, base_action_list, custom_list], outputs=std_output_list)

            moveup_btn.click(fn=manager.moveCurrentTaskUP, outputs=std_output_list)
            parent_btn.click(fn=manager.makeActionParent, outputs=std_output_list)
            unparent_btn.click(fn=manager.makeActionUnParent, outputs=std_output_list)
            link_btn.click(fn=manager.makeActionLink, outputs=std_output_list)
            unlink_btn.click(fn=manager.makeActionUnLink, outputs=std_output_list)
            delete_btn.click(fn=manager.deleteActionTask, outputs=std_output_list)
            extract_btn.click(fn=manager.extractActionTask, outputs=std_output_list)
            copy_brnch_btn.click(fn=projecter.copyChildChains, outputs=std_output_list)
            rm_branch_btn.click(fn=manager.removeActionBranch, outputs=std_output_list)
            rm_tree_btn.click(fn=manager.removeActionTree, outputs=std_output_list)
 
            generate_tree_btn.click(fn=manager.createCollectTreeOnSelectedTasks, outputs= std_output_list)
            # copy_tree.click(fn=manager.copyChildChains, outputs=std_output_list)
            param_apnd.click(fn=manager.appendNewParamToTask, inputs=[param_opt], outputs=std_output_list)


            param_edit.click(fn=manager.setTaskKeyValue, inputs=[param_type, param_key, param_slcval, param_mnlval], outputs=std_output_list)
            extpr_new.click(fn=projecter.newExtProject, inputs=[ extpr_list, prompt], outputs=std_output_list)
            extpr_append.click(fn=projecter.appendExtProject, inputs=[ extpr_list, prompt], outputs=std_output_list)

            next_brend_bt.click(fn=manager.goToNextBranchEnd, outputs=std_output_list)
            next_branch_btn.click(fn=manager.goToNextBranch, outputs=std_output_list)
            next_tree_btn.click(fn=manager.goToNextTree, outputs=std_output_list)
            go_parnt_btn.click(fn=manager.goToParent, outputs=std_output_list)
            go_child_btn.click(fn=manager.goToNextChild, outputs=std_output_list)            

            sel_task_btn.click(fn=manager.setCurrentTaskByName, inputs=[task_list], outputs= std_output_list )


            project_save.click(fn=projecter.save, inputs=[project_name], outputs=[projects_list])
            project_clear.click(fn=projecter.clear)
            project_load.click(fn=projecter.load, inputs=[projects_list], outputs=[project_name])

            res_step_btn.click(fn=manager.resetCurTaskQueue,outputs=std_output_list)
            fix_task_btn.click(fn=manager.fixTasks, outputs=std_output_list)

            run_iter_btn.click(fn=manager.updateSteppedTree, outputs=std_output_list, api_name='runIteration')
            update_task_btn.click(fn=manager.update,outputs=std_output_list, api_name="update_task_btn")
            step_task_btn.click(fn=manager.updateSteppedSelected,outputs=std_output_list, api_name="step_task_btn")
            step_branch_btn.click(fn=manager.updateSteppedTrgBranch, outputs=std_output_list)
            next_task_btn.click(fn=manager.setNextTask, inputs=[next_task_val], outputs=std_output_list, api_name='next_task',)
            prev_task_btn.click(fn=manager.setNextTask, inputs=[prev_task_val], outputs=std_output_list, api_name='prev_task',)
            action_to_task_btn.click(fn=manager.makeTaskAction, inputs=[prompt, task_type_list, creation_types_radio, prompt_tag_list], outputs=std_output_list, api_name="makeTaskAction")
            param_updt.click(fn=manager.updateTaskParam, inputs=param_info, outputs=std_output_list, api_name="update_task_param")

        elif manager.getParam("mode") == "user":
            gr.themes.Base(text_size=sizes.text_lg)
            input_txt = []
            used = manager.getFlagTaskLst()
            # out = gr.Textbox(value=manager.getOutputDataSum(),label="output", interactive=False)
            out = gr.Markdown(value=manager.getOutputDataSum())
            
            for sec_msg in used:
                if sec_msg["type"] == "input":
                    interact = True
                    name = sec_msg["name"]
                    task = manager.getTaskByName(name)
                    txt = task.getInfo(short=False)
                    print("Get task=",task.getName())
                    if task.getType() == "SetOptions":
                        list_options = manager.getFromSetOptions(task)
                        print("List=",list_options)
                        name_task = gr.Textbox(value=task.getName(), label="Task", interactive=False)
                        with gr.Column():
                            for options in list_options:
                                opt_type = gr.Textbox(value=options["type"], label="type", interactive=False)
                                with gr.Row():
                                    for opt in options["parameters"]:
                                        opt_key = gr.Textbox(value=opt["key"], label="key", interactive=False)
                                        if opt["ui"] == "listbox":
                                            opt_val = gr.Dropdown(choices=opt["value"],label="value", interactive=True)
                                        
                                        gr.Button("change").click(fn=manager.updateSetOption, inputs=[name_task, opt_type, opt_key, opt_val])
                    else:
                        with gr.Row() as r:
                            with gr.Column(scale=4):
                                txtblck = gr.Textbox(value=txt, interactive=interact, label="Input")
                            with gr.Column(scale=1):
                                nmblck = gr.Textbox( interactive=False,value=task.getName(), label="Task name")
                            # with gr.Column(scale=1):
                                btn = gr.Button("edit").click(fn=manager.updatePromptForTask, inputs=[nmblck, txtblck], outputs=out)
                        input_txt.append(btn)
            gr.Button("update").click(fn=manager.updateAndGetOutputDataSum, outputs=out, api_name="update_task_btn")
            with gr.Row() as r:
                project_name = gr.Textbox(value = projecter.current_project_name, label="Project name")
                projects_list = gr.Dropdown(choices=projecter.loadList(), label="Available projects:")
                project_load = gr.Button(value = "load")
            project_load.click(fn=projecter.load, inputs=[projects_list], outputs=[project_name])
            
        with gr.Row() as r:
            config_name = gr.Dropdown(choices=manager.getParamsLst())
            config_values = gr.Dropdown(choices=manager.getParam("mode lst"))
            config_btn = gr.Button(value="update mode config").click(fn=manager.setParam, inputs=[config_name, config_values])
            config_name.change(fn=manager.getParamGradioInput, inputs=[config_name], outputs=[config_values])

    demo.launch(share=manager.getParam('shared'))

def test_cmd_body(manager : Manager, projecter : Projecter):
    projecter.clear()
    name = "simple_chat"
    projecter.load(name)

    init_task_json = manager.getTaskJsonStr()
    init_task_json['id'] = 'init'
    init_task_json['name'] = name


    path = "C:\\Users\\Temka\\Documents\\exactoSim\\"

    tasks = json.dumps(init_task_json)
    with open(path + "task.txt", "w") as f:
        f.write(tasks)

    path_msg = path + "msg.txt"
    if(os.path.exists(path_msg)):
        with open(path_msg,"r")as f:
            # msg = f.read()
            # print(msg)
            input_msg_json = json.load(f)
            # print(json_msg)
            res_task_json = manager.processCommand(input_msg_json, init_task_json)
            send_task_list_msg = json.dumps(res_task_json)
            with open(path + "out_msg.txt", "w") as f:
                f.write(send_task_list_msg)

    return



def mliner_body(manager : Manager, projecter : Projecter):

    projecter.clear()
    projecter.load("simple_chat")

    tasks_json = manager.getTaskJsonStr()

    path = "C:\\Users\\Temka\\Documents\\exactoSim\\"

    tasks = json.dumps(tasks_json)
    with open(path + "task.txt", "w") as f:
        f.write(tasks)



    print("Tasks=",len(tasks))
    # print("String:\n", tasks)

    short_msg = tasks[:900]


    index = 0
    mliner = Mliner()
    comm_on = True

    # mliner.upload(tasks, 7, 69)
    # mliner.upload(short_msg, 7)

    # while index < 1000:
    while True:
        # print(10*"==================")
        # if mliner.isDataSended():
        #     print("Data is sended\n")
        if mliner.isDataGetted():
            if comm_on:
                print("Data is received\n")

                # clear prev

                # projecter.clear()
                # projecter.load("simple_chat")


                init_task_json = manager.getTaskJsonStr()
                rspns = mliner.getResponse()
                if len(rspns)> 0:
                    input_msg_json = json.loads(rspns)
                    if 'id' in input_msg_json:
                        if input_msg_json['id'] == 7:
                            res_task_json = manager.processCommand(input_msg_json, init_task_json)
                            send_task_list_msg = json.dumps(res_task_json)
                            mliner.upload(send_task_list_msg, 7, 7)
                        elif input_msg_json['id'] == 11:
                            res_task_json = manager.syncCommand(init_task_json)
                            send_task_list_msg = json.dumps(res_task_json)
                            mliner.upload(send_task_list_msg, 7, 11)
                        elif input_msg_json['id'] == 17:
                            if 'options' in input_msg_json and 'action' in input_msg_json['options']:
                                action_type = input_msg_json['options']['action']
                                if action_type == 'load':
                                    projecter.load(input_msg_json['options']['name'])
                                elif action_type == 'save':
                                    projecter.save(input_msg_json['options']['name'])
                                elif action_type == 'clear':
                                    projecter.clear()
                                # res_tasks_json = manager.getTaskJsonStr()
                                # res_tasks_json['id'] = 'prjt'
                                res_tasks_json = projecter.getTaskJsonStr('prjt')

                                res_tasks = json.dumps(res_tasks_json)
                                mliner.upload(res_tasks, 7, 17)
 
            # with open(path + "msg.txt", "w") as f:
                # f.write(mliner.getResponse())

        # print(10*"==================")

       
        mliner.update()
        index += 1
        # print("index=", index)
        time.sleep(0.25)

    mliner.close()



def main() -> None:
    prompt = "Bissness presentation for investors. My idea is automation of presentation. You just type your idea then software propose your steps to create presentation and try to automatize it."
    # prompt = "automation of presentation"
    manager = Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())

    projecter = Projecter(manager)

    mode = manager.getParam("app type")

    if mode == "gradio":
        print("Start gradio application")
        gr_body(prompt, manager, projecter)
    elif mode == "mliner":
        print("Start console application")
        mliner_body(manager, projecter)
    elif mode == "test":
        print("Start console application")
        test_cmd_body(manager, projecter)
    else:
        print("Unknown app type = ", mode)

    print("End of main")


    del manager, projecter


if __name__ == "__main__":
    main()
    print("Done")
    sys.exc_info()
