import json
import os
from tree_sitter import Language, Parser
import tree_sitter_cpp as tspython
import genslides.task_tools.py_parser as pyparser
import genslides.task_tools.text as TextTool
from pypdf import PdfReader

class DefaultConvertor:
    def __init__(self):
        self.parameters = {
            "suffix":"_dflt"
        }

    def createFileHeader(self, source_path : str, targets : list):
        return {
            "filename": os.path.basename(source_path),
            "path": source_path,
            "version": "0.1",
            "description":"Json File for genslides app",
            "targets": targets
        }
    
    def createTargetPack( self, part_name : str, part_body : str, ttype = "method", parent_target = "None" ):
        return {
                    "type": ttype,
                    "parent_target": parent_target,
                    "name": part_name,
                    "body": part_body
                }


    def process_file( self, file_path, output_dir):
        return {"result": False, "report":" File default convertor run"}

    def process_directory(self,input_dir, output_dir):
        return {"result": False, "report":" Directory default convertor run"}
    
    def get_new_genslides_path( self, file_path, ext = ".json" ):
        output_dir = os.path.dirname( file_path )
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_extension = self.parameters.get("suffix","_unknwn") + ext
        return os.path.join(output_dir, f"{base_name}{output_extension}")
 
    
    def get_genslides_jsonproject_path (self,file_path):
        return self.get_new_genslides_path( file_path, ".json")
    
    def check_extension (self, file_path ):
        return False
    
    def check_generated_genslides_json (self, file_path):
        return os.path.exists( self.get_genslides_jsonproject_path( file_path ) )

    def check_genslides_archive (self, file_path):
        return os.path.exists( self.get_genslides_archive_path( file_path ) )
    
    def get_genslides_archive_path(self, file_path ):
        return self.get_new_genslides_path( file_path, ".7z")


class CppConvertor(DefaultConvertor):
    def get_function_definitions(self,node):
        function_defs = []
        if node.type == 'function_definition':
            declarator_node = node.child_by_field_name('declarator')
            if declarator_node:
                for child in declarator_node.children:
                    if child.type == 'identifier':
                        function_defs.append(child.text.decode())
                    elif child.type == 'qualified_identifier':
                        function_defs.append(child.text.decode())

        for child in node.children:
            function_defs.extend(self.get_function_definitions(child))

        return function_defs

    def auxiliary_check_node_structure(self,node, structure):
        """
        Recursively checks if a node matches a given hierarchical structure.

        Args:
            node: The Tree-sitter node to check.
            structure (list): A list defining the hierarchical structure. 
                            Each element is a dictionary with a "type" key 
                            and optional "children" key.

        Returns:
            bool: True if the node matches the structure, False otherwise.
        """
        if not isinstance(structure, list):  # Base case: single node structure
            return node.type == structure["type"]

        if node.type != structure[0]["type"]:
            return False

        if "children" in structure[0]:
            for child_structure in structure[0]["children"]:
                found_match = False
                for child_node in node.children:
                    if self.auxiliary_check_node_structure(child_node, [child_structure]):
                        found_match = True
                        break
                if not found_match:
                    return False
        return True

    def extract_header_definitions(self,node, search_structure=None, output_structure=None):
        """
        Extracts information from a Tree-sitter parse tree based on search and output structures.
        """
        if search_structure is None:
            search_structure = [{"type": "function_definition", "children": [{"type": "identifier"}]}]

        if output_structure is None:
            output_structure = ["type", "declarator"]

        function_defs = []

        if self.auxiliary_check_node_structure(node, search_structure):
            output_parts = []
            separator = " "

            if isinstance(output_structure, dict):
                output_fields = output_structure.get("fields", [])
                separator = output_structure.get("separator", " ")
            else:
                output_fields = output_structure

            for field_name in output_fields:
                if field_name == "get_all_node_child_types":  # Special handling for child types
                    child_types = [child.type for child in node.children]
                    output_parts.append(", ".join(child_types))
                elif field_name == "get_node_full_text":  # Special handling for full node text
                    output_parts.append(node.text.decode())
                else:  # Handle regular field names
                    child = node.child_by_field_name(field_name)
                    if child:
                        output_parts.append(child.text.decode())

            # Get nested node text
            nested_node_text = []
            for child in node.children:
                nested_node_text.append(child.text.decode())

            # Construct the dictionary with the required output format
            function_defs.append({ 
                "type":"method",
                "parent_target": "None",
                "name": separator.join(output_parts),
                "body": separator.join(output_parts + nested_node_text)
            })

        for child in node.children:
            function_defs.extend(self.extract_header_definitions(child, search_structure, output_structure))

        return function_defs

    def get_function_info(self,node, function_name):
        result = None

        if node.type == 'function_definition':
            declarator_node = node.child_by_field_name('declarator')
            if declarator_node:
                declarator_text = declarator_node.text.decode()
                # Check if the function name is followed by a space or a bracket
                if declarator_text.startswith(function_name + ' ') or declarator_text.startswith(function_name + '('):
                    type_node = node.child_by_field_name('type')
                    type_text = type_node.text.decode().strip() if type_node else ""

                    body_node = node.child_by_field_name('body')
                    body_text = body_node.text.decode().strip() if body_node else ""

                    # Format the result as type, declarator, and body
                    result = f"{type_text} {declarator_text}\n{body_text}"

        # Recursively search child nodes
        for child in node.children:
            child_result = self.get_function_info(child, function_name)
            if child_result:
                return child_result  # Return immediately if a match is found

        return result  # Return the result of the target function

    def extract_function_info(self,root_node, code_path):
        function_names = self.get_function_definitions(root_node)

        # Prepare the output data structure
        targets = []

        # Get function information for each function name
        for function_name in function_names:
            function_info = self.get_function_info(root_node, function_name)
            if function_info:
                targets.append({
                    "type":"method",
                    "parent_target": "None",
                    "name": function_name,
                    "body": function_info
                })

        # Create the final JSON structure
        return {
            "filename": os.path.basename(code_path),
            "path": code_path,
            "version": "0.1",
            "description":"Json File for genslides app",
            "targets": targets
        }

    def process_file(self,file_path, output_dir):
        LANGUAGE = Language(tspython.language())
        ts_parser = Parser(LANGUAGE)
        output = {}
        output["result"] = True

        # Load and parse the C++ source code
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
        except (FileNotFoundError, UnicodeDecodeError) as e:
            print(f"Error reading file {file_path}: {e}")
            output["result"] = False
            return output

        tree = ts_parser.parse(bytes(code, "utf-8"))
        root_node = tree.root_node

        # Determine if the file is a header file and extract accordingly
        if file_path.endswith((".h", ".hpp")):
            json_data = {
                "filename": os.path.basename(file_path),
                "path": file_path,
                "version": "0.1",
                "description":"Json File for genslides app",
                "targets": self.extract_header_definitions(root_node)
            }
        else:
            json_data = self.extract_function_info(root_node, file_path)

        # Construct output file path
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_extension = "_h.json" if ext == ".h" else "_hpp.json" if ext == ".hpp" else "_cpp.json"
        output_file_path = os.path.join(output_dir, f"{base_name}{output_extension}")

        # Write the output to a JSON file
        try:
            with open(output_file_path, "w", encoding="utf-8") as json_file:
                json.dump(json_data, json_file, indent=4)
        except IOError as e:
            print(f"Error writing to file {output_file_path}: {e}")
            output["result"] = False
            return output
        return output 

    def process_directory(self,input_dir, output_dir):
        for entry in os.scandir(input_dir):
            if entry.is_file() and entry.name.endswith((".cpp", ".h", ".hpp")):
                self.process_file(entry.path, output_dir)
            elif entry.is_dir():
                relative_path = os.path.relpath(entry.path, start=input_dir)
                output_subdir = os.path.join(output_dir, relative_path)
                os.makedirs(output_subdir, exist_ok=True)
                self.process_directory(entry.path, output_subdir)
        return {"result": True, "report":"Process directory using cpp"}
    
    def get_genslides_jsonproject_path (self,file_path):
        output_dir = os.path.dirname( file_path )
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_extension = "_h.json" if ext == ".h" else "_hpp.json" if ext == ".hpp" else "_cpp.json"
        return os.path.join(output_dir, f"{base_name}{output_extension}")
    
    def check_extension(self,file_path):
        return True
    
    def check_generated_genslides_json(self,file_path):
        target_path = self.get_genslides_jsonproject_path(file_path)
        return os.path.exists( target_path )
    
    def get_genslides_archive_path(self,file_path):
        output_dir = os.path.dirname( file_path )
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_extension = "_h_gs.7z" if ext == ".h" else "_hpp_gs.7z" if ext == ".hpp" else "_cpp_gs.7z"
        return  os.path.join(output_dir, f"{base_name}{output_extension}")
    
    def check_genslides_archive(self,file_path):
        return os.path.exists( self.get_genslides_archive_path( file_path ) )

class PyConverter(DefaultConvertor):
    def process_file(self,file_path, output_dir):
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_extension = "_py.json"
        output_file_path = os.path.join(output_dir, f"{base_name}{output_extension}")
        return pyparser.convert_genslide_json_file( file_path, output_file_path)
    
    def get_genslides_jsonproject_path (self,file_path):
        output_dir = os.path.dirname( file_path )
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_extension = "_py.json"
        return os.path.join(output_dir, f"{base_name}{output_extension}")
    
    def get_genslides_archive_path(self,file_path):
        output_dir = os.path.dirname( file_path )
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_extension = "_py.7z"
        return os.path.join(output_dir, f"{base_name}{output_extension}")
    
    def check_genslides_archive(self,file_path):
        return os.path.exists( self.get_genslides_archive_path( file_path ) )
 
    def check_extension(self,file_path):
        return True
    
    def check_generated_genslides_json(self,file_path):
        target_path = self.get_genslides_jsonproject_path(file_path)
        return os.path.exists( target_path )

class TxtConverter(DefaultConvertor):
    def __init__(self):
        super().__init__()
        self.parameters["suffix"] = "_txt"

    def process_file(self, file_path, output_dir):
        parts_count_on = self.parameters.get("parts_count_on", False)
        smbl_before = self.parameters.get("smbl_before", 100)
        smbl_after = self.parameters.get("smbl_after",100)
        output = {}
        output["result"] = True

        # Load and parse the C++ source code
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = f.read()
        except (FileNotFoundError, UnicodeDecodeError) as e:
            print(f"Error reading file {file_path}: {e}")
            output["result"] = False
            return output
        cuts = []
        parts = []

        if parts_count_on:
            parts_count = self.parameters.get("parts_target_count", 10)
            cuts = TextTool.cut_text_into_parts(data, parts_count,smbl_before, smbl_after)
        else:
            part_smbl_cnt = self.parameters.get("part_smbl_cnt", 2000)
            cuts = TextTool.split_text_with_context(data, part_smbl_cnt,smbl_before, smbl_after)
        
        for cut in cuts:
            pack = cut.get("Result Text","")
            parts.append(self.createTargetPack("", pack))

        json_data = self.createFileHeader(file_path, parts)
        
        output_file_path = self.get_genslides_jsonproject_path( file_path )
        try:
            with open(output_file_path, "w", encoding="utf-8") as json_file:
                json.dump(json_data, json_file, indent=4)
        except IOError as e:
            print(f"Error writing to file {output_file_path}: {e}")
            output["result"] = False
            return output
        return output 
    
    def check_extension(self, file_path):
        return True
    
class PdfConverter(DefaultConvertor):
    def __init__(self):
        super().__init__()
        self.parameters["suffix"] = "_pdf"

    def process_file(self, file_path, output_dir):
        output = {}
        parts = []
        output["result"] = True

        reader = PdfReader(file_path)
        for page in reader.pages:
            text = page.extract_text()
            if isinstance( text, str):
                parts.append(self.createTargetPack("", text))

        json_data = self.createFileHeader(file_path, parts)
        
        output_file_path = self.get_genslides_jsonproject_path( file_path )
        try:
            with open(output_file_path, "w", encoding="utf-8") as json_file:
                json.dump(json_data, json_file, indent=4)
        except IOError as e:
            print(f"Error writing to file {output_file_path}: {e}")
            output["result"] = False
            return output
        return output 

    def check_extension(self, file_path):
        return True
 
 
CONVERTERS = {
    ".pdf": PdfConverter,
    ".tex": TxtConverter,
    ".txt": TxtConverter,
    ".h":   CppConvertor,
    ".hpp":   CppConvertor,
    ".c":   CppConvertor,
    ".cpp": CppConvertor,
    ".py":  PyConverter,
}

def get_converter(file_path) -> DefaultConvertor:
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in CONVERTERS:
        return DefaultConvertor

    return CONVERTERS[ext]()

def convertFileToGenslidesJson( filepath ):
    converter = get_converter( filepath )
    output_dir = os.path.dirname( filepath )
    return converter.process_file( filepath, output_dir )

def getConvertedGenslidesJsonName ( filepath ):
    converter = get_converter( filepath )
    return converter.get_genslides_jsonproject_path( filepath )

def checkExistOfGenslidesJsonFile( filepath ):
    converter = get_converter( filepath )
    return converter.check_generated_genslides_json( filepath )

def checkExtensionOfFile( filepath ):
    converter = get_converter( filepath )
    return converter.check_extension( filepath )

def checkExistOfGenslidesArchiveFile( filepath ):
    converter = get_converter( filepath )
    return converter.check_genslides_archive( filepath )

def getGenslidesArchiveFilePath( filepath ):
    converter = get_converter( filepath )
    return converter.get_genslides_archive_path( filepath )
