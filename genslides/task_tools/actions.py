import genslides.task_tools.text as txt
import json

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

def getActionsFromPack( tparam ):
        if 'packs' in tparam and len(tparam['packs']):
                actions = tparam['packs'].pop()['actions']
                return True, actions, tparam
        return False, [], tparam

def createEmptyActionsPack():
        return {
                    "type": "autocommander",
                    "packs": []
                }


def updateActionsInPack(tparam, input_value):
        actions = json.loads(input_value, strict=False)
        packs = tparam['packs']
        hash = txt.compute_sha256_hash(json.dumps(actions))
        if len(packs) == 0:
                pack = {
                'hash': hash,
                'actions':actions
                }
                tparam['packs'].append(pack)

        else:
                for pack in packs:
                        if hash == pack['hash']:
                                return tparam
                pack = {
                'hash': hash,
                'actions':actions
                }
                tparam['packs'].append(pack)
        return tparam

