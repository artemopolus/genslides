import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes
from typing import Iterable

from genslides.task.base import TaskManager
from genslides.commanager.jun import Manager
from genslides.commanager.jun import Projecter

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher

from genslides.utils.mliner import Mliner

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

            base_img = gr.Image(tool="sketch", interactive=True, source="upload", type="pil")
            base_img.style(height=800)

           

            with gr.Row() as r:
                run_iter_btn = gr.Button(value="Run")
                update_task_btn = gr.Button(value="Update")
                with gr.Column():
                    l_set_btn = gr.Button("Up")
                    h_set_btn = gr.Button("Down")
            with gr.Row() as r:
                next_task_val = gr.Textbox(value="1")
                next_task_btn = gr.Button(value="Next task, plz")
                prev_task_val = gr.Textbox(value="-1")
                prev_task_btn = gr.Button(value="Prev task, plz")
                task_list = gr.Dropdown(choices=manager.getTaskList())
                sel_task_btn = gr.Button(value="Select")

            with gr.Row():
                with gr.Column():
                    creation_types_radio_list = ["New", "SubTask","Edit","Delete", "Select", "Link", "Unlink", "Parent", "RemoveParent"]
                    for param in manager.vars_param:
                        creation_types_radio_list.append(param)
                        creation_types_radio_list.append("un" + param)
                    # print("list=", creation_types_radio_list)
                    creation_types_radio = gr.Radio(choices=creation_types_radio_list, label="Type of task creation",value="New")
                    action_to_task_btn = gr.Button(value="Make action!")

                    task_type_list = gr.Radio(choices = types,label="Task to create", value=types[0])
                    prompt_tag_list = gr.Radio(choices=["user","assistant"], label="Tag type for prompt",info="Only for request", value="user")

                graph_img = gr.Image(tool="sketch", interactive=True, source="upload", type="pil")
                graph_img.style(height=500)
 

            input = gr.Textbox(label="Input", lines=4, value=request)
            file_input = gr.File()

            # init = gr.Textbox(label="Init", lines=4)
            info = gr.Textbox(label="Info", lines=4)
            output = gr.Textbox(label="Output Box")
            # endi = gr.Textbox(label="Endi", lines=4)
            # question = gr.Textbox(label="Question", lines=4)
            # search = gr.Textbox(label="Search", lines=4)
            # userinput = gr.Textbox(label="User Input", lines=4)

            file_input.change(fn=manager.getTextFromFile, inputs=[input,file_input], outputs = [input])


            with gr.Row() as r:
                project_name = gr.Textbox(value = "Untitled", label="Project name")
                project_save = gr.Button(value="save")
                projects_list = gr.Dropdown(choices=projecter.loadList(), label="Available projects:")
                project_load = gr.Button(value = "load")
                project_clear = gr.Button(value="clear")
            dropdown = gr.Dropdown(choices=task_man.model_list, label="Available models list")
            
            # graph_img.edit(fn=manager.updateGraph, inputs=[graph_img], outputs=[graph_img])
            gr.Button("Clear mask").click(fn=manager.updateGraph, inputs = [graph_img], outputs = [graph_img])

            with gr.Row():
                x_value_txt = gr.Number(value=0, precision=0)
                y_value_txt = gr.Number(value=0, precision=0)


            h_set_btn.click(fn=moveUp, inputs=[graph_img, y_value_txt], outputs=[base_img, y_value_txt])
            l_set_btn.click(fn=moveDown, inputs=[graph_img, y_value_txt], outputs=[base_img, y_value_txt])

            # graph_img.render(fn=moveUp, inputs=[graph_img, y_value_txt], outputs=[base_img, y_value_txt],)

            sel_task_btn.click(fn=manager.setCurrentTaskByName, inputs=[task_list], outputs=[graph_img, task_list, input, prompt_tag_list, info])


            project_save.click(fn=projecter.save, inputs=[project_name], outputs=[projects_list])
            project_clear.click(fn=projecter.clear)
            project_load.click(fn=projecter.load, inputs=[projects_list], outputs=[project_name])

            std_output_list = [info, output, graph_img, input, prompt_tag_list]
            run_iter_btn.click(fn=manager.runIteration, inputs=[input], outputs=std_output_list, api_name='runIteration')
            update_task_btn.click(fn=manager.update,outputs=std_output_list, api_name="update_task_btn")
            next_task_btn.click(fn=manager.setNextTask, inputs=[next_task_val], outputs=std_output_list, api_name='next_task',)
            prev_task_btn.click(fn=manager.setNextTask, inputs=[prev_task_val], outputs=std_output_list, api_name='prev_task',)
            action_to_task_btn.click(fn=manager.makeTaskAction, inputs=[input, task_type_list, creation_types_radio, prompt_tag_list], outputs=std_output_list, api_name="makeTaskAction")
        
        elif manager.getParam("mode") == "user":
            gr.themes.Base(text_size=sizes.text_lg)
            input_txt = []
            used = manager.getFlagTaskLst()
            out = gr.Textbox(value=manager.getOutputDataSum(),label="output", interactive=False)
            for info in used:
                if info["type"] == "input":
                    interact = True
                    name = info["name"]
                    task = manager.getTaskByName(name)
                    txt = task.getInfo(short=False)
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
                project_name = gr.Textbox(value = "Untitled", label="Project name")
                projects_list = gr.Dropdown(choices=projecter.loadList(), label="Available projects:")
                project_load = gr.Button(value = "load")
            project_load.click(fn=projecter.load, inputs=[projects_list], outputs=[project_name])
            
        with gr.Row() as r:
            config_name = gr.Dropdown(choices=manager.getParamsLst())
            config_values = gr.Dropdown(choices=manager.getParam("mode lst"))
            config_btn = gr.Button(value="update mode config").click(fn=manager.setParam, inputs=[config_name, config_values])
            config_name.change(fn=manager.getParamGradioInput, inputs=[config_name], outputs=[config_values])

    demo.launch(share=False)

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
