from genslides.task.base import BaseTask
from genslides.commands.create import CreateCommand

import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester
import genslides.utils.request as Response

import collections
import collections.abc

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches


class PresentationTask(BaseTask):
    def __init__(self,  parent, reqhelper : ReqHelper, requester :Requester, description) -> None:
        super().__init__(reqhelper, requester, type='Presentation', prompt=description, parent=parent)
        self.prs = Presentation()
        self.description = description
        title_slide_layout = self.prs.slide_layouts[0]
        slide = self.prs.slides.add_slide(title_slide_layout)
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        print("Init presentation")
        presentation_prompt = self.reqhelper.getPrompt('Presentation', self.description)
        index = 0
        while len(self.responselist) == 0 and index < 3:
            print("Request to chatgpt about slides")
            if index > 0:
                info_prompt = self.reqhelper.getPrompt('Information', self.description)

                info_response = self.requester.getResponse(info_prompt)
                search_result = ""
                for pack in info_response:
                    if(pack.type == 'Search'):
                        print('Doing search')
                comb_prompt = self.reqhelper.getPrompt('Combinator', search_result)
                info_response = self.requester.getResponse(comb_prompt)
                for pack in info_response:
                    if(pack.type == 'Text'):
                        print('Add data to description')

                

            response = self.requester.getResponse(presentation_prompt)
            for pack in response:
                if pack.type == 'Slide':
                    self.responselist.append(pack)


class SlideTask(BaseTask):
    def __init__(self, parent, reqhelper : ReqHelper, requester :Requester, description) -> None:
        super().__init__(reqhelper, requester)
        self.parent = parent
        self.description = description
        print("Init slide")
