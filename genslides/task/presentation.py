from genslides.task.base import BaseTask

import collections
import collections.abc

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches


class PresentationTask(BaseTask):
    def __init__(self, text="Hello, World", subtext="python-pptx was here!"):
        super().__init__()
        self.prs = Presentation()
        title_slide_layout = self.prs.slide_layouts[0]
        slide = self.prs.slides.add_slide(title_slide_layout)
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        title.text = text
        subtitle.text = subtext

    def createSubTask(self):
        return None


class SlideTask(BaseTask):
    def __init__(self, parent) -> None:
        super().__init__()
        self.parent = parent
