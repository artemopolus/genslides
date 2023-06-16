from genslides.task.presentation import PresentationTask
from genslides.task.base import BaseTask
from genslides.task.base import TaskDescription
from genslides.task.richtext import RichTextTask
from genslides.task.request import RequestTask
from genslides.task.response import ResponseTask
from genslides.task.collect import CollectTask
from genslides.task.group import GroupTask
from genslides.task.readfile import ReadFileTask
from genslides.task.writetofile import WriteToFileTask
from genslides.task.websurf import WebSurfTask
from genslides.task.readpage import ReadPageTask
from genslides.task.largetextresponse import LargeTextResponseTask

from genslides.task.gettime import GetTimeTask

import genslides.commands.create as cr

def checkTypeFromName(name : str, type :str) -> bool:
    stype = ''.join([i for i in name if not i.isdigit()])
    return stype.endswith(type)

def createTaskByType(type : str,info : TaskDescription):
    # if type == "Presentation":
        # return PresentationTask(info)
    stype = ''.join([i for i in type if not i.isdigit()])
    info.type = stype
    info.filename = type
    if stype.endswith("Text"):
        info.method = RichTextTask
        return cr.CreateCommand(info)
    if stype.endswith("Request"):
        info.method = RequestTask
        return cr.CreateCommand(info)
    if stype.endswith("LargeTextResponse"):
        info.method = LargeTextResponseTask
        return cr.CreateCommand(info)
    if stype.endswith("Response"):
        info.method = ResponseTask
        return cr.CreateCommand(info)
    if stype.endswith("Group"):
        info.method = GroupTask
        return cr.CreateCommand(info)
    if stype.endswith("Collect"):
        info.method = CollectTask
        return cr.CreateCommand(info)
    if stype.endswith("ReadFile"):
        info.method = ReadFileTask
        return cr.CreateCommand(info)
    if stype.endswith("WriteToFile"):
        info.method = WriteToFileTask
        return cr.CreateCommand(info)
    if stype.endswith("WebSurf"):
        info.method = WebSurfTask
        return cr.CreateCommand(info)
    if stype.endswith("GetTime"):
        info.method = GetTimeTask
        return cr.CreateCommand(info)
    if stype.endswith("ReadPage"):
        info.method = ReadPageTask
        return cr.CreateCommand(info)
    else:
    	return None
