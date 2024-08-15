import os
import shutil
import unittest
from create_project import create_project, count_created_files, linking_project, expected_files_count, advanced_branching

class TestCreateProject(unittest.TestCase):


    def setUp(self):
        # Set up the path where files are saved
        self.project_path = os.path.join('saved', 'project', 'test')
        self.config_path = 'config/'
        self.examples_config_path = 'examples/config/'

        # Clear all files and folders in 'saved' directory
        if os.path.exists('saved'):
            shutil.rmtree('saved')
        os.makedirs(self.project_path)

        # Check if 'config/' directory exists, if not, create it
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
            # Copy files from 'examples/config' to 'config'
            for filename in os.listdir(self.examples_config_path):
                source_file = os.path.join(self.examples_config_path, filename)
                shutil.copy(source_file, self.config_path)


    def test_create_files(self):
        # Run the project creation
        create_project()

        # Check if files are created in the saved directory
        file_count = count_created_files(self.project_path)
        self.assertEqual(file_count, expected_files_count(), "Expected 3 files to be created!")

        # Check for the creation of any .7z file in the ../../tt_temp directory
        temp_dir_path = os.path.join(self.project_path, '..', '..', 'tt_temp')
        seven_zip_files = [f for f in os.listdir(temp_dir_path) if f.endswith('.7z')]
        self.assertGreater(len(seven_zip_files), 0, "Expected at least one .7z file to be created in tt_temp directory!")


    def test_linking_project(self):
        # Call the linking_project function
        total_tasks, total_linked_tasks = linking_project()

        # Check the expected counts
        self.assertGreater(total_tasks, 0, "Expected some tasks to be created!")
        self.assertGreater(total_linked_tasks, 0, "Expected some linked tasks to be created!")


    def test_advanced_branching(self):
        # Call the advanced_branching function
        total_tasks, total_linked_tasks, branching_tasks_count = advanced_branching()

        # Check the expected counts
        self.assertGreater(total_tasks, 0, "Expected some tasks to be created!")
        self.assertGreater(total_linked_tasks, 0, "Expected some linked tasks to be created!")
        self.assertGreaterEqual(branching_tasks_count, 0, "Expected non-negative count for branching tasks!")


if __name__ == '__main__':
    unittest.main()



