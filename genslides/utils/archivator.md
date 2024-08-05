# Main part
# Examples

The "Archivator_class" in the provided Python file is a class that contains methods for archiving files and extracting archived files using the py7zr library. Here are the primary features and functionalities of the Python file:

1. Archiving files: The class provides methods to archive files either individually or by archiving an entire directory. It uses the 7z format for compression.

2. Extracting files: The class includes a method to extract files from a 7z archive to a specified destination.

Here are some example use cases to demonstrate the key functionalities of the "Archivator_class":

**1. Archiving Individual Files:**
```python
from archivator import Archivator

src_path = "path/to/source/file.txt"
trg_path = "path/to/destination"
name = "archive"

Archivator.saveOnlyFiles(src_path, trg_path, name)
```
*This example demonstrates how to archive a single file "file.txt" from the source path to the destination path using the provided class.*

**2. Archiving Entire Directory:**
```python
from archivator import Archivator

src_path = "path/to/source/directory"
trg_path = "path/to/destination"
name = "archive"

Archivator.saveAll(src_path, trg_path, name)
```
*This example showcases archiving all files within a directory to a single archive file named "archive.7z" in the specified destination path.*

**3. Extracting Files from Archive:**
```python
from archivator import Archivator

trg_path = "path/to/archive"
filename = "archive"
path_to_extract = "path/to/extract"

Archivator.extractFiles(trg_path, filename, path_to_extract)
```
*In this example, the method is used to extract all files from the archive file "archive.7z" located in the target path to the specified extraction path.*

These examples provide a basic demonstration of the key functionalities of the "Archivator_class" in archiving and extracting files. By following the provided examples, users can effectively utilize the class to manage their file archiving needs.
Function: `extractFiles`

This function in the `Archivator` class is designed to extract all files from a specific 7z archive file to a specified path. The primary features and functionalities of this function include extracting files from a 7z archive and storing them in a specified directory.

Key functionalities highlighted in the examples:
1. Extract files from a 7z archive.
2. Specify the destination path for extracted files.

Example 1: Extract all files from a 7z archive to a specified path.
```python
from archivator import Archivator

trg_path = "path_to_archive_directory"
filename = "sample_archive"
path_to_extract = "path_to_extract_directory"

extract_result = Archivator.extractFiles(trg_path, filename, path_to_extract)
if extract_result:
    print("Files extracted successfully.")
else:
    print("Error: Archive file not found.")
```

Example 2: Handling non-existent archive file error.
```python
from archivator import Archivator

trg_path = "path_to_archive_directory"
filename = "non_existent_archive"
path_to_extract = "path_to_extract_directory"

extract_result = Archivator.extractFiles(trg_path, filename, path_to_extract)
if extract_result:
    print("Files extracted successfully.")
else:
    print("Error: Archive file not found.")
# Output: Error: Archive file not found.
```

Introduction:
The examples demonstrate how to use the `extractFiles` function to extract files from a 7z archive to a specified directory. The first example shows a successful extraction, while the second example handles the scenario where the archive file does not exist.

Expected Output:
Example 1: "Files extracted successfully."
Example 2: "Error: Archive file not found."

Troubleshooting:
If the extraction fails, ensure that the `trg_path` and `filename` variables point to the correct location and that the specified archive file exists. Check the `path_to_extract` directory for the extracted files.

By following the provided examples, users can effectively utilize the `extractFiles` function within the Archivator class for extracting files from 7z archives in Python. Your feedback is valuable for enhancing clarity and usefulness.
### Function: saveAll

#### Features and Functionalities:
- The `saveAll` function in the `Archivator` class creates a 7z archive file containing all files and folders in a specified source directory.
- It offers a convenient way to compress and store multiple files and folders in a single archive file.

#### Example 1: Saving all files and folders from a source directory

```python
from archivator import Archivator

# Define source and target paths
src_path = '/path/to/source_directory'
trg_path = '/path/to/target_directory'
name = 'my_archive'

# Save all files and folders from the source directory to a 7z archive
Archivator.saveAll(src_path, trg_path, name)
```

#### Expected Output:
- The function will create a 7z archive file in the target directory (`trg_path`) containing all files and folders from the source directory (`src_path`).

#### Example 2: Extracting files from a saved archive

```python
from archivator import Archivator

# Define target path and archive filename
trg_path = '/path/to/target_directory'
filename = 'my_archive'
path_to_extract = '/path/to/extracted_files'

# Extract all files from the saved archive to the specified extraction path
success = Archivator.extractFiles(trg_path, filename, path_to_extract)

if success:
    print("Extraction successful!")
else:
    print("Archive not found.")
```

#### Expected Output:
- The function will extract all files and folders from the specified archive file (`filename`) in the target directory (`trg_path`) to the extraction path (`path_to_extract`).
- If the archive is found and extraction is successful, it will print "Extraction successful!" Otherwise, it will print "Archive not found."

#### Troubleshooting Tips:
- Ensure that the paths provided in the examples are valid and accessible in your file system.
- Verify that the source directory for saving files (`src_path`) contains files and folders to archive.
- Check for any potential errors or exceptions raised during the archive creation or extraction process and handle them accordingly.
The `saveOnlyFiles` function in the provided Python file is designed to create a 7z archive by compressing only the files present in a specified source directory. Let's demonstrate the usage of this function with simple and advanced examples:

### Example 1: Simple Usage
This example illustrates how to create a 7z archive including all files from a specific source directory.

```python
from archivator import Archivator

src_path = "/path/to/source_directory"
trg_path = "/path/to/target_directory"
archive_name = "archive_with_files"

Archivator.saveOnlyFiles(src_path, trg_path, archive_name)
```

**Expected Output:**
- The function will create a 7z archive named `archive_with_files.7z` in the target directory (`trg_path`), containing all files from the specified source directory (`src_path`).

### Example 2: Advanced Usage
In this example, we demonstrate appending additional files to an existing 7z archive.

```python
from archivator import Archivator

src_path = "/path/to/source_directory"
trg_path = "/path/to/target_directory"
archive_name = "existing_archive"

# Create an initial archive with the first set of files
Archivator.saveOnlyFiles(src_path, trg_path, archive_name)

# Append new files to the existing archive
new_files_path = "/path/to/additional_files_directory"
Archivator.saveOnlyFiles(new_files_path, trg_path, archive_name)
```

**Expected Output:**
- The function will add the new files from `new_files_path` to the existing 7z archive named `existing_archive.7z` in the target directory (`trg_path`).

### Troubleshooting:
- Make sure the paths (`src_path`, `trg_path`, `new_files_path`) provided are valid directories.
- Check the file permissions for both source and target directories to ensure write access.
- Verify that the 7z library (py7zr) is installed in the Python environment.

These examples demonstrate the primary functionality of the `saveOnlyFiles` method, showcasing how to create 7z archives selectively with files from specified directories. Users can further explore additional features and settings as needed for their specific archiving requirements.
- **Brief Description:** The `Archivator` class provides methods for creating, updating, and extracting files from 7z compressed archives.

- **Methods:**

1. **saveOnlyFiles:**
   - **Parameters (`Args`):**
     - `src_path` (str): The path to the directory containing the files to be archived.
     - `trg_path` (str): The path to the directory where the archive will be saved.
     - `name` (str): The name of the archive.
   - **Returns:** None
   - **Raises:** None
   - **Examples:**
     ```python
     Archivator.saveOnlyFiles("source_directory", "target_directory", "archive_name")
     ```
   - **Notes or Warnings (Optional):** This method creates a new 7z archive and adds only the files from the specified source directory.

2. **saveAll:**
   - **Parameters (`Args`):**
     - `src_path` (str): The path to the directory containing all files and subdirectories to be archived.
     - `trg_path` (str): The path to the directory where the archive will be saved.
     - `name` (str): The name of the archive.
   - **Returns:** None
   - **Raises:** None
   - **Examples:**
     ```python
     Archivator.saveAll("source_directory", "target_directory", "archive_name")
     ```
   - **Notes or Warnings (Optional):** This method creates a new 7z archive and adds all files and subdirectories from the specified source directory.

3. **extractFiles:**
   - **Parameters (`Args`):**
     - `trg_path` (str): The path to the directory where the archive is located.
     - `filename` (str): The name of the archive file (without the extension).
     - `path_to_extract` (str): The path to extract the files from the archive.
   - **Returns:** bool (True if extraction successful, False otherwise)
   - **Raises:** None
   - **Examples:**
     ```python
     Archivator.extractFiles("target_directory", "archive_name", "extract_directory")
     ```
   - **Notes or Warnings (Optional):** This method extracts all files from the specified 7z archive to the specified extraction directory.
```python
# Function: extractFiles

# Brief Description:
# Extracts all files from a 7z archive file to a specified path.

# Parameters (Args):
#     trg_path (str): The path where the 7z archive file is located.
#     filename (str): The name of the 7z archive file to extract from.
#     path_to_extract (str): The path where the files will be extracted to.

# Returns:
#     bool: True if the extraction was successful, False otherwise.

# Raises:
#     NoFileError: Raised when the specified file does not exist in the target path.

# Examples:
#     extractFiles("C:/Downloads", "data", "C:/ExtractedFiles")
#     # Extracts all files from "C:/Downloads/data.7z" to "C:/ExtractedFiles"

# Notes or Warnings:
#     - Make sure to provide the correct paths and filenames for extraction.
#     - This function requires the py7zr library to be installed.
```
### `saveAll`

- **Brief Description:** This function creates a 7z archive file containing either all the files in a source directory or all the contents within the source directory, including subdirectories.

- **Parameters (`Args`):**
    - `src_path` (string): The path of the source directory to be archived.
    - `trg_path` (string): The target directory path where the archive file will be saved.
    - `name` (string): The name of the output archive file.

- **Returns:** None

- **Raises:** None

- **Examples:**
    ```python
    Archivator.saveAll('source_directory', 'target_directory', 'archive_name')
    ```

- **Notes or Warnings:**
    - This function will create a new 7z archive file or append to an existing one in the target directory.
    - The function can handle both files and directories, archiving all items in the source directory.

- **Other Sections (Optional):** N/A
### Function: `saveOnlyFiles`

- **Brief Description:**
  This function archives only the files from a specified source path to a target path in a .7z format.

- **Parameters (`Args`):**
  1. `src_path` (str): The path of the source directory containing files to be archived.
  2. `trg_path` (str): The target directory where the archive (.7z) file will be saved.
  3. `name` (str): The name of the archive file to be created.

- **Returns:**
  This function does not return any value.

- **Raises:**
  No specific exceptions are handled within this function.

- **Examples:**
  ```python
  Archivator.saveOnlyFiles("source_path", "target_path", "archive_name")
  ```
  - This will create a .7z archive file in the `target_path` containing all files from the `source_path` directory.

- **Notes or Warnings:**
  - This function archives only the files from the source directory; subdirectories are not included in the archive.
  - Ensure that the source and target paths are valid and have appropriate permissions for file operations.

- **Other Sections:**
  - It's recommended to validate the paths and permissions before calling this function to avoid any runtime errors related to file operations.

# Recomendations
##Recommendations for function

Archivator_class


In the updated `Archivator` class, comments have been added to explain the purpose of the code and provide clarity on certain aspects. Here is the revised code with explanatory comments:

```python
from typing import List
import py7zr
import os
from os import listdir
from os.path import isfile, join

class Archivator:
    """
    This class provides methods for archiving and extracting files using 7z compression.

    Key functions:
    - saveOnlyFiles: Archive only files from a source directory.
    - saveAll: Archive all files and folders from a source directory.
    - extractFiles: Extract files from a 7z archive.

    Dependencies: py7zr

    Usage Example:
    from archivator import Archivator

    # Archive only files from source_path to target_path with name "archive"
    Archivator.saveOnlyFiles("source_path", "target_path", "archive")
    """

    @staticmethod
    def saveOnlyFiles(src_path: str, trg_path: str, name: str) -> None:
        """
        Archives only files from a source directory.

        Parameters:
        - src_path (str): Path to the source directory.
        - trg_path (str): Path to the target directory.
        - name (str): Name of the archive file.

        Returns:
        None
        """
        onlyfiles: List[str] = [f for f in listdir(src_path) if isfile(join(src_path, f))]  # Get only files from the source directory
        first: bool = True  # Flag to check if it's the first file being archived
        res_trg_path: str = join(trg_path, name + ".7z")  # Path for the target archive file
        for file in onlyfiles:
            res_src_path: str = join(src_path, file)
            if first:
                with py7zr.SevenZipFile(res_trg_path, 'w') as archive:
                    print('Write', res_src_path, 'to', res_trg_path)
                    archive.write(res_src_path, arcname=file)  # Write the first file to the archive
                first = False
            else:
                with py7zr.SevenZipFile(res_trg_path, 'a') as archive:
                    print('Append', res_src_path, 'to', res_trg_path)
                    archive.write(res_src_path, arcname=file)  # Append subsequent files to the archive

    @staticmethod
    def saveAll(src_path: str, trg_path: str, name: str) -> None:
        """
        Archives all files and folders from a source directory.

        Parameters:
        - src_path (str): Path to the source directory.
        - trg_path (str): Path to the target directory.
        - name (str): Name of the archive file.

        Returns:
        None
        """
        res_trg_path: str = join(trg_path, name + ".7z")  # Path for the target archive file
        with py7zr.SevenZipFile(res_trg_path, 'w') as archive:
            print('Write', src_path, 'to', res_trg_path)
            archive.writeall(src_path, arcname='')  # Write all files and folders from the source directory to the archive

    @staticmethod
    def extractFiles(trg_path: str, filename: str, path_to_extract: str) -> bool:
        """
        Extracts files from a 7z archive.

        Parameters:
        - trg_path (str): Path to the 7z archive directory.
        - filename (str): Name of the 7z archive file.
        - path_to_extract (str): Path to extract the files.

        Returns:
        bool: True if extraction is successful, False otherwise.
        """
        onlyfiles: List[str] = [f for f in listdir(trg_path) if isfile(join(trg_path, f)]]
        if filename + ".7z" not in onlyfiles:
            return False  # If the specified 7z archive file is not found, return False
        with py7zr.SevenZipFile(join(trg_path, filename + ".7z"), 'r') as archive:
            print('Extract all from', trg_path, filename, 'to', path_to_extract)
            archive.extractall(path=path_to_extract)  # Extract all files from the specified 7z archive
        return True  # Return True if the extraction is successful
```

By incorporating comments as explained above, the code becomes more informative and easier to understand for developers working with or reviewing the `Archivator` class.

##Recommendations for function

extractFiles


```python
from typing import List
import py7zr
import os
from os import listdir
from os.path import isfile, join

def extractFiles(trg_path: str, filename: str, path_to_extract: str) -> bool:
    """Extract files from a 7z archive.
    
    This function extracts files from a 7z archive located in `trg_path` under the provided `filename`.
    
    Args:
        trg_path (str): The path to the directory containing the 7z archive.
        filename (str): The name of the 7z archive file (without the extension).
        path_to_extract (str): The path to extract the contents of the 7z archive.
        
    Returns:
        bool: True if extraction was successful, False otherwise.
        
    Example:
        extractFiles("/path/to/archive", "example_archive", "/path/to/extract")
    """
    
    # Get the list of files in the target directory
    onlyfiles: List[str] = [f for f in listdir(trg_path) if isfile(join(trg_path, f))]
    
    # Check if the specified 7z archive file exists in the directory
    if filename + ".7z" not in onlyfiles:
        return False
    
    # Extract the files from the 7z archive
    with py7zr.SevenZipFile(join(trg_path, filename + ".7z"), 'r') as archive:
        print('Extract all from', trg_path, filename, 'to', path_to_extract)
        archive.extractall(path=path_to_extract)
    
    return True
```

##Recommendations for function

saveAll


```python
from typing import NoReturn

class Archivator:
    @staticmethod
    def saveAll(src_path: str, trg_path: str, name: str) -> NoReturn:
        """
        Archive all files from the source directory to the target directory with the given name.

        This method is necessary to create a compressed archive of all files present in the specified source directory.

        Parameters:
        - src_path (str): The path to the source directory.
        - trg_path (str): The path to the target directory.
        - name (str): The name of the archive file.

        Returns:
        NoReturn: This function does not return anything.
        """
        # The following code compresses all files from src_path into trg_path with the given name
        pass  # Actual implementation code to follow
```

By explaining the purpose and necessity of the code in the docstring as well as commenting, you provide context for why the `saveAll` function is needed. This helps developers understand the rationale behind the code and its specific role in the overall functionality of the module.

##Recommendations for function

saveOnlyFiles


```python
from typing import List
from os.path import join

class Archivator():
    """
    This class provides functions for archiving files using the 7z format.
    
    Key functions:
    - saveOnlyFiles: Archives only files from a source directory to a target directory.
    
    External dependencies: py7zr
    
    Usage example:
    archiver = Archivator()
    archiver.saveOnlyFiles('source_directory', 'target_directory', 'archive_name')
    """

    @staticmethod
    def saveOnlyFiles(src_path: str, trg_path: str, name: str) -> None:
        """
        Archives only files from the source directory to the target directory.
        
        Parameters:
        - src_path: The path to the source directory containing files to archive.
        - trg_path: The path to the target directory where the archive will be saved.
        - name: The name of the archive file.
        """
        
        # Get a list of only files (excluding directories) in the source directory
        onlyfiles: List[str] = [f for f in listdir(src_path) if isfile(join(src_path, f)]
        
        first: bool = True
        res_trg_path: str = join(trg_path, name + ".7z")
        
        for file in onlyfiles:
            res_src_path: str = join(src_path, file)
            
            # If it's the first file, create a new archive and write the file
            if first:
                with py7zr.SevenZipFile(res_trg_path, 'w') as archive:
                    print('write', res_src_path, 'to', res_trg_path)
                    archive.write(res_src_path, arcname=file)
                first = False
            # For subsequent files, append them to the existing archive
            else:
                with py7zr.SevenZipFile(res_trg_path, 'a') as archive:
                    print('append', res_src_path, 'to', res_trg_path)
                    archive.write(res_src_path, arcname=file)
```

In the updated `saveOnlyFiles` function, comments are used to explain the purpose of each key section of the code, such as obtaining a list of files, creating a new archive for the first file, and appending to an existing archive for subsequent files. By providing these comments, the code becomes more manageable and easier to understand for developers reviewing the implementation.


