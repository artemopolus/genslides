# genslides/test/create_project.py

import os
import genslides.commanager.group as Actioner
import genslides.commanager.sen as Projecter

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher

project_path = 'saved/'


def create_task(StdProjecter : Projecter.Projecter, prompt : str, role : str, task_type = 'Request', custom_action = 'SetOptions', action_type='SubTask', edit_cmd = []):
    # Get initial tasks count
    old_tasks = StdProjecter.actioner.manager.getTasks()
    if task_type == 'Request':
        # Create Request Task
        StdProjecter.makeRequestAction(prompt, action_type, role, edit_cmd)
    elif task_type == 'Response':
        # Create Response Task
        StdProjecter.makeResponseAction('', action_type, 'assistant',edit_cmd)
    elif task_type == 'Custom':
        # Create Custom Task with special configuration
        StdProjecter.makeCustomAction(prompt, action_type, custom_action)
    else:
        return None
    # Get current task count
    tasks = StdProjecter.actioner.manager.getTasks()
    created = None
    # Find created task count
    for task in tasks:
        if task not in old_tasks:
            created = task
    return created

def create_project():
    # Create Manager
    StdManager = Actioner.Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
    # Create projecter to manipulate Manager via Actioner
    StdProjecter = Projecter.Projecter(StdManager)
    # Load task from location
    StdProjecter.loadActionerByPath(project_path)
    mercury_task = create_task(StdProjecter, 'Mercury', 'user')
    venus_task = create_task(StdProjecter, 'Venus', 'user')
    earth_task = create_task(StdProjecter, 'Earth', 'user')
    mars_task = create_task(StdProjecter, 'Mars', 'user')
    jupiter_task = create_task(StdProjecter, 'Jupiter','user')

def edit_task(StdProjecter : Projecter.Projecter, prompt : str, role : str, edit_cmd = []) -> list[Projecter.BaseTask]:
    created = []
    old_tasks = StdProjecter.actioner.manager.getTasks()

    StdProjecter.makeRequestAction(prompt, "Edit", role, edit_cmd)

    tasks = StdProjecter.actioner.manager.getTasks()
    for task in tasks:
        if task not in old_tasks:
            created.append(task)
    return created

def get_task_raw_prompt(task : Projecter.BaseTask):
    return task.getLastMsgContentRaw()


def linking_project():
    StdManager = Actioner.Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
    StdProjecter = Projecter.Projecter(StdManager)

    StdProjecter.loadActionerByPath(project_path)
    mercury_task = create_task(StdProjecter, 'Mercury', 'user')
    venus_task = create_task(StdProjecter, 'Venus', 'user')
    earth_task = create_task(StdProjecter, 'Earth', 'user')
    mars_task = create_task(StdProjecter, 'Mars', 'user')
    jupiter_task = create_task(StdProjecter, 'Jupiter','user')

    # Set Task to Current Task of Actioner Current Manager
    StdProjecter.actioner.manager.setCurrentTask(mars_task)

    # Select Current Task
    StdProjecter.addCurrTaskToSelectList()

    rover_link_tree = create_task(StdProjecter, '','user', task_type='Custom', custom_action='SetOptions')

    # Create Collect Task
    StdProjecter.createCollectTreeOnSelectedTasks('SubTask')

    tasks = StdProjecter.actioner.manager.getTasks()

    linked_count = 0
    # How many tasks is linked?
    for task in tasks:
        if len(task.getGarlandPart()) > 0:
            linked_count += 1
    return len(tasks), linked_count

def advanced_branching():
    StdManager = Actioner.Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
    StdProjecter = Projecter.Projecter(StdManager)

    StdProjecter.loadActionerByPath(project_path)
    mercury_task = create_task(StdProjecter, 'Mercury', 'user')
    venus_task = create_task(StdProjecter, 'Venus', 'user')
    earth_task = create_task(StdProjecter, 'Earth', 'user')
    mars_task = create_task(StdProjecter, 'Mars', 'user')
    jupiter_task = create_task(StdProjecter, 'Jupiter','user')

    # Set Task to Current Task of Actioner Current Manager
    StdProjecter.actioner.manager.setCurrentTask(mars_task)

    # Select Current Task
    StdProjecter.addCurrTaskToSelectList()

    rover_link_tree = create_task(StdProjecter, '','user', task_type='Custom', custom_action='SetOptions', action_type='New')

    # Create Collect Task
    StdProjecter.createCollectTreeOnSelectedTasks('SubTask')

    mars3_task = create_task(StdProjecter, 'Mars 3','user')
    sojourner_task = create_task(StdProjecter, 'Sojourner','user')
    
    StdProjecter.actioner.manager.setCurrentTask(mars_task)

    branching_tasks_list = edit_task(StdProjecter, "Moon", 'user', ['copy_editbranch','in','out','link'])
    for task in branching_tasks_list:
        if not task.checkType('SetOptions'):
            if get_task_raw_prompt(task) == 'Mars 3':
                StdProjecter.actioner.manager.setCurrentTask(task)
                edit_task(StdProjecter,"Luna-17",'user')
            elif get_task_raw_prompt(task) == 'Sojourner':
                StdProjecter.actioner.manager.setCurrentTask(task)
                edit_task(StdProjecter,"Moon Rover-001",'user')


    StdProjecter.updateAll()


    tasks = StdProjecter.actioner.manager.getTasks()
    
    print('Tasks:', len(tasks))

    idx = 0
    for task in tasks:
        if len(task.getChilds()) == 0:
            branch = task.getAllParents()
            print('Branch',idx,':')
            idx += 1
            for t in branch:
                if not t.checkType('SetOptions'):
                    print (t.getName(),':', get_task_raw_prompt(t))
                else:
                    print (t.getName())


    linked_count = 0
    # How many tasks is linked?
    for task in tasks:
        if len(task.getGarlandPart()) > 0:
            linked_count += 1
    return len(tasks), linked_count, len(branching_tasks_list)

def expected_files_count():
    return 7

def count_created_files(path):
    return len(os.listdir(path))

if __name__ == "__main__":
    create_project()

