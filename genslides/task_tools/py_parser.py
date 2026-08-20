import json
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from pathlib import Path, PureWindowsPath
import genslides.utils.writer as Writer



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

def get_docstring_lines(code):
    tree = parser.parse(code.encode("utf8"))
    root_node = tree.root_node
    code_lines = code.splitlines()

    docstrings = []

    def get_first_statement(node):
        for child in node.children:
            # Комментарии не считаем statement'ами
            if child.type == "comment":
                continue

            return child

        return None

    def walk(node):
        if node.type in (
            "module",
            "function_definition",
            "class_definition",
        ):
            first_statement = get_first_statement(node)

            if first_statement and first_statement.type == "expression_statement":
                # В твоём AST:
                #
                # expression_statement
                #     string
                #
                # Поэтому берём первый child напрямую.
                for child in first_statement.children:
                    if child.type == "string":
                        line_number = child.start_point[0]

                        docstrings.append([
                            line_number,
                            child.text.decode("utf8"),
                            code_lines[line_number],
                        ])

                        break

        # Продолжаем поиск внутри функций и классов
        for child in node.children:
            if child.type in (
                "function_definition",
                "class_definition",
            ):
                walk(child)

    walk(root_node)

    return docstrings

def get_comment_lines(code):
    tree = parser.parse(code.encode("utf8"))
    root_node = tree.root_node
    code_lines = code.splitlines()

    comments = []

    def walk(node):
        if node.type == "comment":
            line_number = node.start_point[0]
            comment_text = node.text.decode("utf8")
            full_line = code_lines[line_number]

            comments.append([
                line_number,
                comment_text,
                full_line,
            ])

            # Внутри comment больше ничего интересующего нас нет.
            return

        for child in node.children:
            walk(child)

    walk(root_node)

    return comments

def get_global_variable_lines(code):
    tree = parser.parse(code.encode("utf8"))
    root_node = tree.root_node
    code_lines = code.splitlines()

    global_variables = []

    def walk(node, in_global_scope=True):
        # Если вошли в функцию или класс — всё внутри уже
        # не является глобальной переменной модуля.
        if node.type in ("function_definition", "class_definition"):
            return

        if node.type == "assignment" and in_global_scope:
            target = node.child_by_field_name("left")

            if target and target.type == "identifier":
                line_number = node.start_point[0]

                global_variables.append([
                    line_number,
                    target.text.decode("utf8"),
                    code_lines[line_number],
                ])

            # После assignment можно не искать assignment
            # внутри него повторно.
            return

        for child in node.children:
            walk(child, in_global_scope)

    walk(root_node)


    return global_variables


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

def get_class_function_body(code_text, class_name, function_name, return_type = "all"):
    tree = parser.parse(bytes(code_text, "utf8"))
    root_node = tree.root_node

    def traverse_for_function(node, found_class, in_nested_class=False, return_type = "all" ):
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
                if return_type == "all":
                    return f"{def_indent}def {function_name}{parameters_text}:\n{body_text}"  # Added def_indent
                elif return_type == "params":
                    parameters_inc = parameters_text.replace("(","")
                    parameters_inc = parameters_inc.replace(")","")
                    parameters_inc = parameters_inc.replace(" ","")

                    parameters_list = parameters_inc.split(",")
                    nout_params_list = []
                    for param in parameters_list:
                        if param != "self":
                            splitted_param = param.split(":")
                            if len(splitted_param) > 1:
                                paramout = splitted_param[0]
                            else:
                                paramout = param
                            # paramout = "\"" + paramout + "\""
                            nout_params_list.append(paramout)
                    parameters_text = ",".join(nout_params_list)
                    return f"{parameters_text}"
                else:
                    return f"{def_indent}def {function_name}{parameters_text}:\n{body_text}"  # Added def_indent

        for child in node.children:
            info = traverse_for_function(child, found_class, in_nested_class, return_type)
            if info:
                return info

        if node.type == 'class_definition' and found_class and in_nested_class:
            in_nested_class = False
        return None  # Return None if function not found in this branch

    return traverse_for_function(root_node, False, return_type=return_type)

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

def get_class_names_lines( code ):
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node
    class_names = []

    for node in root_node.children:  # Iterate only through direct children of the root
        if node.type == 'class_definition':
            class_name_node = node.child_by_field_name('name')
            class_name_node_text = class_name_node.text.decode('utf-8')
            parameters_node = node.child_by_field_name('parameters')
            parameters_text = parameters_node.text.decode() if parameters_node else "()"
            def_indent = " " * node.start_point[1]
            line = f"{def_indent}def {class_name_node_text}{parameters_text}:\n"  # Added def_indent
            class_names.append([class_name_node_text, line])

    return class_names


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

def getCodeParsingByArgs(arr : list, script_text):
    array_data = []
    if len(arr) > 2:
        if len(arr) > 4 and arr[2] == 'class_method':
            parsed = get_class_function_body(script_text, arr[3], arr[4])
            script_text = "" if parsed == None else parsed
        elif arr[2] == 'imports':
            array_data = get_import_statements(script_text)
        elif arr[2] == 'globvars':
            array_data = get_global_variable_lines( script_text )
        else:
            if len(arr) > 4:
                methods, classes = get_class_info(script_text, arr[3])
                if arr[2] == 'class_allmethods':
                    array_data = methods
                if arr[2] == 'class_allnested':
                    array_data = classes
            elif arr[2] == 'allmethods':
                array_data = get_global_functions(script_text)
            elif arr[2] == 'allclasses':
                array_data = get_class_names(script_text)
            else:
                array_data = []
    return array_data



def convertPythonFileToGenslidesJson( target_file_path : str , output_file_path : str )-> bool:
    """
    Считывает файл, извлекает информацию о методах и классах,
    используя py_parser.get_class_info().
    """
    # Путь к файлу, который нужно проанализировать
    target_file = Path(target_file_path)
    output_file = Path(output_file_path)
    if not target_file.is_file():
        return False
    if target_file.suffix != ".py":
        return False
    if output_file.is_dir():
        output_file = output_file / target_file.stem
        output_file = output_file.with_suffix(".json")
    else:
        return False

    # Считываем содержимое файла
    with target_file.open("r", encoding="utf-8") as f:
        code = f.read()
        # print(f"📄 Прочитано {len(code)} символ(ов) из {target_file}")

    output_jsonfile = {
            "filename": target_file.name,
            "path": target_file.absolute().as_posix(),
            "version": "0.1",
            "description":"Json File for genslides app",
            "targets":[] 
        }

    base_imports = get_import_statements( code )
    output_jsonfile["targets"].append({
        "type":"imports",
        "description": "imports",
        "body": "\n".join(base_imports)
    })

    base_global_vars = get_global_variable_lines( code )
    base_global_vars_text = ""
    for idx, name, text in base_global_vars:
        base_global_vars += text

    if len(base_global_vars):
        output_jsonfile["targets"].append({
                "type":"variables",
                "parent_target": "None",
                "description": "global_vars",
                "body": base_global_vars_text
        })


    
    base_global_method_names = get_global_functions( code )
    if len(base_global_method_names):
        base_global_method_text = ""
        for name in base_global_method_names:
            base_global_method_text += get_function_info( name )
        output_jsonfile["targets"].append({
                "type":"method",
                "parent_target": "None",
                "description": "global methods",
                "body": base_global_method_text
        })


    base_class_names = get_class_names_lines( code )
    for target_class_name, target_class_line in base_class_names:
        output_jsonfile["targets"].append({
                "type":"class",
                "parent_target": target_class_name,
                "name": target_class_name,
                "body": target_class_line
            })


        # Извлекаем информацию о методах и классах целевого класса
        target_methods, target_internal_classes = get_class_info(code, target_class_name)
        for method_name in target_methods:
            target_method_body_text = get_class_function_body(code, target_class_name, method_name)
            output_jsonfile["targets"].append({
                "type":"method",
                "parent_target": target_class_name,
                "name": method_name,
                "description": f"method {method_name} : class {target_class_name}",
                "body": target_method_body_text
            })

        # TODO:
        # for classname in target_internal_classes:


        # Вывод результатов
    try:
        with output_file.open("w", encoding="utf-8") as json_file:
        # with open(output_file_path, "w", encoding="utf-8") as json_file:
            json.dump(output_jsonfile, json_file, indent=4)
    except IOError as e:
        return False
    return True

def convert_genslide_json_file( target_file_path, output_file_path ):
    """
    Считывает файл, извлекает информацию о методах и классах,
    используя py_parser.get_class_info().
    """
    # Путь к файлу, который нужно проанализировать
    target_file = Path(target_file_path)
    output_file = Path(output_file_path)
    output = {
        "result":False,
        "report":""
    }
    if not target_file.is_file():
        output["report"] = "Is not file"
        return output
    if target_file.suffix != ".py":
        output["report"] = "Error: Is not py file"
        return output
    if output_file.is_dir():
        output_file = output_file / target_file.stem
        output_file = output_file.with_suffix(".json")
    else:
        output["report"] = f"Use {output_file} for writing"
        # return output

    # Считываем содержимое файла
    with target_file.open("r", encoding="utf-8") as f:
        code = f.read()
        # print(f"📄 Прочитано {len(code)} символ(ов) из {target_file}")


    output_jsonfile = {
            "filename": target_file.name,
            "path": target_file.absolute().as_posix(),
            "version": "0.1",
            "description":"Json File for genslides app",
            "targets":[] 
        }
    return convert_text_to_genslides_json_file( code, output_jsonfile, output_file, output)

def generate_genslides_json_file( code, filename, output_file_path):
    output_file = Path(output_file_path)
    output = {
        "result":False,
        "report":""
    }
    if output_file.is_dir():
        output_file = output_file / filename
        output_file = output_file.with_suffix(".json")
    else:
        output["report"] = f"Error: {output_file.resolve()} is not dir"
        return output
    output_jsonfile = {
            "filename": filename,
            "version": "0.1",
            "description":"Json File for genslides app",
            "targets":[] 
        }
    return convert_text_to_genslides_json_file( code, output_jsonfile, output_file, output)

def convert_text_to_genslides_json_file( code, output_jsonfile, output_file : Path, output):

    print( "Convert text to genslides json file" )

    base_imports = get_import_statements( code )
    output_jsonfile["targets"].append({
        "type":"imports",
        "description": "imports",
        "body": "\n".join(base_imports)
    })
    docstrings_txt = []

    for doc in get_docstring_lines( code ):
        if len( doc) == 3:
            docstrings_txt.append( doc[2])

    if len( docstrings_txt ):
        output_jsonfile["targets"].append({
                "type":"variables",
                "parent_target": "None",
                "description": "doc_strings",
                "body": "\n".join( docstrings_txt )
        })

    global_comments_txt = []

    for global_comments in get_comment_lines( code ):
        if len( global_comments ) == 3:
            global_comments_txt.append( global_comments[2] )
    if len( global_comments_txt):
        output_jsonfile["targets"].append({
                "type":"variables",
                "parent_target": "None",
                "description": "comments",
                "body": "\n".join( global_comments_txt )
        })

    base_global_vars = get_global_variable_lines( code )
    base_global_vars_text = []
    for bgvars in base_global_vars:
        if len( bgvars ) == 3:
            base_global_vars_text.append( bgvars[2] )

    if len(base_global_vars):
        output_jsonfile["targets"].append({
                "type":"variables",
                "parent_target": "None",
                "description": "global_vars",
                "body": "\n".join( base_global_vars_text )
        })


    
    base_global_method_names = get_global_functions( code )
    if len(base_global_method_names):
        base_global_method_text = ""
        for name in base_global_method_names:
            base_global_method_text += parse_text( code, name )
        output_jsonfile["targets"].append({
                "type":"method",
                "parent_target": "None",
                "description": "global methods",
                "body": base_global_method_text
        })


    base_class_names = get_class_names_lines( code )
    for target_class_name, target_class_line in base_class_names:
        output_jsonfile["targets"].append({
                "type":"class",
                "parent_target": target_class_name,
                "name": target_class_name,
                "body": target_class_line
            })


        # Извлекаем информацию о методах и классах целевого класса
        target_methods, target_internal_classes = get_class_info(code, target_class_name)
        for method_name in target_methods:
            target_method_body_text = get_class_function_body(code, target_class_name, method_name)
            output_jsonfile["targets"].append({
                "type":"method",
                "parent_target": target_class_name,
                "name": method_name,
                "description": f"method {method_name} : class {target_class_name}",
                "body": target_method_body_text
            })

        # TODO:
        # for classname in target_internal_classes:


        # Вывод результатов
    try:
        Writer.writeJsonToFile( output_file , output_jsonfile, indent=4)
        # with output_file.open("w", encoding="utf-8") as json_file:
        #     json.dump(output_jsonfile, json_file, indent=4)
    except IOError as e:
        output["report"] = f"Error writing to file {PureWindowsPath(output_file.resolve())}: {e}"
        return output
    output["report"] = f"Output written to {PureWindowsPath(output_file.resolve())}"
    output["result_filepath"] = PureWindowsPath(output_file.resolve())
    output["result"] = True
    return output


