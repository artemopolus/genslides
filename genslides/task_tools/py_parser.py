import argparse
from tree_sitter import Language, Parser
import tree_sitter_python as tspython




PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)



def get_function_info(node, function_name):
    if node.type == 'function_definition':
        name_node = node.child_by_field_name('name')
        if name_node and name_node.text.decode() == function_name:
            parameters_node = node.child_by_field_name('parameters')
            parameters_text = parameters_node.text.decode() if parameters_node else "()"
            body_node = node.child_by_field_name('body')

            def_indent = " " * node.start_point[1]
            body_indent = " " * body_node.start_point[1] if body_node else ""

            body_text = ""
            if body_node:
                body_lines = body_node.text.decode().splitlines()
                if body_lines:
                    first_line = body_lines[0]
                    rest_of_the_lines = "\n".join(body_lines[1:])
                    body_text = f"{first_line}\n{rest_of_the_lines}" if rest_of_the_lines else first_line
                    body_text =  f"{body_indent}{body_text}"  

            return f"{def_indent}def {function_name}{parameters_text}:\n{body_text}"

    for child in node.children:
        info = get_function_info(child, function_name)
        if info:
            return info
    return ""  # Return empty string if function not found

def parse_text(code_text, function_name, encoding="utf-8"):
    """
    Parses the given code text and extracts information about the specified function.

    Args:
        code_text: The code as a string.
        function_name: The name of the function to extract information about.
        encoding: The encoding of the code text (default: utf-8).

    Returns:
        The function information as a string, or an error message if the function is not found or an error occurs.
    """
    try:
        LANGUAGE = Language(tspython.language())  # Assuming tspython and Language are available
        ts_parser = Parser(LANGUAGE)
        tree = ts_parser.parse(bytes(code_text, encoding))
        root_node = tree.root_node

        function_info = get_function_info(root_node, function_name)  # Assuming get_function_info is defined
        if function_info:
            return function_info
        else:
            return f"Function '{function_name}' not found."

    except (UnicodeDecodeError, Exception) as e:
        return f"Error during parsing: {e}"


def get_global_variable_lines(code):
    """
    Parses Python code and returns a list of lines containing global variable declarations.

    Args:
        code: The Python code as a string.

    Returns:
        A list of tuples, where each tuple contains:
            - The line number (0-indexed).
            - The variable name.
            - The full line of code.
        Returns an empty list if no global variables are found.
    """
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node
    code_lines = code.splitlines()

    def _get_global_variables(node, current_scope=None):
        global_variables = []

        if current_scope is None:
            current_scope = []

        for child in node.children:
            if child.type == 'class_definition':
                continue  # Skip class nodes

            elif child.type == 'function_definition':
                global_variables.extend(_get_global_variables(child, current_scope + ["function"]))

            elif child.type == 'assignment':
                if not current_scope:  # Only in global scope
                    target = child.child_by_field_name("left")
                    if target and target.type == 'identifier':
                        line_number = child.start_point[0]
                        full_line = code_lines[line_number]
                        global_variables.append((line_number, target.text.decode(), full_line))

            else:
                global_variables.extend(_get_global_variables(child, current_scope))

        return global_variables

    return _get_global_variables(root_node)

def get_import_statements(code):
    """
    Extracts import statements from Python code.

    Args:
        code: The Python code as a string.

    Returns:
        A list of strings, where each string is an import statement.
    """
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node

    def _traverse_tree(node):
        imports = []
        if node.type in ('import_statement', 'import_from_statement'):
            imports.append(node.text.decode('utf-8'))
        for child in node.children:
            imports.extend(_traverse_tree(child))
        return imports

    return _traverse_tree(root_node)

def get_class_function_body(code_text, class_name, function_name):
    tree = parser.parse(bytes(code_text, "utf8"))
    root_node = tree.root_node

    def traverse_for_function(node, found_class, in_nested_class=False):
        if node.type == 'class_definition':
            class_name_node = node.child_by_field_name('name')
            current_class_name = class_name_node.text.decode('utf-8')
            if current_class_name == class_name:
                found_class = True
            elif found_class:
                in_nested_class = True

        if found_class and node.type == 'function_definition' and not in_nested_class:
            name_node = node.child_by_field_name('name')
            if name_node and name_node.text.decode() == function_name:
                parameters_node = node.child_by_field_name('parameters')
                parameters_text = parameters_node.text.decode() if parameters_node else "()"
                body_node = node.child_by_field_name('body')

                def_indent = " " * node.start_point[1]
                body_indent = " " * body_node.start_point[1] if body_node else ""

                body_text = ""
                if body_node:
                    body_lines = body_node.text.decode().splitlines()
                    if body_lines:
                        first_line = body_lines[0].strip()  # Strip leading/trailing whitespace
                        rest_of_the_lines = "\n".join(body_lines[1:])
                        body_text = f"{first_line}\n{rest_of_the_lines}" if rest_of_the_lines else first_line
                        body_text = f"{body_indent}{body_text}"

                return f"{def_indent}def {function_name}{parameters_text}:\n{body_text}"  # Added def_indent

        for child in node.children:
            info = traverse_for_function(child, found_class, in_nested_class)
            if info:
                return info

        if node.type == 'class_definition' and found_class and in_nested_class:
            in_nested_class = False
        return None  # Return None if function not found in this branch

    return traverse_for_function(root_node, False)

def get_class_info(code, target_class_name):
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node

    def traverse_for_info(node, found_class, in_nested_class=False):
        class_methods = []
        nested_classes = []

        if node.type == 'class_definition':
            class_name_node = node.child_by_field_name('name')
            current_class_name = class_name_node.text.decode('utf-8')
            if current_class_name == target_class_name:
                found_class = True
            elif found_class:  # Check if we've entered a nested class within the target
                in_nested_class = True
                nested_classes.append(current_class_name) # Collect nested class names

        if found_class and node.type == 'function_definition' and not in_nested_class:
            method_name_node = node.child_by_field_name('name')
            class_methods.append(method_name_node.text.decode('utf-8'))

        for child in node.children:
            methods, nested = traverse_for_info(child, found_class, in_nested_class)
            class_methods.extend(methods)
            nested_classes.extend(nested)

        if node.type == 'class_definition' and found_class and in_nested_class:
             in_nested_class = False # Reset after nested class

        return class_methods, nested_classes

    return traverse_for_info(root_node, False)

def get_global_functions(code):
    """
    Extracts top-level function names from Python code.

    Args:
        code: The Python code as a string.

    Returns:
        A list of global function names (strings).
    """
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node
    function_names = []

    for node in root_node.children:
        if node.type == 'function_definition':
            function_name_node = node.child_by_field_name('name')
            function_names.append(function_name_node.text.decode('utf-8'))

    return function_names

def get_class_names(code):
    """
    Extracts top-level class names from Python code.

    Args:
        code: The Python code as a string.

    Returns:
        A list of class names (strings).
    """
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node
    class_names = []

    for node in root_node.children:  # Iterate only through direct children of the root
        if node.type == 'class_definition':
            class_name_node = node.child_by_field_name('name')
            class_names.append(class_name_node.text.decode('utf-8'))

    return class_names

