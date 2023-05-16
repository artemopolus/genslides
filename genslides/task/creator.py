from genslides.task.presentation import PresentationTask
from genslides.task.base import BaseTask
from genslides.task.base import TaskDescription
from genslides.task.richtext import RichTextTask
from genslides.task.request import RequestTask

import genslides.commands.create as cr

def createTaskByType(type : str,info : TaskDescription):
    # if type == "Presentation":
        # return PresentationTask(info)
    if type.endswith("Text"):
        info.method = RichTextTask
        info.type = type
        return cr.CreateCommand(info)
    if type.endswith("Request"):
        info.method = RequestTask
        info.type = type
        return cr.CreateCommand(info)
    else:
    	return None
