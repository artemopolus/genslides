from genslides.task.base import BaseTask
from genslides.task.base import TaskDescription
from genslides.task.richtext import RichTextTask
from genslides.task.request import RequestTask
from genslides.task.response import ResponseTask
from genslides.task.collect import CollectTask, GarlandTask, ReceiveTask
from genslides.task.group import GroupTask
from genslides.task.readfile import ReadFileTask
from genslides.task.writetofile import WriteToFileTask
from genslides.task.websurf import WebSurfTask
from genslides.task.readpage import ReadPageTask
from genslides.task.largetextresponse import LargeTextResponseTask

from genslides.task.writedialtofile import WriteBranchTask
from genslides.task.readdial import ReadBranchTask

from genslides.task.gettime import GetTimeTask

from genslides.task.iteration import IterationTask, IterationEndTask
# from genslides.task.runscript import RunScriptTask
from genslides.task.websurfarray import WebSurfArrayTask
from genslides.task.writejsontofile import WriteJsonToFileTask

from genslides.task.largedialresponse import LargeDialResponseTask

import genslides.task.setoptions as so
from genslides.task.writetofileparam import WriteToFileParamTask
from genslides.task.readfileparam import ReadFileParamTask

# from genslides.task.extproject import ExtProjectTask
import genslides.task.extproject as ep
import genslides.task.runscript as rs
from genslides.task.groupcollect import GroupCollectTask

import genslides.task.external as ex

import genslides.commands.create as cr
import genslides.task.link as lk
import genslides.task.entry as ey
import genslides.task.keycraft as cg

def checkTypeFromName(name : str, type :str) -> bool:
    stype = ''.join([i for i in name if not i.isdigit()])
    return stype.endswith(type)

def createTaskByType(type : str, info : TaskDescription):
    # print('Start params=',info.params)
    stype = ''.join([i for i in type if not i.isdigit()])
    info.type = stype
    info.filename = type
    # print('Create task',type,'-', stype)
    if stype.endswith("Text"):
        info.method = RichTextTask
        return cr.CreateCommand(info)
    if stype.endswith("Request"):
        info.method = RequestTask
        return cr.CreateCommand(info)
    if stype.endswith("LargeTextResponse"):
        info.method = LargeTextResponseTask
        return cr.CreateCommand(info)
    if stype.endswith("LargeDialResponseTask"):
        info.method = LargeDialResponseTask
        return cr.CreateCommand(info)
    if stype.endswith("Response"):
        info.method = ResponseTask
        return cr.CreateCommand(info)
    if stype.endswith("Group"):
        info.method = GroupTask
        return cr.CreateCommand(info)
    if stype.endswith("GroupCollect"):
        info.method = GroupCollectTask
        return cr.CreateCommand(info)
    if stype.endswith("Receive"):
        info.method = ReceiveTask
        return cr.CreateCommand(info)
    if stype.endswith("Collect"):
        info.method = CollectTask
        return cr.CreateCommand(info)
    if stype.endswith("Listener"):
        info.method = lk.ListenerTask
        return cr.CreateCommand(info)
    if stype.endswith("Garland"):
        info.method = GarlandTask
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
    if stype.endswith("ReadBranch"):
        info.method = ReadBranchTask
        return cr.CreateCommand(info)
    if stype.endswith("WriteBranch"):
        info.method = WriteBranchTask
        return cr.CreateCommand(info)
    if stype.endswith("Iteration"):
        info.method = IterationTask
        return cr.CreateCommand(info)
    if stype.endswith("IterationEnd"):
        info.method = IterationEndTask
        return cr.CreateCommand(info)
    if stype.endswith("RunScript"):
        info.method = rs.RunScriptTask
        return cr.CreateCommand(info)
    if stype.endswith("SaveScriptRun"):
        info.method = rs.SaveScriptRunTask
        return cr.CreateCommand(info)
    if stype.endswith("WebSurfArray"):
        info.method = WebSurfArrayTask
        return cr.CreateCommand(info)
    if stype.endswith("WriteJsonToFile"):
        info.method = WriteJsonToFileTask
        return cr.CreateCommand(info)
    if stype.endswith("SetOptions"):
        info.method = so.SetOptionsTask
        return cr.CreateCommand(info)
    if stype.endswith("Generator"):
        info.method = so.GeneratorTask
        return cr.CreateCommand(info)
    if stype.endswith("WriteToFileParam"):
        info.method = WriteToFileParamTask
        return cr.CreateCommand(info)
    if stype.endswith("ReadFileParam"):
        info.method = ReadFileParamTask
        return cr.CreateCommand(info)
    if stype.endswith("ExtProject"):
        info.method = ep.ExtProjectTask
        return cr.CreateCommand(info)
    if stype.endswith('ExternalInput'):
        info.method = ex.ExternalInput
        return cr.CreateCommand(info)
    if stype.endswith("JumperTree"):
        info.method = ep.JumperTreeTask
        return cr.CreateCommand(info)
    if stype.endswith("InExtTree"):
        info.method = ep.InExtTreeTask
        return cr.CreateCommand(info)
    if stype.endswith("OutExtTree"):
        info.method = ep.OutExtTreeTask
        return cr.CreateCommand(info)
    if stype.endswith("Searcher"):
        info.method = ep.SearcherTask
        return cr.CreateCommand(info)    
    if stype.endswith("Entry"):
        info.method = ey.EntryTask
        return cr.CreateCommand(info)    
    if stype.endswith("KeyCraft"):
        info.method = cg.KeyCraftTask
        return cr.CreateCommand(info)    
    else:
    	return None
    
def getTasksDict() -> list:
    out = []
    out.append({"type":"Request","short":"Rq","creation":RequestTask})
    out.append({"type":"Response","short":"Rs","creation":ResponseTask})
    out.append({"type":"Receive","short":"Rc","creation":ReceiveTask})
    out.append({"type":"Collect","short":"Cl","creation":CollectTask})
    out.append({"type":"Listener","short":"Ls","creation":lk.ListenerTask})
    out.append({"type":"Garland","short":"Gr","creation":GarlandTask})
    out.append({"type":"GroupCollect","short":"Gc","creation":GroupCollectTask})
    out.append({"type":"ReadDial","short":"Rb","creation":ReadBranchTask})
    out.append({"type":"WriteBranch","short":"Wb","creation":WriteBranchTask})
    out.append({"type":"ReadFile","short":"Rf","creation":ReadFileTask})
    out.append({"type":"WriteToFile","short":"Wf","creation":WriteToFileTask})
    out.append({"type":"WriteToFileParam","short":"Wp","creation":WriteToFileParamTask})
    out.append({"type":"ReadFileParam","short":"Rp","creation":ReadFileParamTask})
    out.append({"type":"WriteJsonToFile","short":"Wj","creation":WriteJsonToFileTask})
    out.append({"type":"SetOptions","short":"So","creation":so.SetOptionsTask})
    out.append({"type":"Generator","short":"Ge","creation":so.GeneratorTask})
    out.append({"type":"RunScript","short":"Rs","creation":rs.RunScriptTask})
    out.append({"type":"ExtProject","short":"Ep","creation":ep.ExtProjectTask})
    out.append({"type":"ExternalInput","short":"Ei","creation":ex.ExternalInput})
    out.append({"type":"JumperTree","short":"Je","creation":ep.JumperTreeTask})
    out.append({"type":"InExtTree","short":"Ie","creation":ep.InExtTreeTask})
    out.append({"type":"OutExtTree","short":"Oe","creation":ep.InExtTreeTask})
    out.append({"type":"Searcher","short":"Se","creation":ep.SearcherTask})
    out.append({"type":"Entry","short":"Ey","creation":ey.EntryTask})
    out.append({"type":"KeyCraft","short":"Cg","creation":cg.KeyCraftTask})
    return out
