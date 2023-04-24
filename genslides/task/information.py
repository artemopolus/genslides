from genslides.task.base import BaseTask

import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester

class InformationTask(BaseTask):
    def __init__(self,  parent, reqhelper : ReqHelper, requester :Requester, description) -> None:
        super().__init__(reqhelper, requester, type='Information', prompt=description)
