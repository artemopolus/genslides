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
    updsecact_btn = gr.Button('Update')
    act_rad = gr.Radio(label='Actioners')
    with gr.Row():
        with gr.Column(scale=1):
            etmgraph_img = gr.Image(label='tree')
        with gr.Column(scale=3):
            etminfo_cht = gr.Chatbot(label='dial')
    with gr.Column():
        man_rad = gr.Radio(label='Managers')
        tree_rad = gr.Radio(label='Trees')
    with gr.Row():
        etmbudlist_drd = gr.Dropdown(label='Man bud list')
        etmbudtasks_drd = gr.Dropdown(label='Bud branch')
        trgtype_rad = gr.Radio(choices=['Current task','Compare results','Selected task'])
        etmtasksend_btn = gr.Button('Send to selected task')
        updatealltree_btn = gr.Button('Update All Trees')

    secoutput = [
        etminfo_cht,
        etmgraph_img,
        act_rad,
        man_rad,
        tree_rad,
        etmbudlist_drd,
        etmbudtasks_drd
    ]

    updsecact_btn.click(fn=projecter.updateSecActUI,outputs=secoutput)
