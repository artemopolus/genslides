from genslides.task.base import BaseTask
from genslides.commands.create import CreateCommand

import genslides.utils.reqhelper as ReqHelper
import collections
import collections.abc

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches


class PresentationTask(BaseTask):
    def __init__(self,  parent, reqhelper : ReqHelper ,description="python-pptx was here!"):
        super().__init__(reqhelper)
        self.prs = Presentation()
        title_slide_layout = self.prs.slide_layouts[0]
        slide = self.prs.slides.add_slide(title_slide_layout)
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        print("Init presentation")
        print("Request to chatgpt about slides")

    def getCmd(self):
        print("create slide")
        prompt = 'create slide'
        return CreateCommand( self.prs, self.reqhelper, prompt , SlideTask)


class SlideTask(BaseTask):
    def __init__(self, parent, reqhelper : ReqHelper, description) -> None:
        super().__init__(reqhelper)
        self.parent = parent
        print("Init slide")
