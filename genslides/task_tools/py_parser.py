import argparse
from tree_sitter import Language, Parser
import tree_sitter_python as tspython


def get_function_info(node, function_name):
    if node.type == 'function_definition':
        name_node = node.child_by_field_name('name')
        if name_node and name_node.text.decode() == function_name:
            parameters_node = node.child_by_field_name('parameters')
            parameters_text = parameters_node.text.decode() if parameters_node else "()"
            body_node = node.child_by_field_name('body')

            # Calculate indents based on start_point's column
            def_indent = " " * node.start_point[1]
            body_indent = " " * body_node.start_point[1] if body_node else ""  # Handle cases with no body


            body_text = ""
            if body_node:
                body_lines = body_node.text.decode().splitlines()
                if body_lines: # Check if there are lines in the body
                    first_line = body_lines[0]
                    rest_of_the_lines = "\n".join(body_lines[1:])

                    body_text = f"{first_line}\n{rest_of_the_lines}" if rest_of_the_lines else first_line  # Properly handle both single and multi-line bodies
                
                    body_text =  f"{body_indent}{body_text}"  # Indent the formatted body
                


            return f"{def_indent}def {function_name}{parameters_text}:\n{body_text}"

    for child in node.children:
        info = get_function_info(child, function_name)
        if info:
            return info
    return None

def parse_text(code_text, function_name, encoding="utf-8"):
    """
    Parses the given code text and extracts information about the specified function.

    Args:
        code_text: The code as a string.
        function_name: The name of the function to extract information about.
        encoding: The encoding of the code text (default: utf-8).

    Returns:
        The function information as a string, or None if the function is not found.
    """
    try:
        LANGUAGE = Language(tspython.language()) # Assuming tspython and Language are available in scope
        ts_parser = Parser(LANGUAGE)
        tree = ts_parser.parse(bytes(code_text, encoding))
        root_node = tree.root_node

        function_info = get_function_info(root_node, function_name) # Assuming get_function_info is defined
        return function_info

    except (UnicodeDecodeError, Exception) as e:
        print(f"Error during parsing: {e}")
        return None


