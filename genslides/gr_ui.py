import gradio as gr
from genslides.commanager.sen import Projecter

def exttreemanagerManipulator(projecter : Projecter):
    etmgetbypath_btn = gr.Button('Browse to project')
    
    with gr.Row():
        with gr.Column(scale=1):
            etmgraph_img = gr.Image(label='tree')
        with gr.Column(scale=3):
            etminfo_cht = gr.Chatbot(label='dial')
    with gr.Row():
        etmbudlist_drd = gr.Dropdown(label='Man bud list')
        etmbudtasks_drd = gr.Dropdown()
        etmtasksend_btn = gr.Button('Send to selected task')
