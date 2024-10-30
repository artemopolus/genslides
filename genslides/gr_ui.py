import gradio as gr
from genslides.commanager.sen import Projecter

def exttreemanagerManipulator(projecter : Projecter):
    updsecact_btn = gr.Button('Update')
    act_rad = gr.Radio(label='Actioners')
    with gr.Row():
        with gr.Column(scale=1):
            etmgraph_img = gr.Image(label='tree')
        with gr.Column(scale=3):
            etminfo_cht = gr.Chatbot(label='dial',type='messages')
    with gr.Column():
        man_rad = gr.Radio(label='Managers')
        tree_rad = gr.Radio(label='Trees')
        etmbudlist_drd = gr.Dropdown(label='Man bud list')
        etmbudtasks_drd = gr.Dropdown(label='Bud branch')
    with gr.Row():
        trgtype_rad = gr.Radio(choices=['Current task','Compare results','Selected task'])
    with gr.Row():
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
    act_rad.input(fn=projecter.selectSecActionerByInfo, inputs=[act_rad], outputs=secoutput)
    man_rad.input(fn=projecter.selectSecActMan, inputs=[man_rad], outputs=secoutput)
    tree_rad.input(fn=projecter.selectSecActTree, inputs=[tree_rad], outputs=secoutput)
    etmbudlist_drd.input(fn=projecter.selectSecActBud,inputs=[etmbudlist_drd], outputs=secoutput)
    etmbudtasks_drd.input(fn=projecter.selectSecActTask, inputs=[etmbudtasks_drd], outputs=secoutput)

def textslider( projecter : Projecter):
    gettextwindow_btn = gr.Button('Get text window')
    windowsize_nbr = gr.Number(label='Window size', value=200,interactive=False)
    minsmbls_sld = gr.Slider(label='Upper border',value=0, minimum=0, maximum=100, step=1,interactive=False)
    windowtext_txt = gr.Markdown(label='Window')
    maxsmbls_sld = gr.Slider(label='Lower border',value=100, minimum=0, maximum=100, step=1,interactive=False)
    windowapply_btn = gr.Button('Apply text window')


    winoutput = [
        windowsize_nbr,
        minsmbls_sld,
        maxsmbls_sld,
        windowtext_txt
    ]
    gettextwindow_btn.click(fn=projecter.getTextWindowFromCurrTask, outputs=winoutput)
    minsmbls_sld.release(fn=projecter.changeTextWindowFromCurrTask, inputs=[minsmbls_sld, maxsmbls_sld], outputs=[windowtext_txt])
    maxsmbls_sld.release(fn=projecter.changeTextWindowFromCurrTask, inputs=[minsmbls_sld, maxsmbls_sld], outputs=[windowtext_txt])
    windowapply_btn.click(fn=projecter.setTextWindowToCurrTask,inputs=[minsmbls_sld,maxsmbls_sld])