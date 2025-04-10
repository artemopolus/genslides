import genslides.task.request as Request
import genslides.utils.loader as Ld


class JsonTask(Request.RequestTask):
    def __init__(self, task_info, type="Json"):
        super().__init__(task_info, type)

    def getJsonObject( self , inparams :dict):
        jres, jobj = self.getParamStruct("json_create", True)
        if jres:
            key = self.findKeyParam( jobj["key"] )
            jtype = self.findKeyParam( jobj["jtype"] )
            if jtype in ["list","dict"]:
                out = {}
                trgs = self.getChilds()
                emptys = []
                while(len(trgs)):
                    emptys = []
                    for child in trgs:
                        if not child.checkType("Json"):
                            emptys.extend(child.getChilds())
                        else:
                            res = child.getJsonObject( inparams )
                            if res == None:
                                emptys.extend(child.getChilds())
                            elif "schema" in inparams and inparams["schema"]:
                                if isinstance(res, dict):
                                    out.update( res )
                            elif jtype == "dict":
                                if isinstance(res, dict):
                                    out.update( res )
                            elif jtype == "list":
                                out.append( res )
                            
                    trgs = emptys.copy()
                if "schema" in inparams and inparams["schema"]:
                    if jtype == "dict":
                        rq = [ k for k, v in out.items() ]
                        return { key : {"type": "object","properties":out},"required":rq,"additionalFields": False}
                    elif jtype == "list":
                        return { key : {"type": "object","items":out}}
                else:
                    return out
            elif jtype == "str":
                if "schema" in inparams and inparams["schema"]:
                    return { key :{"type":"string", "description": self.findKeyParam( jobj["value"] ) }}
                else:
                    return { key :self.findKeyParam( jobj["value"] ) }
        return None


    def update(self, input = None):
        out = super().update(input)
        jres, inparams = self.getParamStruct("json_create", True)
        if jres:

            trg = self.getJsonObject(inparams)
            if trg != None:
                self.updateParamStruct("json_create","result", Ld.Loader.convJsonToText(trg))
        return out
