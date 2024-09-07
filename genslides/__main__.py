import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes
from typing import Iterable

from genslides.task.base import TaskManager
# from genslides.commanager.jun import Manager
import genslides.commanager.group as Actioner

from genslides.commanager.sen import Projecter

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher
import genslides.gr_ui as UI
# from genslides.utils.mliner import Mliner

from PIL.Image import Image
import sys
import time
import json
import os
import genslides.utils.finder as finder
import argparse

# [[---]]

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




# [[---]]
def gr_body(request, manager : Actioner.Manager.Manager, projecter : Projecter, project_params) -> None:

    seafoam = Seafoam()
    with gr.Blocks(theme=seafoam) as demo:

        types = [t for t in manager.helper.getNames()]

        task_man = TaskManager()

        if manager.getParam("mode") == "base":


            project_manipulator = projecter
            userinput_manager = projecter
            manipulate_manager = projecter
            parameters_manager = projecter
            with gr.Accordion(label='session'):
                with gr.Row():
                    sessionname_drd = gr.Dropdown(label='Session names list',choices=projecter.getSessionNameList())
                    setsessionname_btn = gr.Button('Select from list')
                    sessionnamecur_txt = gr.Textbox(label='Session name',lines=1,value=projecter.getCurrentSessionName())
                    newsessionname_btn = gr.Button('New name for session')
                # with gr.Row():
                    # project_manLoad = gr.Button(value='Default project location')
                    # project_manBrow = gr.Button(value='Select project location')
                with gr.Column():
                    actaddbybrow_btn = gr.Button('Load actioner from location')
                    actionerlist_rad = gr.Radio(label='Actioners')
                    updactlist_btn = gr.Button('Update')
                    updactlist_btn.click(fn=projecter.getActionerList, outputs=[actionerlist_rad])
                with gr.Row():
                    exttreetaskaddact_btn = gr.Button('Load ExtTree to actioner')



            with gr.Row() as r:
                tree_names_radio = gr.Radio(label='Trees:')
            with gr.Row() as r:
                new_tree_name_txt = gr.Textbox(label='Current tree label:')

            with gr.Row() as r:
                # with gr.Column(min_width=150):
                    new_tree_btn = gr.Button(value='Create tree', min_width=150)
                    next_tree_btn = gr.Button(value='Next tree', min_width=150)
                # with gr.Column():
            # with gr.Row() as r:
                # with gr.Column():
            with gr.Row():
                status_txt = gr.Textbox(label='Status')
                    
            with gr.Accordion(label='Buds', open=False):
                with gr.Row():
                        end_names_radio = gr.Radio(label='Buds:')
                with gr.Row():
                        end_name_text = gr.Textbox(label='Current bud:')
            with gr.Row():
                next_branch_btn = gr.Button(value='Next branch', min_width=150)
                prev_branch_btn = gr.Button(value='Prev branch', min_width=150)
                next_brend_bt = gr.Button(value='Next bud', min_width=150)
                go_parnt_btn = gr.Button(value='Go up')
                go_child_btn = gr.Button(value='Go down')

            with gr.Tab('Workspace'):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            name_info = gr.Text(value="None", label="Task")
                        with gr.Row():
                            graph_img = gr.Image(
                            # tool="sketch", 
                            # interactive=True, 
                            # source="upload", type="pil", 
                            # height=700
                            )
                    with gr.Column(scale=3):
                        with gr.Row():
                            go_lnkback_btn = gr.Button(value='Go BackLnk')
                            go_lnkfrwd_rad = gr.Radio(label='Targets')
                            go_lnkfrwd_btn = gr.Button(value='Go FrwdLnk')
                            go_hlfbrch_btn = gr.Button(value='Go to MidBranch')
                            go_brchfrk_btn = gr.Button(value='Go to fork')
                            go_taskbud_btn = gr.Button(value='Go to Task Bud')

                        with gr.Row():
                            viewhiddenmsgs_chck = gr.Checkbox(label='Hide task(s)', value=True)
                        with gr.Row():
                            sec_msg = gr.Chatbot(height=700)
                    # sec_msg.style(height=500)
                # graph_img.style(height=500)
            with gr.Tab('Step navigation'):
                with gr.Row():
                    with gr.Column(scale=1):
                        graph_alone = gr.Image(
                            # width=500
                        )
                    with gr.Column(scale=3):
                        with gr.Row():
                            updateall_step_btn = gr.Button(value="Update all trees(UAT)")
                            update_step_btn = gr.Button(value="UAT one step")
                            upd2cur_step_btn = gr.Button(value='UAT to cur')
                            updbrnc_step_btn = gr.Button(value='Update Tree + Linked')
                            updateforktasks_btn = gr.Button('UAT fork')
                        with gr.Accordion("Additional",open=False):
                            with gr.Row():
                                updateall_stepNs_sld = gr.Slider(label='UAT N times',value=0,minimum=0, maximum=50,step=1)
                                updateall_stepNs_btn = gr.Button('UAT N times')
                            with gr.Row():
                                clnresp_btn = gr.Button(value='Clean Response')
                            with gr.Row():
                                updatecheckown_chk = gr.Checkbox(label='Check tasks manager', value=False)
                                reset_step_btn = gr.Button(value="Reset steps")
                                updatechildtasks_btn = gr.Button('UAT childs')
                                updatemultitasks_btn = gr.Button('UAT multi')
                                updatecntreset_btn = gr.Button('reset UAT cnt')
 
                            # move2brnch_btn = gr.Button(value='Move to next branch', min_width=150)
                            # move2parnt_btn = gr.Button(value='Go up')
                            # move2child_btn = gr.Button(value='Go down')
                            with gr.Column():
                                getinexttreetasks_btn = gr.Button('Get InExtTree Task(s)')
                                inexttretasklist_chk = gr.CheckboxGroup(label='InExtTree Task(s)')
                                updselinexttreetasks_btn = gr.Button('Update selected')
                                getinexttreetasks_btn.click(fn=projecter.getCurManInExtTreeTasks, outputs=[inexttretasklist_chk])
                with gr.Row():
                    dial_block = gr.Chatbot(height=800)

            with gr.Tab('Raw graph'):
                with gr.Row():
                    # with gr.Column(scale=1):
                        raw_graph = gr.Image(
                            # width=500
                            # height=800
                        )
                    # with gr.Column(scale=1):
            with gr.Tab('Raw dial'):
                with gr.Row():
                            raw_dial = gr.Chatbot(height=500)
                with gr.Row():
                            task_list = gr.Dropdown(choices=manager.getTaskList(), label='Available tasks')
                            sel_task_btn = gr.Button(value="Select")
                with gr.Row():
                            trgtexttosearch_txt = gr.Textbox(label='Text to search')
                            foundtaskstext_txt = gr.Textbox(label='Search results')
                            findtextintasks_btn = gr.Button('Find')
                            findtextintasks_btn.click(fn=projecter.findSubStringInTasks, inputs=[trgtexttosearch_txt], outputs=[foundtaskstext_txt])
            with gr.Tab('Comparing'):
                with gr.Row():
                    comparison_rad = gr.Radio(choices=projecter.getComparisonTypes())
                with gr.Row():
                    comparison_btn = gr.Button('Compare')
                with gr.Row():
                    fullchatrecords_btn = gr.Button('Get full chat')
                    fullchatrecords_sld = gr.Slider(interactive=True)
                with gr.Row():
                    rowchatrecords_btn = gr.Button('Get chat row')
                    rowchatrecords_sld = gr.Slider(interactive=True)
                with gr.Row():
                    infochatrecords_txt = gr.Textbox()
                with gr.Row():
                    infochatrecords_btn = gr.Button('Update')
                with gr.Row():
                    comparison_chat = gr.Chatbot(height=500, label='Comparison chat')
                with gr.Column():
                    headercontent_txt = gr.Textbox(label='Header',lines=4)
                    prefixcontent_txt = gr.Textbox(label='Prefix',lines=4)
                    suffixcontent_txt = gr.Textbox(label='Suffix',lines=4)
                    conclcontent_txt = gr.Textbox(label='PS',lines=4)

                    resultmsg_btn = gr.Button('Create Message')
                    resultmsg_txt = gr.Textbox(label='Result Message', lines=8)

                    resultmsg_btn.click(fn=projecter.createMessageBasedOnRecords, inputs=[
                                    comparison_chat,
                                    headercontent_txt,
                                    prefixcontent_txt,
                                    suffixcontent_txt,
                                    conclcontent_txt
                                        ], outputs=[resultmsg_txt]
                    )


                fullchatrecords_btn.click(fn=projecter.getCopyBranch, inputs = [fullchatrecords_sld], 
                                          outputs=[comparison_chat, infochatrecords_txt, fullchatrecords_sld, rowchatrecords_sld])
                rowchatrecords_btn.click(fn=projecter.getCopyBranchRow, inputs = [rowchatrecords_sld], 
                                          outputs=[comparison_chat, infochatrecords_txt, fullchatrecords_sld, rowchatrecords_sld])
                infochatrecords_btn.click(fn=projecter.getCopyBranchesInfo, outputs=[infochatrecords_txt, fullchatrecords_sld, rowchatrecords_sld])
                comparison_btn.click(fn=projecter.getBudMsgs, inputs=comparison_rad, outputs=comparison_chat)
            with gr.Tab('Plain Text'):
                with gr.Row():
                    treeplaintexttype_rad = gr.Radio(choices=['Tree','Current Task Tree', 'MultiSelected'])
                    updateplaintext_btn = gr.Button('Update')
                with gr.Row():
                    pretext_txt = gr.Textbox()
                with gr.Row():
                    moveupplaintext_btn = gr.Button('Up')
                with gr.Row():
                    curtext_txt = gr.Textbox(label='Current task', lines=4)
                with gr.Row():
                    saveplaintextcontent_btn = gr.Button('Save edits')
                    movedwplaintext_btn = gr.Button('Down')
                with gr.Row():
                    afttext_txt = gr.Textbox()
                plaintext_output = [pretext_txt, curtext_txt, afttext_txt]
                updateplaintext_btn.click(fn=projecter.getConvertTreeTo3PlainText, inputs=[treeplaintexttype_rad], outputs=plaintext_output)
                moveupplaintext_btn.click(fn=projecter.moveUpTree3PlainText, outputs=plaintext_output)
                movedwplaintext_btn.click(fn=projecter.moveDwTree3PlainText, outputs=plaintext_output)
                saveplaintextcontent_btn.click(fn=projecter.editPromptTree3PlainText, inputs=[curtext_txt], outputs=plaintext_output)
            with gr.Tab('Attention window'):
                with gr.Column():
                    UI.textslider(projecter)
            
            with gr.Accordion('Tools', open=False):
                
                tmp_code_txt = gr.Textbox(label="KeyCode", value="None", show_copy_button=True, lines=1)
                tmp_content_txt = gr.Textbox(  value="None", show_copy_button=True, lines=3, max_lines=5)
                # with gr.Row():
                    # gr.Button("Copy raw dial").click(fn=projecter.copyToClickBoardDialRaw)
                    # gr.Button("Copy raw reqs").click(fn=projecter.copyToClickBoardReqListRaw)
                    # gr.Button("Copy tokens").click(fn=projecter.copyToClickBoardTokens)
                    # gr.Button("Cp branch code").click(fn=projecter.getCurrentTaskBranchCodeTag)
                with gr.Column():
                    gr.Button("Copy dial").click(fn=projecter.copyToClickBoardDial, outputs=[tmp_code_txt, tmp_content_txt])
                    gr.Button("Copy lst msg").click(fn=projecter.copyToClickBoardLstMsg, outputs=[tmp_code_txt, tmp_content_txt])
                    # gr.Button("[ [parent:msg_content] ]").click(fn=projecter.copyToClickBoardParentContent)
                    gr.Button("[ [parent:msg_content:json:answer] ]").click(fn=projecter.copyToClickBoardParentContentJSONtrg, outputs=[tmp_code_txt, tmp_content_txt])
                    gr.Button("[ [parent:code] ]").click(fn=projecter.copyToClickBoardParentCode, outputs=[tmp_code_txt, tmp_content_txt])
                    gr.Button("paths").click(fn=projecter.copyToClickBoardPaths, outputs=[tmp_code_txt, tmp_content_txt])
 
            with gr.Row():
                # with gr.Column():
                    with gr.Tab('Prompt'):
                        with gr.Row():
                            with gr.Column(scale=1,min_width=150):
                                base_action_list = gr.Radio(choices=["New","SubTask","Insert","Edit"], 
                                                            label="Select actions", 
                                                            value="New"
                                                            )
                                roles_list = gr.Radio(choices=["user","assistant","system"], label="Tag type for prompt", value="user", interactive=False)
                                vizprompt_list = gr.Radio(choices=["None","markdown","python","json"], label="Visualization", value="None", interactive=True)
                            with gr.Column(scale = 19):
                                prompt = gr.Textbox(label="Prompt", lines=4, value=request)
                                with gr.Row():
                                    request_btn = gr.Button(value='Request')
                                    response_btn = gr.Button(value='Response',interactive=False)
                                    custom_list_data = projecter.getFullCmdList()
                                    custom_list = gr.Dropdown(label='Custom actions', choices=custom_list_data, value=custom_list_data[0])
                                    custom_btn = gr.Button(value='Custom')
                                with gr.Row():
                                    extcopy_chck = gr.CheckboxGroup(label='Edit task parameters')
                        with gr.Row():
                            oldtexttochange_txt = gr.Textbox(label='Old text to change')
                            newtexttochange_txt = gr.Textbox(label='New text for replacing')
                            changeoldtonew_btn = gr.Button('Change for multi')
                        with gr.Row():
                            shiftpartag_sld = gr.Slider(label='Shift value for par tag', minimum=-20, maximum=20, step=1, value=1)
                        with gr.Row():
                            childshiftpartag_btn = gr.Button('Shift par tag for cur&child')
                            multishiftpartag_btn = gr.Button('Shift par tag for multisel')

                        
                   
                    base_action_list.change(fn=projecter.actionTypeChanging, inputs=[base_action_list,  vizprompt_list], outputs=[prompt, request_btn, response_btn, custom_btn, roles_list,extcopy_chck])
                    vizprompt_list.change(fn=projecter.changeVizType, inputs=[base_action_list,  vizprompt_list], outputs=prompt)
                    with gr.Tab('Params'):
                        with gr.Row():
                            with gr.Column():
                                with gr.Row():
                                    with gr.Column(scale=4):
                                        param_type = gr.Dropdown(choices=[],label="Params")
                                    with gr.Column(scale=1):
                                        param_rmve = gr.Button('Remove')
                                with gr.Row():
                                    with gr.Column(scale=4):
                                        param_opt = gr.Dropdown(choices=projecter.getAppendableParam(),label='Params to append')
                                    with gr.Column(scale=1):
                                        param_apnd = gr.Button('Append new')
                                # param_info = gr.Textbox(label="Params", lines=10, max_lines=20)
                                param_info = gr.JSON(label="Params")
                            with gr.Column():
                                param_key = gr.Dropdown(choices=[],label="Key")
                                param_type.select(fn=projecter.getTaskKeys, inputs=param_type, outputs=param_key)
                                param_slcval = gr.Dropdown(choices=[],label="Options")
                                paramslctset_btn = gr.Button('Set option to value')
                                param_mnlval = gr.Textbox(label='Value',info='manual',lines=4, interactive=True)
                                param_edit = gr.Button("Edit param")

                                paramslctset_btn.click(fn=projecter.setSelectOptionToValue, inputs=[param_type, param_key,param_slcval], outputs=[param_mnlval])

                                addkey_key_txt = gr.Textbox(label='New key to add')
                                addkey_val_txt = gr.Textbox(label='New key value')
                                addkey_apd_btn = gr.Button('Add new key, value')
                                param_key.select(fn=projecter.getTaskKeyValue, inputs=[param_type, param_key], outputs=[param_slcval, param_mnlval])
                                setrecords_btn = gr.Button('Set recording') 
                                clrrecords_btn = gr.Button('Clear records')
                                with gr.Row():
                                    savemanact2currtask_drd = gr.Dropdown(choices=projecter.getFullCmdList(True), interactive=True)
                                    savemanact2currtask_btn = gr.Button('Save actions to task')
                    with gr.Tab('Select'):
                        with gr.Row():
                            selected_tasks_list = gr.Textbox(label='Selected:',value=','.join(manager.getSelectList()))
                            select_to_list_btn = gr.Button(value='Select')
                            relink_sel2cur_btn = gr.Button(value='Relink Sel to Cur')
                            clear_select_list_btn = gr.Button(value='Clear Select').click(fn=manager.clearSelectList, outputs=[selected_tasks_list])
                        with gr.Row():
                            parent_btn = gr.Button(value='Parent')
                            link_btn = gr.Button(value='Link')
                            child_btn = gr.Button(value='Child')
                            revlink_btn = gr.Button(value='Revert Link')
                        with gr.Row():
                            slct_action_list = gr.Radio(choices=["New","SubTask","Insert"], 
                                                            label="Select actions", 
                                                            value="New"
                                                            )
                        with gr.Row():
                            collect_btn = gr.Button(value='Collect')
                            shoot_btn = gr.Button(value='Shoot')
                            garland_btn = gr.Button(value='Garland')
                        with gr.Row():
                            selected_prompt = gr.Textbox(value='',lines=4, label='Selected prompt')
                        select_to_list_btn.click(fn=projecter.addCurrTaskToSelectList, outputs=[selected_tasks_list, selected_prompt])
                    with gr.Tab('MultiSelect'):
                        with gr.Row():
                            multiselecttask_txt = gr.Textbox(label='Multiselected tasks:')
                        with gr.Row():
                            addtask2reltask_btn = gr.Button('Add task')
                            addpart2reltask_btn = gr.Button('Add brpart')
                            addbrch2reltask_btn = gr.Button('Add branch')
                            addchds2reltask_btn = gr.Button('Add childs')
                            addtree2reltask_btn = gr.Button('Add tree')
                        with gr.Row():
                            relatedtask_btn = gr.Button('Relationship chain')
                            nearesttask_btn = gr.Button('Nearest tasks')
                            get_hold_garland_btn = gr.Button('Get Garland Holders')
                        with gr.Row():
                            relatedfwrdchain_btn = gr.Button('Forward relation')
                            relatedfwrdchain_sld = gr.Slider(minimum=0, maximum=20,step=1,value=1,label='Range')
                        with gr.Row():
                            relatedbackchain_btn = gr.Button('Back relation')
                            relatedbackchain_sld = gr.Slider(minimum=0, maximum=20,step=1,value=1,label='Range')
                        with gr.Row():
                            rmvtask2reltask_btn = gr.Button('Rmv task')
                            rmvpart2reltask_btn = gr.Button('Rmv brpart')
                            rmvbrch2reltask_btn = gr.Button('Rmv branch')
                            rmvchds2reltask_btn = gr.Button('Rmv childs')
                            rmvtree2reltask_btn = gr.Button('Rmv tree')
                            rmvprns2reltask_btn = gr.Button('Rmv parents')
                        with gr.Row():
                            addrow2reltask_btn = gr.Button('Select row')
                            addcurrtaskrow2reltask_btn = gr.Button('Select row by range')
                            addcurrtaskrow2reltask_sld = gr.Slider(minimum=0, maximum=20,step=1,value=1,label='range to row')
                        with gr.Row():
                            addcpbranch2reltask_btn = gr.Button('Select copy Branch')
                            addcptasks2reltask_btn = gr.Button('Select copy Task')
                        with gr.Row():
                            relattaskcln_btn = gr.Button('Clear all')
                        with gr.Row():
                            with gr.Column():
                                parammultikey_dd = gr.Dropdown(choices=projecter.getAppendableParam(),label='Param keys')
                                getparamamulti_btn = gr.Button('Get params from multi')
                                parammulti_json = gr.Textbox(label='Parameters', interactive=True)
                                parammultilog_txt = gr.Textbox(label='log')
                                gr.Button(value='Update param struct').click(fn=projecter.setParamStructToMultiSelect, 
                                                                             inputs=[parammulti_json, parammultikey_dd], 
                                                                             outputs=[parammulti_json, parammultilog_txt])

                                getparamamulti_btn.click(fn=projecter.getParamFromMultiSelected, 
                                                         inputs=parammultikey_dd, 
                                                         outputs=[parammulti_json, parammultilog_txt])
                            with gr.Column():
                                delete_reltasks_btn = gr.Button('Delete multiselected')
                                set_multi_child_btn = gr.Button('Set Multiselected as Child')
                                garlandmulti_btn = gr.Button('Garland from multi')
                                collectmulti_btn = gr.Button('Collect from multi')
                                gr.Button('Check').click(fn=projecter.checkTaskFiles)
                                minichainstobig_btn = gr.Button('Mini chains to ONE')
                                disunselectchild_btn = gr.Button('Disable unselected children from queue')
                                enablemultichilds_btn = gr.Button('Enable children to queue')
                                selectactioner_btn = gr.Button('Select Multiselected Task Act')
                                copymultiselecttask_btn = gr.Button('Mov here Act Multi Task', interactive=False)

                                applyautocmdtomulti_btn = gr.Button('Apply AutoCmd to Multi')
                                selectactioner_btn.click(fn=projecter.selectTargetActioner, outputs=[copymultiselecttask_btn])
                                copymultiselecttask_btn.click(fn=projecter.moveMultiSelectedTasksFromTargetActioner, outputs=[copymultiselecttask_btn])


                                with gr.Row():
                                    savemultitasks_txt = gr.Textbox()
                                    savemultitasks_btn = gr.Button('Save multi to folder').click(fn=projecter.copyMultiSelectToFolder, outputs=[savemultitasks_txt])


                    with gr.Tab('Cmds'):
                        with gr.Row():
                            moveup_btn = gr.Button(value='MoveUP')
                            switchup_btn = gr.Button(value='SwitchUP')
                            reparup_btn = gr.Button(value='ReparentUP')
                            unparent_btn = gr.Button(value='Unparent')
                            unlink_btn = gr.Button(value='Unlink')
                            delete_btn = gr.Button(value='Delete')
                            extract_btn = gr.Button(value='Extract')
                            unite_btn = gr.Button(value='Unite')
                            rm_branch_btn = gr.Button(value='Remove Branch')
                            rm_tree_btn = gr.Button(value='Remove Tree')
                            copy_chain_btn = gr.Button(value='Copy ch step')
                            update_task_btn = gr.Button(value="Update")
                            updatecur_task_btn = gr.Button(value='Update current')
                            clean_task_btn = gr.Button(value='Clean')
                    with gr.Tab('Arrange'):
                        with gr.Row():
                            with gr.Column():
                                branches_data = gr.Highlightedtext(label="Branches",
                                        combine_adjacent=True,
                                        # show_legend=True,
                                        color_map={
                                            "common": "gray", 
                                            "target": "green"
                                            })
                            with gr.Column():
                                    # gr.Button(value='Update').click(fn= projecter.getBranchList, outputs=[branches_data])
                                    moveupprio_btn = gr.Button(value='MoveUpPrio')
                                    movedwprio_btn = gr.Button(value='MoveDwPrio')
                            with gr.Column():
                                trees_data = gr.Highlightedtext(label="Trees",
                                        combine_adjacent=True,
                                        # show_legend=True,
                                        color_map={
                                            "common": "gray", 
                                            "target": "green"
                                            })
                            with gr.Column():
                                # gr.Button(value='Update').click(fn= projecter.getTreesList, outputs=[trees_data])
                                moveuptree_btn = gr.Button(value='Up')
                                movedwtree_btn = gr.Button(value='Dw')
                        with gr.Row():
                            # branch_msgs = gr.Highlightedtext(label="Trees",
                            #             combine_adjacent=True,
                            #             show_legend=True,
                            #             color_map={
                            #                 "common": "gray", 
                            #                 "target": "green"
                            #                 })
                            branch_msgs = gr.Markdown()
                            # gr.Button('Update').click(fn=projecter.getBranchMessages, outputs=[branch_msgs])

                            
                    with gr.Tab('Manager'):
                        with gr.Row():
                            with gr.Tab('List'):
                                with gr.Row():
                                    # get_tempman = gr.Dropdown(label='Temp managers', interactive=True)
                                    get_tempman = gr.Radio(label='Managers list')
                                with gr.Row():
                                    tmpmanname_txt = gr.Textbox(label='Current manager name')
                                with gr.Row():
                                    tmpman_clrpck = gr.ColorPicker()
                                    load_tempman_btn = gr.Button(value='Set man tasks color').click(fn=projecter.setCurManagerColor, 
                                                                                          inputs=[tmpman_clrpck])
                                with gr.Row():
                                    updt_prman_btn = gr.Button(value='Updt managers list')
                                with gr.Row():
                                    gr.Button('Save Cur Tmp man info files').click(fn=projecter.saveCurrManInfo)
                                    gr.Button('Save Cur Tmp Man to location').click(fn=projecter.saveTmpMan)
                            with gr.Tab('Create'):
                                with gr.Row():
                                    name_prman = gr.Text(value='None', label = 'Manager')
                                with gr.Column():
                                    with gr.Row():
                                        initmannname_rad = gr.Radio(label='Manager name', choices=['Current', 'Selected','1st MultiS','Custom'],value='Current')
                                        custominitname_txt = gr.Textbox(label='Custom name', lines=1)
                                    manextntasklist_rad = gr.Radio(label='ExtTask for init', choices=['Current','Selected','Multis'], value='Current')
                                    mancopytasklist_rad = gr.Radio(label='Move tasks in init', choices=['Multis','None'], value='None')
                                    getinittmpmaninfo_btn = gr.Button('Get init man info')
                                    inittmpmaninfo_jsn = gr.JSON()
                                    init_prman_btn = gr.Button(value='Init manager from MultiTasks', interactive=False)

                                    getinittmpmaninfo_btn.click(fn=projecter.getPrivMangerDefaultInfo,
                                         inputs=[initmannname_rad, custominitname_txt, manextntasklist_rad, mancopytasklist_rad], 
                                         outputs=[
                                        inittmpmaninfo_jsn,
                                        init_prman_btn
                                    ])
                            with gr.Tab('Remove'):
                                rset_prman_btn = gr.Button(value='Remove manager')
                                stop_prman_btn = gr.Button(value='RM man & Save tasks to BASE')
                            with gr.Tab('MultiSelect'):
                                # with gr.Row():
                                    # gr.Label(value='Multiselect tasks (MST) action')
                                gr.Textbox("std -- Base Manager\ntmp -- Temporary Manager\nMST -- Multiselected task of manager",lines=3)
                                with gr.Column():
                                    addmultitotmp_btn = gr.Button(value='Add links of Base multiselected to Tmp Manager')
                                    rmvmultifrtmp_btn = gr.Button(value='Rmv links from Tmp Manager')
                                    movemulti2std_btn = gr.Button(value='Move Tmp Manager Multiselected tasks to Base')
                                    movemulti2tmp_btn = gr.Button(value='Move Base Multiselected tasks to Tmp Manager')
                                with gr.Row():
                                    tempman_drp = gr.Dropdown(label='Selected Manager')
                                    movetmp2tmp_btn = gr.Button('Move curman->selman')
                            with gr.Tab('Files management'):
                                with gr.Row():
                                    copycurmantaskstofolder_btn = gr.Button('Copy tasks in another folder')
                                with gr.Row():
                                    settmpmanagertasks_btn = gr.Button('Get Tmp Manager Folder')
                                with gr.Row():
                                    newtmpmanname_txt = gr.Textbox(label='Tmp Manager Name')
                                with gr.Row():
                                    pathtotrgtmpman_txt = gr.Textbox(label='Path to tmp manager folder')
                                with gr.Row():
                                    multiselectedlistcurman_txt = gr.Textbox(label="Tasks of current manager")
                                with gr.Row():
                                    tmpmanagerexttasks_dtf = gr.DataFrame(headers=['External', 'Target'],type='array', col_count=2)
                                with gr.Row():
                                    addextmantasksintocurman = gr.Button('Copy & change tasks in cur tmp man')
                                
                                loadtaskintomanbrow_btn = gr.Button('Load task into manager from browser')
                                copycurmantaskstofolder_btn.click(fn=projecter.copyManagerTaskFilesToAnotherFolder)
                                settmpmanagertasks_btn.click(fn=projecter.loadTmpManagerInfoForCopying, 
                                                             outputs=[
                                                                 tmpmanagerexttasks_dtf,
                                                                 multiselectedlistcurman_txt,
                                                                 pathtotrgtmpman_txt
                                                                 ])

                            with gr.Tab('Other'):
                                with gr.Row():
                                    get_savdman_btn = gr.Dropdown(label='Saved managers', interactive=True)
                                with gr.Row():
                                    load_prman_btn = gr.Button(value='Load to trgtask')
                                    exe_act2cur_btn = gr.Button(value='Load to curtask')
                                with gr.Row():
                                    actpack_name_txt = gr.Textbox(value='',label='Act pack name', lines=1)
                                    actpack_save_btn = gr.Button(value='Save actpack')
                                with gr.Row():
                                    actpack_saved_lst = gr.Dropdown(label='Saved actpacks', choices=projecter.getActPacksList())
                                    actpack_load_btn = gr.Button(value='Load actpack2man')
                                    actpack_save_btn.click(fn=projecter.saveActPack, inputs=[actpack_name_txt], outputs=actpack_saved_lst)
                                with gr.Row():
                                    save2curtask_btn = gr.Button(value='Save man2task')
                                # with gr.Row():
                                    # clr_prman_btn = gr.Button('Clear vals')
                                # with gr.Row():
                                    # params_prman = gr.Textbox(label="Params", lines=4, max_lines=20)
                                # with gr.Row():
                                    # edit_param_prman = gr.Button(value='Edit param managers')
                                # with gr.Row():
                                    # setname_prman_text = gr.Button('Back')
                                    # setname_prman_btn = gr.Button('Set name')
                                    # exttaskopt_chgr = gr.CheckboxGroup()
                        # with gr.Tab("Actions"):
                            with gr.Tab('Actions'):
                                actions_list = gr.CheckboxGroup(label='Action list')
                                actpack_load_btn.click(fn=projecter.loadActPack, inputs=[actpack_saved_lst], outputs=[actions_list])
                                with gr.Row():
                                    gr.Button('Update').click(fn=projecter.getActionsList, outputs=actions_list)
                                    gr.Button('Move').click(fn=projecter.moveActionUp, inputs=actions_list, outputs=actions_list)
                                    gr.Button('Delete').click(fn=projecter.delAction, inputs=actions_list, outputs=actions_list)
                                    gr.Button('Save').click(fn=projecter.saveAction, outputs=actions_list)
                                with gr.Row():
                                    exe_act_btn = gr.Button(value='Execute action')
                                actions_info_txt = gr.Textbox(lines=4)
                                actions_list_toadd = gr.Dropdown(choices=projecter.getAvailableActionsList())
                                action_param = gr.Textbox(lines = 4, interactive=True)
                                actions_list_toadd.select(fn=projecter.getAvailableActionTemplate,inputs=actions_list_toadd, outputs=action_param)
                                gr.Button('Save action').click(fn=projecter.addActionToCurrentManager, inputs=[actions_list_toadd, action_param], outputs=actions_list)
                                actions_list.change(fn=projecter.getActionInfo, inputs=actions_list, outputs=actions_info_txt)
                    with gr.Tab('ExtProject'):
                        with gr.Tab('Create'):
                            with gr.Row():
                                convbranch2inoutext_btn = gr.Button('Convert muliselect tasks in InOutExtTree Tasks')
                            with gr.Row():
                                manextinfocurtask_btn = gr.Button('Get cur task tmp manager info')
                                manextinfobrowse_btn = gr.Button('Browse info from tmp manager')
                            with gr.Row():
                                with gr.Column():
                                    with gr.Row():
                                        mantsklist_drd = gr.Dropdown(label='External Tasks of Loaded Tmp Manager')
                                        mantsklist_btn = gr.Button('Select')
                                    with gr.Row():
                                        exttargettask_drd = gr.Dropdown(label='Available Targets in Current Manager')
                                with gr.Column():
                                    with gr.Row():
                                        inexttreeparam_txt = gr.Textbox(label='InExtTree Task Parameters',lines=5)
                                    with gr.Row():
                                        inextreesubtask_btn = gr.Button('InExtTree SubTask')
                            with gr.Accordion(visible=False):
                                with gr.Row():
                                    with gr.Column():
                                        manbudlist_drd = gr.Radio(label='Buds:')
                                        with gr.Row():
                                            inet_extmanbud_btn = gr.Button('Set for In')
                                            outet_extmanbud_btn = gr.Button('Set for Out')
                                        manbudsum_txt = gr.Textbox(label='Summary')
                                        manbudindo_txt = gr.Textbox(label='BranchCode')
                                        manalltsklist_drd = gr.Dropdown(label='Project Tasks')
                                        with gr.Row():
                                            inet_extmantasks_btn = gr.Button('Set for In')
                                            outet_extmantasks_btn = gr.Button('Set for Out')
                                    with gr.Column():
                                        manbudlist_cht = gr.Chatbot()
                                    # manbudinfoupdt_btn.click(fn=projecter.getBudInfo, inputs=[manbudlist_drd], outputs=[manbudsum_txt,manbudindo_txt, manbudlist_cht])
                                    manbudlist_drd.input(fn=projecter.getBudInfo, inputs=[manbudlist_drd], outputs=[manbudsum_txt,manbudindo_txt, manbudlist_cht])
                                with gr.Row():
                                    exttreename_txt = gr.Textbox(label='ExtTreeTask name:')

                                with gr.Row():
                                    exttreetasktype_rad = gr.Radio(choices=['In','Out'],value='In',interactive=True, label='Ext Branch Type')
                                    exttreecopytype_rad = gr.Radio(choices=['Src','Copy'],value='Copy',interactive=True, label='Ext Branch Type')
                                with gr.Row():
                                    with gr.Column():
                                        with gr.Row():
                                            outexttreeparam_txt = gr.Textbox(label='OutExtTreeParam',lines=5)
                                    # with gr.Row():
                                    #     outextreesubtask_btn = gr.Button('Sub OutExtTree')
                        with gr.Tab('Edit'):
                            with gr.Row():
                                addmultitastoinexttree_btn = gr.Button('Add multi to Cur InExtTree')

                            with gr.Row():
                                gr.Label('Manipulate actioner')
                            with gr.Row():
                                load_extproj_act_btn = gr.Button('Set Act InOutExtTree')
                                reset_initact_btn = gr.Button('Set Act ProjectBase')
                            with gr.Row():
                                inoutexttreeparamget_btn = gr.Button('Get params for InExtTree OutExtTree Tasks')
                            with gr.Row():
                                with gr.Column():
                                    inexttaskname_txt = gr.Textbox(label='In ExtTask Name')
                                    inexttaskparamedit_jsn = gr.JSON(label='In ExtTask Param')
                                with gr.Column():
                                    outexttaskname_txt = gr.Textbox(label='Out ExtTask Name')
                                    outexttaskparamedit_jsn = gr.JSON(label='Out ExtTask Param')
                                    outexttaskset_btn = gr.Button("Set Cur Task for Out Param")

                                    outexttaskadd_btn = gr.Button('Add Out Ext Task', interactive=False)
                                    outexttaskedit_btn = gr.Button('Edit Out Ext Task', interactive=False)
                            inoutexttreeparamget_btn.click(fn=projecter.getExtTreeParamsForEdit, outputs=[
                                    inexttaskname_txt, 
                                    outexttaskname_txt,
                                    inexttaskparamedit_jsn, 
                                    outexttaskparamedit_jsn,
                                    outexttaskadd_btn,
                                    outexttaskedit_btn
                                    ])
                            outexttaskset_btn.click(fn=projecter.setCurTaskToOutExtTree, inputs=[outexttaskparamedit_jsn], outputs=[outexttaskparamedit_jsn])
                            outexttaskadd_btn.click(fn=projecter.addOutExtTreeSubTask, inputs=[outexttaskparamedit_jsn])
                        maninfoextout = [
                            inexttreeparam_txt, 
                            outexttreeparam_txt,
                            manbudlist_drd, 
                            mantsklist_drd, 
                            manalltsklist_drd, 
                            exttargettask_drd]
                        with gr.Tab('Cmds'):
                            with gr.Row():
                                updinexttree_btn = gr.Button('Update InExtTree act')

                        
                        manextinfobrowse_btn.click(fn=projecter.loadMangerExtInfoExtWithBrowser, outputs=maninfoextout)
                        manextinfocurtask_btn.click(fn=projecter.loadMangerExtInfoExtForCurTask, outputs=maninfoextout)

                        exttreeoption_input = [inexttreeparam_txt, exttreetasktype_rad, exttargettask_drd, exttreecopytype_rad, exttreename_txt]
                        inet_extmanbud_btn.click(fn=projecter.addInExtTreeInfo, inputs=exttreeoption_input + [manbudlist_drd], outputs=[inexttreeparam_txt])
                        inet_extmantasks_btn.click(fn=projecter.addInExtTreeInfo, inputs=exttreeoption_input + [manalltsklist_drd], outputs=[inexttreeparam_txt])
                        mantsklist_btn.click(fn=projecter.addInExtTreeInfo, inputs=exttreeoption_input + [mantsklist_drd], outputs=[inexttreeparam_txt])

                        outet_extmanbud_btn.click(fn=projecter.addOutExtTreeInfo, inputs=[outexttreeparam_txt, manbudlist_drd], outputs=outexttreeparam_txt)
                        outet_extmantasks_btn.click(fn=projecter.addOutExtTreeInfo, inputs=[outexttreeparam_txt, manalltsklist_drd], outputs=outexttreeparam_txt)
                    
                    std_output_man_list = [
                                        get_savdman_btn, 
                                        get_tempman, 
                                        #    params_prman, 
                                           name_prman, 
                                        #    exttaskopt_chgr, 
                                        tempman_drp,
                                        sessionnamecur_txt,
                                        actionerlist_rad
                                           ]

                    # edit_param_prman.click(fn=manipulate_manager.editParamPrivManager,inputs=params_prman, outputs=std_output_man_list)
                    save2curtask_btn.click(fn=manipulate_manager.savePrivManToTask, outputs=std_output_man_list)
                    updt_prman_btn.click(fn=manipulate_manager.getPrivManager, outputs=std_output_man_list)                  
                    exe_act2cur_btn.click(fn=manipulate_manager.initSavdManagerToCur, inputs=get_savdman_btn, outputs=std_output_man_list)
                    load_prman_btn.click(fn=manipulate_manager.loadPrivManager, inputs=get_savdman_btn, outputs = std_output_man_list)
                    # setname_prman_btn.click(fn=manipulate_manager.setCurrAsManagerStartTask, outputs=std_output_man_list)
                    # exttaskopt_chgr.change(fn=manipulate_manager.setCurrentExtTaskOptions, inputs=exttaskopt_chgr, outputs=std_output_man_list)
                    # clr_prman_btn.click(fn=manipulate_manager.resetAllExtTaskOptions, outputs=std_output_man_list)

                    with gr.Tab("Text"):
                        analysis_text = gr.Highlightedtext(label="Diff",
                                    combine_adjacent=True,
                                    show_legend=True,
                                    color_map={
                                        "bad": "red", 
                                        "good": "green",
                                        "notgood":"yellow"
                                        })
                        with gr.Row():
                            log_plot = gr.Plot()
                        with gr.Row():
                            notgood = gr.Number(value=-0.1, label='Notgood')
                            bad = gr.Number(value=-5, label='bad')
                            analysis_log = gr.Textbox()
                            gr.Button('Get').click(fn=projecter.getTextInfo, inputs=[notgood, bad], outputs=[analysis_text, analysis_log, log_plot])
                        tokenizedtext_htxt = gr.Highlightedtext(label="Tokens",
                                    combine_adjacent=True,
                                    show_legend=True,
                                    color_map={
                                        "token": "white", 
                                        "bytes": "green"
                                        })
                        gr.Button('Tokenize').click(fn=projecter.getWordTokenPairs, outputs=tokenizedtext_htxt)
                       
                    with gr.Tab('Ext Tree Managment'):
                        UI.exttreemanagerManipulator(projecter)

                    with gr.Tab("Others"):
                        parents_list = gr.Dropdown(label="Parent tasks:")
                        find_key_type = gr.Dropdown(choices=finder.getKayArray(), value='msg', interactive=True)
                        with gr.Row():
                            trg_params_list = gr.Dropdown(label='List of params')
                            trg_keys_list = gr.Dropdown(label='List of keys')
                        parents_list.select(fn=projecter.getByTaskNameParamList, inputs=[parents_list], outputs=[trg_params_list])
                        trg_params_list.select(fn=projecter.getByTaskNameTasksKeys, inputs=[parents_list, trg_params_list], outputs=[trg_keys_list])
                        gr.Button('Copy').click(fn=projecter.getFinderKeyString, inputs=[parents_list, find_key_type, trg_params_list, trg_keys_list])
                        project_clear = gr.Button(value="clear tasks")
                        fix_task_btn = gr.Button(value = 'Fix Q Tasks')
                        gr.Button('Check Trash').click(fn=projecter.checkTrashInManagerFolder)
 
            with gr.Row() as r:
                gr.Label('Save and load project')
            with gr.Row() as r:
                project_name = gr.Textbox(value = project_manipulator.current_project_name, label="Project name")
                project_save = gr.Button(value="save")
                # projects_list = gr.Dropdown(choices=project_manipulator.loadList(), label="Available projects:")
                project_load = gr.Button(value = "load")
                project_reload = gr.Button(value='reload')
                gr.Button('append').click(fn=project_manipulator.appendProjectTasks)
            with gr.Row() as r:
                saveresresult_txt = gr.Textbox()
                gr.Button('Save to reserved').click(fn=projecter.saveToTmp, outputs=saveresresult_txt)
                projectrestore_btn = gr.Button('Restore reserved')
                project_save.click(fn=projecter.save, inputs=[project_name], outputs=saveresresult_txt )

            # param_updt = gr.Button(value="Edit param")


            creation_types_radio_list = projecter.getMainCommandList()
            creation_types_radio_list += manager.getSecdCommandList()
            for param in manager.vars_param:
                creation_types_radio_list.append(param)
                creation_types_radio_list.append("un" + param)


            # prompt_tag_list = gr.Radio(choices=["user","assistant"], label="Tag type for prompt",info="Only for request", value="user")


            # fst_msg = gr.Textbox(label="Current", lines=4, value=request)
            # output = gr.Textbox(label="Output Box")

            # checkbox = gr.CheckboxGroup(["test1","1111", "val"])

            std_output_list = [sec_msg, 
                            #    output, 
                            #    fst_msg, 
                            #    prompt_tag_list, 
                            #    checkbox,
                                name_info, 
                               param_info, 
                               prompt, 
                               task_list, 
                               param_type, 
                               parents_list, 
                               base_action_list, 
                               dial_block, 
                            #    exttaskopt_chgr, 
                               tree_names_radio, 
                               new_tree_name_txt,
                               end_names_radio, 
                               end_name_text, 
                               extcopy_chck,
                               branches_data, 
                               branch_msgs,
                               status_txt,
                               raw_dial, 
                               go_lnkfrwd_rad,
                               tmpmanname_txt,
                               tmpman_clrpck,
                               multiselecttask_txt,
                                selected_tasks_list, 
                                selected_prompt
                               ]
            std_output_list.extend([trees_data, graph_img, graph_alone, raw_graph])

            savemanact2currtask_btn.click(fn=projecter.saveManagerActionToCurrentTask, inputs=[savemanact2currtask_drd], outputs=std_output_list)
            
            updatecntreset_btn.click(fn=projecter.resetActUpdateCnt, outputs=std_output_list)

            addextmantasksintocurman.click(fn=projecter.copyExternalTmpManagerToCurrProject,
                                                               inputs=[
                                                                   tmpmanagerexttasks_dtf,
                                                                   pathtotrgtmpman_txt
                                                               ], outputs=std_output_list
                                                               )
            
            viewhiddenmsgs_chck.input(fn=projecter.setHideTaskStatus, inputs=[viewhiddenmsgs_chck], outputs=std_output_list)

            updselinexttreetasks_btn.click(fn=projecter.updateInExtTreeTasksByName, inputs=[inexttretasklist_chk], outputs=std_output_list)
            loadtaskintomanbrow_btn.click(fn=projecter.loadAdditionalTasksInManager, outputs=std_output_list)

            multishiftpartag_btn.click(fn=projecter.shiftParentTagForMultiSelect, inputs=[shiftpartag_sld], outputs=std_output_list)
            childshiftpartag_btn.click(fn=projecter.shiftParentTagForCurAndChilds, inputs=[shiftpartag_sld], outputs=std_output_list)
            changeoldtonew_btn.click(fn=projecter.replaceTextForMultiSelect, inputs=[oldtexttochange_txt, newtexttochange_txt], outputs=std_output_list)

            inextreesubtask_btn.click(fn=projecter.addInExtTreeSubTask, inputs=[inexttreeparam_txt], outputs=std_output_list)
            convbranch2inoutext_btn.click(fn=projecter.convertTaskBranchInInOutExtPair, outputs=std_output_list)
            addmultitastoinexttree_btn.click(fn=projecter.addTaskBranchInExtTree, outputs=std_output_list)
            # outextreesubtask_btn.click(fn=projecter.addOutExtTreeSubTask, inputs=[outexttreeparam_txt], outputs=std_output_list)

            setrecords_btn.click(fn=projecter.makeTaskRecordable, outputs=std_output_list)
            clrrecords_btn.click(fn=projecter.clearTaskRecords, outputs=std_output_list)
            clnresp_btn.click(fn=projecter.cleanLastMessage, outputs=std_output_list)

            addmultitotmp_btn.click(fn=projecter.addMultiSelectTasksFromStdMan, outputs=std_output_list) 
            rmvmultifrtmp_btn.click(fn=projecter.rmvMultiSelectTasksFromTmpMan, outputs=std_output_list)  
            movemulti2std_btn.click(fn=projecter.moveTaskToStdMan, outputs=std_output_list) 
            movemulti2tmp_btn.click(fn=projecter.moveTaskToTmpMan, outputs=std_output_list) 

            moveupprio_btn.click(fn=projecter.moveBranchIdxUp, outputs=std_output_list )
            movedwprio_btn.click(fn=projecter.moveBranchIdxDw, outputs=std_output_list )
            moveuptree_btn.click(fn=projecter.moveUpTree, outputs=std_output_list )
            movedwtree_btn.click(fn=projecter.moveDwTree, outputs=std_output_list )
 
            std_full = std_output_list.copy()
            std_full.extend(std_output_man_list)

            applyautocmdtomulti_btn.click(projecter.applyAutoCommandsToMulti, outputs=std_full)

            exttreetaskaddact_btn.click(fn=projecter.addCurrentExtTreeTaskActioner, outputs=std_full)

            setsessionname_btn.click(fn=projecter.getSessionNameFromList, inputs=[sessionname_drd], outputs=std_full)
            newsessionname_btn.click(fn=projecter.setNewSessionName, inputs=[sessionnamecur_txt], outputs=[sessionnamecur_txt, sessionname_drd])
   
            actaddbybrow_btn.click(fn=projecter.loadActionerByBrowsing, outputs=std_full)
            actionerlist_rad.input(fn=projecter.selectActionerByInfo, inputs=[actionerlist_rad], outputs=std_full)

            projectrestore_btn.click(fn=projecter.loadFromTmp, outputs=std_full)
            movetmp2tmp_btn.click(fn=projecter.moveTaskTmpToTmp,inputs=[tempman_drp], outputs=std_full)

            init_prman_btn.click(fn=manipulate_manager.initPrivManagerByInfo, inputs=[inittmpmaninfo_jsn], outputs=std_full)
            get_tempman.input(fn=manipulate_manager.loadTmpManager, inputs=[get_tempman], outputs=std_full)
            load_extproj_act_btn.click(fn=manipulate_manager.switchToExtTaskManager, outputs=std_full)
            updinexttree_btn.click(fn=manipulate_manager.activateExtTask, outputs=std_full)
            reset_initact_btn.click(fn=manipulate_manager.backToDefaultActioner, outputs=std_full)

            tmpmanname_txt.submit(fn=manipulate_manager.setCurManagerName, inputs = [tmpmanname_txt], outputs=std_full)
            
            exe_act_btn.click(fn=manipulate_manager.exeActions, outputs=std_full)

            stop_prman_btn.click(fn=manipulate_manager.stopPrivManager, outputs=std_full)
            rset_prman_btn.click(fn=manipulate_manager.rmvePrivManager, outputs=std_full)  


            relink_sel2cur_btn.click(fn=projecter.relinkToCurrTaskByName, inputs=[selected_tasks_list], outputs=std_output_list)
            relatedtask_btn.click(fn=projecter.selectRelatedChain, outputs=std_output_list)
            nearesttask_btn.click(fn=projecter.selectNearestTasks, outputs=std_output_list)
            get_hold_garland_btn.click(fn=projecter.selectGarlandHolders, outputs=std_output_list)

            relatedfwrdchain_btn.click(fn=projecter.getRalationForward, inputs=relatedfwrdchain_sld, outputs=std_output_list)
            relatedbackchain_btn.click(fn=projecter.getRelationBack, inputs=relatedbackchain_sld, outputs=std_output_list)

            relattaskcln_btn.click(fn=projecter.deselectRealtedChain, outputs=std_output_list)
            addtask2reltask_btn.click(fn=projecter.appendTaskToChain, outputs=std_output_list)
            addpart2reltask_btn.click(fn=projecter.appendBranchPartToChain, outputs=std_output_list)
            addbrch2reltask_btn.click(fn=projecter.appendBranchtoChain, outputs=std_output_list)
            addtree2reltask_btn.click(fn=projecter.appendTreeToChain, outputs=std_output_list)
            addchds2reltask_btn.click(fn=projecter.appendChildsToChain, outputs=std_output_list)
            addrow2reltask_btn.click(fn=projecter.selectRowTasks, outputs=std_output_list)

            addcpbranch2reltask_btn.click(fn=projecter.selectCopyBranch, outputs=std_output_list)
            addcptasks2reltask_btn.click(fn=projecter.selectCopyTasks, outputs=std_output_list)

            addcurrtaskrow2reltask_btn.click(fn=projecter.selectTaskRowFromCurrent, inputs=[addcurrtaskrow2reltask_sld], outputs=std_output_list)

            rmvtask2reltask_btn.click(fn=projecter.removeTaskFromChain, outputs=std_output_list)
            rmvpart2reltask_btn.click(fn=projecter.removeBranchPartFromChain, outputs=std_output_list)
            rmvbrch2reltask_btn.click(fn=projecter.removeBranchFromChain, outputs=std_output_list)
            rmvtree2reltask_btn.click(fn=projecter.removeTreeFromChain, outputs=std_output_list)
            rmvchds2reltask_btn.click(fn=projecter.removeChildsFromChain, outputs=std_output_list)
            rmvprns2reltask_btn.click(fn=projecter.removeParentsFromChain, outputs=std_output_list)
            delete_reltasks_btn.click(fn=projecter.removeMultiSelect, outputs=std_output_list)
            set_multi_child_btn.click(fn=projecter.makeMultiSelectedAsChilds, outputs=std_output_list)
            
            tree_names_radio.input(fn=projecter.goToTreeByName, inputs=[tree_names_radio], outputs=std_output_list)
            new_tree_name_txt.submit(fn=projecter.setTreeName,inputs=[new_tree_name_txt], outputs=std_output_list)
            end_names_radio.input(fn=projecter.setCurrTaskByBranchEndName, inputs=[end_names_radio], outputs=std_output_list)
            end_name_text.submit(fn=projecter.setBranchEndName, inputs=[end_name_text], outputs=std_output_list)
            # setname_prman_text.click(fn=projecter.backToStartTask, outputs=std_output_list)
            roles_list.change(fn=projecter.switchRole, inputs=[roles_list, prompt], outputs=std_output_list)

            request_btn.click(fn=userinput_manager.makeRequestAction, inputs=[prompt, base_action_list, roles_list, extcopy_chck], outputs=std_output_list)
            response_btn.click(fn=userinput_manager.makeResponseAction, inputs=[prompt, base_action_list, roles_list, extcopy_chck], outputs=std_output_list)
            custom_btn.click(fn=userinput_manager.makeCustomAction, inputs=[prompt, base_action_list, custom_list], outputs=std_output_list)
            
            collect_btn.click(fn=userinput_manager.createCollectTreeOnSelectedTasks,inputs=slct_action_list, outputs= std_output_list)
            shoot_btn.click(fn=userinput_manager.createShootTreeOnSelectedTasks,inputs=slct_action_list, outputs= std_output_list)
            garland_btn.click(fn=userinput_manager.createGarlandOnSelectedTasks,inputs=slct_action_list, outputs= std_output_list)
            
            garlandmulti_btn.click(fn=projecter.createGarlandFromMultiSelect, outputs=std_output_list)
            collectmulti_btn.click(fn=projecter.createCollectFromMultiSelect, outputs=std_output_list)
            minichainstobig_btn.click(fn=projecter.copyMultiSelectedTasksChainsToSingleChain, outputs=std_output_list)
            disunselectchild_btn.click(fn=projecter.setMultiselectedTasksChainToMainTrack, outputs=std_output_list)
            enablemultichilds_btn.click(fn=projecter.resetMultiselectedTasksChainToMainTrack, outputs=std_output_list)

            moveup_btn.click(fn=manipulate_manager.moveCurrentTaskUP, outputs=std_output_list)
            switchup_btn.click(fn=manipulate_manager.swicthCurTaskUP, outputs=std_output_list)
            reparup_btn.click(fn=manipulate_manager.reparentCurTaskChildsUP, outputs=std_output_list)
            unite_btn.click(fn=manipulate_manager.uniteTask, outputs=std_output_list)
            parent_btn.click(fn=manipulate_manager.makeActionParent, outputs=std_output_list)
            child_btn.click(fn=manipulate_manager.makeActionChild, outputs=std_output_list)
            link_btn.click(fn=manipulate_manager.makeActionLink, outputs=std_output_list)
            revlink_btn.click(fn=manipulate_manager.makeActionRevertLink, outputs=std_output_list)
            unparent_btn.click(fn=manipulate_manager.makeActionUnParent, outputs=std_output_list)
            unlink_btn.click(fn=manipulate_manager.makeActionUnLink, outputs=std_output_list)
            delete_btn.click(fn=manipulate_manager.deleteActionTask, outputs=std_output_list)
            extract_btn.click(fn=manipulate_manager.extractActionTask, outputs=std_output_list)
            rm_branch_btn.click(fn=manipulate_manager.removeActionBranch, outputs=std_output_list)
            rm_tree_btn.click(fn=manipulate_manager.removeActionTree, outputs=std_output_list)
            copy_chain_btn.click(fn=manipulate_manager.copyChainStepped, outputs=std_output_list)
            clean_task_btn.click(fn=manipulate_manager.cleanCurrTask, outputs=std_output_list)
 
            param_apnd.click(fn=parameters_manager.appendNewParamToTask, inputs=[param_opt], outputs=std_output_list)
            param_rmve.click(fn=parameters_manager.removeParamFromTask, inputs=[param_type], outputs=std_output_list)
            param_edit.click(fn=parameters_manager.setTaskKeyValue, inputs=[param_type, param_key, param_mnlval], outputs=std_output_list)
            addkey_apd_btn.click(fn=parameters_manager.addTaskNewKeyValue, inputs=[param_type, addkey_key_txt, addkey_val_txt], outputs=std_output_list)


            # extpr_new.click(fn=projecter.newExtProject, inputs=[ extpr_list, prompt], outputs=std_output_list)
            # extpr_append.click(fn=projecter.appendExtProject, inputs=[ extpr_list, prompt], outputs=std_output_list)


            # move2child_btn.click(fn=projecter.moveToNextChild, outputs=std_output_list)
            # move2parnt_btn.click(fn=projecter.moveToParent, outputs=std_output_list)
            # move2brnch_btn.click(fn=projecter.moveToNextBranch, outputs=std_output_list)

            next_branch_btn.click(fn=projecter.goToNextBranch, outputs=std_output_list)
            prev_branch_btn.click(fn=projecter.goToPrevBranch, outputs=std_output_list)
            next_brend_bt.click(fn=projecter.goToNextBranchEnd, outputs=std_output_list)
            go_parnt_btn.click(fn=projecter.goToParent, outputs=std_output_list)
            go_child_btn.click(fn=projecter.goToNextChild, outputs=std_output_list)  
            go_hlfbrch_btn.click(fn=projecter.goToHalfBranch, outputs=std_output_list)
            go_brchfrk_btn.click(fn=projecter.goToBranchFork, outputs=std_output_list)
            go_taskbud_btn.click(fn=projecter.goToCurrTaskBud, outputs=std_output_list)

            # raw_next_brnch_btn.click(fn=projecter.goToNextBranch, outputs=std_output_list)
            # raw_next_brend_btn.click(fn=projecter.goToNextBranchEnd, outputs=std_output_list)
            # raw_move_parnt_btn.click(fn=projecter.goToParent, outputs=std_output_list)
            # raw_move_child_btn.click(fn=projecter.goToNextChild, outputs=std_output_list)  

           

            new_tree_btn.click(fn=projecter.createNewTree, outputs=std_output_list)
            next_tree_btn.click(fn=projecter.goToNextTree, outputs=std_output_list)
            go_lnkback_btn.click(fn=projecter.goBackByLink, outputs=std_output_list)          

            sel_task_btn.click(fn=projecter.setCurrentTaskByName, inputs=[task_list], outputs= std_output_list )
            go_lnkfrwd_btn.click(fn=projecter.setCurrentTaskByName, inputs=[go_lnkfrwd_rad], outputs= std_output_list )


            project_clear.click(fn=projecter.clear)
            project_load.click(fn=projecter.load, outputs=[project_name])
            project_reload.click(fn=projecter.reload)
            # project_manLoad.click(fn=projecter.loadManager, outputs=std_output_list)
            # project_manBrow.click(fn=projecter.loadManagerFromBrowser, outputs=std_output_list)

            fix_task_btn.click(fn=projecter.fixCurManQtasks, outputs=std_output_list)

            # run_iter_btn.click(fn=manager.updateSteppedTree, outputs=std_output_list, api_name='runIteration')
            update_task_btn.click(fn=manager.update,outputs=std_output_list, api_name="update_task_btn")
            updatecur_task_btn.click(fn=manager.updateCurrent, outputs=std_output_list)

            update_step_btn.click(fn=projecter.update, outputs=std_output_list)
            updateall_step_btn.click(fn=projecter.updateAll, inputs=[updatecheckown_chk], outputs=std_output_list)
            updateall_stepNs_btn.click(fn=projecter.updateAllnTimes, inputs=[updateall_stepNs_sld, updatecheckown_chk], outputs=std_output_list)
            upd2cur_step_btn.click(fn=projecter.updateAllUntillCurrTask, inputs=[updatecheckown_chk], outputs=std_output_list)
            updatechildtasks_btn.click(fn=projecter.updateChildTasks, inputs=[updatecheckown_chk], outputs=std_output_list)
            updatemultitasks_btn.click(fn=projecter.updateMultiSelectedTasks, inputs=[updatecheckown_chk], outputs=std_output_list)
            updateforktasks_btn.click(fn=projecter.updateFromFork, inputs=[updatecheckown_chk], outputs=std_output_list)

            updbrnc_step_btn.click(fn=projecter.updateCurrentTree, outputs=std_output_list)
            reset_step_btn.click(fn=projecter.resetUpdate, outputs= std_output_list)

            # next_task_btn.click(fn=manager.setNextTask, inputs=[next_task_val], outputs=std_output_list, api_name='next_task',)
            # prev_task_btn.click(fn=manager.setNextTask, inputs=[prev_task_val], outputs=std_output_list, api_name='prev_task',)
            # action_to_task_btn.click(fn=manager.makeTaskAction, inputs=[prompt, task_type_list, creation_types_radio, prompt_tag_list], outputs=std_output_list, api_name="makeTaskAction")
            if project_params['project'] != None:
                projecter.loadManagerByPath(project_params['project'])
# [[---]]
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
                    if task.checkType("SetOptions"):
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
            # config_name.change(fn=manager.getParamGradioInput, inputs=[config_name], outputs=[config_values])

    demo.launch(share=project_params['share'])

def test_cmd_body(manager : Actioner.Manager, projecter : Projecter):
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



def mliner_body(manager : Actioner.Manager, projecter : Projecter):

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


# [[---]]

def main() -> None:
    prompt = "Bissness presentation for investors. My idea is automation of presentation. You just type your idea then software propose your steps to create presentation and try to automatize it."
    # prompt = "automation of presentation"


    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    # Add arguments for the variables
    parser.add_argument("--project", type=str, help="Path to start project location")
    parser.add_argument("--share", type=bool, help="Share UI via Gradio", default=False)

    # Parse the command line arguments
    args = parser.parse_args()

    # Access the values of the variables
    project_params = {
        "project": args.project,
        "share": args.share
    }

    # Use the variables in your script
    print(f"Params: {project_params}")


    manager = Actioner.Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())

    projecter = Projecter(manager)

    mode = manager.getParam("app type")

    if mode == "gradio":
        print("Start gradio application")
        gr_body(prompt, manager, projecter, project_params=project_params)
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
