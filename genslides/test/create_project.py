# genslides/test/create_project.py

import os
import genslides.commanager.group as Actioner
import genslides.commanager.sen as Projecter

from genslides.utils.reqhelper import RequestHelper
from genslides.utils.testrequest import TestRequester
from genslides.utils.searcher import GoogleApiSearcher

project_path = 'saved/'

def create_project():
    StdManager = Actioner.Manager.Manager(RequestHelper(), TestRequester(), GoogleApiSearcher())
    StdProjecter = Projecter.Projecter(StdManager)

    StdProjecter.loadActionerByPath(project_path)
    StdProjecter.makeRequestAction('Test', 'SubTask', 'User', [])

def count_created_files(path):
    return len(os.listdir(path))

if __name__ == "__main__":
    create_project()

