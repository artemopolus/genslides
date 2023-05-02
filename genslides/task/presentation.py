from genslides.task.base import BaseTask
from genslides.task.base import TaskDescription

from genslides.task.text import TextTask
from genslides.task.text import RichTextTask
from genslides.commands.create import CreateCommand


import genslides.utils.reqhelper as ReqHelper
import genslides.utils.request as Requester
import genslides.utils.request as Response
from genslides.utils.chatgptrequester import ChatGPTrequester

import collections
import collections.abc

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches


class PresentationTask(TextTask):
    def __init__(self, reqhelper: ReqHelper, requester: Requester, prompt=None, parent=None, method=None) -> None:
        super().__init__(reqhelper, requester, "Presentation", prompt, parent, method)
        print("Start presentation Task")
        request = self.init + self.prompt + self.endi
        descriptions = self.getResponse(request)
        if len(descriptions) == 0:
            print("Request to ChatGPT")
            chat  = ChatGPTrequester()
            responses = chat.getResponse(request, ['title','description'])
            for response in responses:
                print(response)
                description = "Title of slide is " + response.trgs['title'] +". Slide description is:"+  response.trgs['description']
                descriptions.append(description)
            self.saveRespJson(request, descriptions)
            del chat
        else:
            print("Data from saved file")

        for t in descriptions:
            self.task_creation_result += t + '\n'

        self.prs = Presentation()

        for description in descriptions:
            ch_prompt = description + "Presentation description is :" + self.prompt
            self.addChildTask(TaskDescription( prompt= ch_prompt, method= SlideTask, parent= self))

    # def __init__(self,  parent, reqhelper : ReqHelper, requester :Requester, description) -> None:
    #     super().__init__(reqhelper, requester, type='Presentation', prompt=description, parent=parent)
    #     self.prs = Presentation()
    #     self.description = description
    #     title_slide_layout = self.prs.slide_layouts[0]
    #     slide = self.prs.slides.add_slide(title_slide_layout)
    #     title = slide.shapes.title
    #     subtitle = slide.placeholders[1]
    #     print("Init presentation")
    #     presentation_prompt = self.reqhelper.getPrompt('Presentation', self.description)
    #     index = 0
    #     while len(self.responselist) == 0 and index < 3:
    #         print("Request to chatgpt about slides")
    #         if index > 0:
    #             info_prompt = self.reqhelper.getPrompt('Information', self.description)

    #             info_response = self.requester.getResponse(info_prompt)
    #             search_result = ""
    #             for pack in info_response:
    #                 if(pack.type == 'Search'):
    #                     print('Doing search')
    #             comb_prompt = self.reqhelper.getPrompt('Combinator', search_result)
    #             info_response = self.requester.getResponse(comb_prompt)
    #             for pack in info_response:
    #                 if(pack.type == 'Text'):
    #                     print('Add data to description')

                

    #         response = self.requester.getResponse(presentation_prompt)
    #         for pack in response:
    #             if pack.type == 'Slide':
    #                 self.responselist.append(pack)


class SlideTask(TextTask):
    def __init__(self, reqhelper: ReqHelper, requester: Requester, prompt=None, parent=None, method=None) -> None:
        super().__init__(reqhelper, requester, "Slide", prompt, parent, method)
        print("Create slide with prompt:\n" + prompt)
        request = self.init + self.prompt + self.endi
        descriptions = self.getResponse(request)
        slide_part_prompts =[]
        if len(descriptions) == 0:
            self.task_creation_result += "Request to ChatGPT:\n"
            # print(request)
            chat  = ChatGPTrequester()
            responses = chat.getResponse(request, ['type','description','position'])
            index = 0
            for response in responses:
                description = {}
                description['id'] = index
                index += 1
                description['solved'] = False
                description['type'] = response.trgs['type']
                description['description'] = response.trgs['description']
                description['position'] = response.trgs['position']
                # print(description)
                init_sent = "unknown"
                if description['type'] == 'text':
                    init_sent = "detailed and enriched text for slide part\"" + description['description'] + "\". "
                elif description['type'] == 'table':
                    init_sent = "list of table cells for slide part\"" + description['description'] + "\" formatted in json as: cell row, cell coll, cell text. "
                elif description['type'] == 'plot':
                    init_sent = "list of data plots for slide part\"" + description['description'] + "\" formatted in json as: data name, array of data series. "
                elif description['type'] == 'chart':
                    init_sent = "list of data charts for slide part\"" + description['description'] + "\" formatted in json as: data name, data value. "
                elif description['type'] == 'image':
                    init_sent = "image description for slide part\"" + description['description'] + "\". "
                sent = init_sent + self.prompt
                description['prompt'] = sent
                slide_part_prompts.append(sent)
                descriptions.append(description)
            self.saveRespJson(request, descriptions)
            del chat
        else:
            self.task_creation_result += "Data from saved file:\n"
        
        for t in descriptions:
            self.task_creation_result += str(t) + '\n'


        for description in descriptions:
        #     ch_prompt = description + self.prompt
                self.addChildTask(TaskDescription( prompt= description['prompt'], method= RichTextTask, parent= self))


        # self.parent = parent
        # self.description = description
        # print("Init slide")
