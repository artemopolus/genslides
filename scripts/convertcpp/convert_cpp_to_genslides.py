import argparse
import json
import os
from tree_sitter import Language, Parser
import tree_sitter_cpp as tspython

def get_function_definitions(node):
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
        function_defs.extend(get_function_definitions(child))

    return function_defs

def auxiliary_check_node_structure(node, structure):
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
                if auxiliary_check_node_structure(child_node, [child_structure]):
                    found_match = True
                    break
            if not found_match:
                return False
    return True

def extract_header_definitions(node, search_structure=None, output_structure=None):
    """
    Extracts information from a Tree-sitter parse tree based on search and output structures.
    """
    if search_structure is None:
        search_structure = [{"type": "function_definition", "children": [{"type": "identifier"}]}]

    if output_structure is None:
        output_structure = ["type", "declarator"]

    function_defs = []

    if auxiliary_check_node_structure(node, search_structure):
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
            "function_name": separator.join(output_parts),
            "function_info": separator.join(output_parts + nested_node_text)
        })

    for child in node.children:
        function_defs.extend(extract_header_definitions(child, search_structure, output_structure))

    return function_defs

def get_function_info(node, function_name):
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
        child_result = get_function_info(child, function_name)
        if child_result:
            return child_result  # Return immediately if a match is found

    return result  # Return the result of the target function

def extract_function_info(root_node, code_path):
    function_names = get_function_definitions(root_node)

    # Prepare the output data structure
    targets = []

    # Get function information for each function name
    for function_name in function_names:
        function_info = get_function_info(root_node, function_name)
        if function_info:
            targets.append({
                "function_name": function_name,
                "function_info": function_info
            })

    # Create the final JSON structure
    return {
        "filename": os.path.basename(code_path),
        "path": code_path,
        "targets": targets
    }

def process_file(file_path, output_dir):
    LANGUAGE = Language(tspython.language())
    ts_parser = Parser(LANGUAGE)

    # Load and parse the C++ source code
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
    except (FileNotFoundError, UnicodeDecodeError) as e:
        print(f"Error reading file {file_path}: {e}")
        return

    tree = ts_parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    # Determine if the file is a header file and extract accordingly
    if file_path.endswith((".h", ".hpp")):
        json_data = {
            "filename": os.path.basename(file_path),
            "path": file_path,
            "targets": extract_header_definitions(root_node)
        }
    else:
        json_data = extract_function_info(root_node, file_path)

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

def process_directory(input_dir, output_dir):
    for entry in os.scandir(input_dir):
        if entry.is_file() and entry.name.endswith((".cpp", ".h", ".hpp")):
            process_file(entry.path, output_dir)
        elif entry.is_dir():
            relative_path = os.path.relpath(entry.path, start=input_dir)
            output_subdir = os.path.join(output_dir, relative_path)
            os.makedirs(output_subdir, exist_ok=True)
            process_directory(entry.path, output_subdir)

def main():
    parser = argparse.ArgumentParser(description="Process C++ files in a directory to extract function information.")
    parser.add_argument("--path", required=True, help="Path to the folder with C++ source files")
    parser.add_argument("--output", required=True, help="Path to the folder to save output JSON files")
    global args
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    process_directory(args.path, args.output)

    print(f"Processed files in {args.path}")
    print(f"Output written to {args.output}")

if __name__ == "__main__":
    main()

