import gradio as gr
from genslides.task.base import TaskManager
from genslides.commanager.jun import Manager
from genslides.commanager.jun import Projecter

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher


def gr_body(request) -> None:
    manager = Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())

    projecter = Projecter(manager)



    with gr.Blocks() as demo:

        types = [t for t in manager.helper.getNames()]

        task_man = TaskManager()


        graph_img = gr.Image(tool="sketch", interactive=True, source="upload", type="numpy")
        # graph_img = gr.ImagePaint()
        graph_img.style(height=800)
        

        with gr.Row() as r:
            add_new_btn = gr.Button(value="Run")
            update_task_btn = gr.Button(value="Update")
        with gr.Row() as r:
            next_task_val = gr.Textbox(value="1")
            next_task_btn = gr.Button(value="Next task, plz")
            prev_task_val = gr.Textbox(value="-1")
            prev_task_btn = gr.Button(value="Prev task, plz")
        creation_types_radio = gr.Radio(choices=["New", "SubTask","Edit","Delete", "Select", "Link", "Unlink", "Parent", "RemoveParent"], label="Type of task creation",value="New")
        cr_new_task_btn = gr.Button(value="Make action!")

        creation_var_list = gr.Radio(choices = types,label="Task to create", value=types[0])
        creation_tag_list = gr.Radio(choices=["user","assistant"], label="Tag type for prompt",info="Only for request", value="user")
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

        project_save.click(fn=projecter.save, inputs=[project_name], outputs=[projects_list])
        project_clear.click(fn=projecter.clear)
        project_load.click(fn=projecter.load, inputs=[projects_list], outputs=[project_name])

        std_output_list = [info, output, graph_img, input, creation_tag_list]
        add_new_btn.click(fn=manager.runIteration, inputs=[input], outputs=std_output_list, api_name='runIteration')
        update_task_btn.click(fn=manager.update,outputs=std_output_list, api_name="update_task_btn")
        next_task_btn.click(fn=manager.setNextTask, inputs=[next_task_val], outputs=std_output_list, api_name='next_task',)
        prev_task_btn.click(fn=manager.setNextTask, inputs=[prev_task_val], outputs=std_output_list, api_name='prev_task',)
        cr_new_task_btn.click(fn=manager.makeTaskAction, inputs=[input, creation_var_list, creation_types_radio, creation_tag_list], outputs=std_output_list, api_name="makeTaskAction")

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
