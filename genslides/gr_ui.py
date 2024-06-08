import gradio as gr
from genslides.commanager.sen import Projecter

def exttreemanagerManipulator(projecter : Projecter):
    etmgetbypath_btn = gr.Button('Browse to project')
    manpath_txt = gr.Textbox(label='Path to selected')
    tasktotargets_dtf = gr.DataFrame(headers=['ExtTreeTasks', 'Target'],type='array', col_count=2, label='Connect existed tasks to tmp man ext tasks')
    addcurrtask_btn = gr.Button('Add current task to Empty Target')
    setexttreeparam_btn = gr.Button('Set ext tree project parameters')
    exttreeparams_jsn = gr.JSON(label='Ext Tree project parameters')
    loadexttree_btn = gr.Button('Load ext tree project')
    with gr.Row():
        with gr.Column(scale=1):
            etmgraph_img = gr.Image(label='tree')
        with gr.Column(scale=3):
            etminfo_cht = gr.Chatbot(label='dial')
    with gr.Row():
        etmbudlist_drd = gr.Dropdown(label='Man bud list')
        etmbudtasks_drd = gr.Dropdown(label='Bud branch')
        trgtype_rad = gr.Radio(choices=['Current task','Compare results','Selected task'])
        etmtasksend_btn = gr.Button('Send to selected task')
        updatealltree_btn = gr.Button('Update All Trees')
