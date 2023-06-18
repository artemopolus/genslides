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

from PIL.Image import Image
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

def updateHeight(num, img):
    print(img['image'])
    # for key, value in img:
    #     print(key, ":", value)
    print("try")
    out = img['image']
    print("sz=",out.size[0])
    (left, upper, right, lower) = (0, num, out.size[0], num + 1000)
    im_crop = out.crop((left, upper, right, lower))
    print("sz=",im_crop.size)
    return im_crop
    # return "output\\img.png"

def gr_body(request) -> None:
    manager = Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())

    projecter = Projecter(manager)


    seafoam = Seafoam()
    with gr.Blocks(theme=seafoam) as demo:

        types = [t for t in manager.helper.getNames()]

        task_man = TaskManager()

        if manager.getParam("mode") == "base":

            graph_img = gr.Image(tool="sketch", interactive=True, source="upload", type="pil")
            # graph_img = gr.ImagePaint()
            graph_img.style(height=800)
            # graph_img.style(width=1600)
            

            with gr.Row() as r:
                run_iter_btn = gr.Button(value="Run")
                update_task_btn = gr.Button(value="Update")
                h_value_txt = gr.Number(value=0, precision=0)
                gr.Button("Set height").click(fn=updateHeight, inputs=[h_value_txt, graph_img], outputs=[graph_img])
            with gr.Row() as r:
                next_task_val = gr.Textbox(value="1")
                next_task_btn = gr.Button(value="Next task, plz")
                prev_task_val = gr.Textbox(value="-1")
                prev_task_btn = gr.Button(value="Prev task, plz")
                task_list = gr.Dropdown(choices=manager.getTaskList())
                sel_task_btn = gr.Button(value="Select")
            creation_types_radio_list = ["New", "SubTask","Edit","Delete", "Select", "Link", "Unlink", "Parent", "RemoveParent"]
            for param in manager.vars_param:
                creation_types_radio_list.append(param)
                creation_types_radio_list.append("un" + param)
            # print("list=", creation_types_radio_list)
            creation_types_radio = gr.Radio(choices=creation_types_radio_list, label="Type of task creation",value="New")
            action_to_task_btn = gr.Button(value="Make action!")

            task_type_list = gr.Radio(choices = types,label="Task to create", value=types[0])
            prompt_tag_list = gr.Radio(choices=["user","assistant"], label="Tag type for prompt",info="Only for request", value="user")
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
            config_name = gr.Dropdown(choices=["mode"])
            config_values = gr.Dropdown(choices=["base", "user"])
            config_btn = gr.Button(value="update mode config").click(fn=manager.setParam, inputs=[config_name, config_values])

    demo.launch(share=False)


def main() -> None:
    prompt = "Bissness presentation for investors. My idea is automation of presentation. You just type your idea then software propose your steps to create presentation and try to automatize it."
    # prompt = "automation of presentation"

    if 1:
        print("Start gradio application")
        gr_body(prompt)
        return

    print("Start console application")


if __name__ == "__main__":
    main()
