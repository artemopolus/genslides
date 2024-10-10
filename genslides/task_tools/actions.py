
def createActionPack( id = 0, action = '', prompt = '',
                      tag = '', act_type = '', param = {},
                      current_task_name = '', selected_task_name = '', multi_task_names = []
                      ):
        pack = {'id': id,'action':action,'prompt':prompt,
                'tag':tag,
                'type':act_type,
                'param': param }

        pack['current'] = current_task_name
        pack['slct'] = selected_task_name
        pack['multi'] = multi_task_names
        return pack


def updateActionPackByMethod(pack, method):
    pack['prompt'] = method(pack['prompt'])
    return pack
