import genslides.task.request as Request
import genslides.task_tools.py_parser as PyParser
import genslides.utils.loader as Ld

class GenDocTask(Request.RequestTask):
    def __init__(self, task_info, type="GenDoc"):
        super().__init__(task_info, type)

    def update(self, input = None):
        if not self.checkParentMsgList(update=True, save_curr=False):
            self.saveGenslidesJsonFile()
        out = super().update(input)
        return out
    
    def saveGenslidesJsonFile( self ):
        gres, gparam = self.getParamStruct("gendoc_config", True)
        if gres:
            try:
                path_to_folder = self.findKeyParam(gparam["path_to_write"])
                code = Ld.Loader.convertMDwithPythonToCode( self.findKeyParam(gparam["target"]) )
                filename = self.findKeyParam(gparam["filename"])
                report = PyParser.generate_genslides_json_file( code, filename, path_to_folder )
                gparam["info"] = report["report"]
                gparam["result"] = report["result"]
                gparam["result_filepath"] = Ld.Loader.getManRePath( report["result_filepath"], self.manager.getPath())

                self.setParamStruct( gparam )
            except Exception as e:
                self.updateUpdationInfo(f"Error:{e}")


