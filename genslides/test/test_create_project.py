# genslides/test/test_create_project.py

import os
import unittest
from create_project import create_project, count_created_files

class TestCreateProject(unittest.TestCase):
    
    def setUp(self):
        # Set up the path where files are saved
        self.project_path = 'saved/'
        if os.path.exists(self.project_path):
            for f in os.listdir(self.project_path):
                os.remove(os.path.join(self.project_path, f))
        else:
            os.makedirs(self.project_path)

    def test_create_files(self):
        # Run the project creation
        create_project()

        # Check if files are created
        file_count = count_created_files(self.project_path)
        self.assertEqual(file_count, 3, "Expected 3 files to be created!")

if __name__ == '__main__':
    unittest.main()

    