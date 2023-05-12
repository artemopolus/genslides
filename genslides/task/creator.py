from genslides.task.presentation import PresentationTask
from genslides.task.base import BaseTask
from genslides.task.base import TaskDescription
from genslides.task.text import RichTextTask

import genslides.commands.create as cr

def createTaskByType(type : str,info : TaskDescription):
    # if type == "Presentation":
        # return PresentationTask(info)
    if type.endswith("Text"):
        info.method = RichTextTask
        info.type = type
        return cr.CreateCommand(info)
    else:
    	return None
