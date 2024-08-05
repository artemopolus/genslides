import re
import json
import sys

def extract_functions_and_classes(file_name):
    with open(file_name, 'r') as file:
        content = file.read()

    function_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*:'
    class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(.*?)\s*:'

    functions = re.findall(function_pattern, content)
    classes = re.findall(class_pattern, content, re.DOTALL)

    function_names = [function[0] for function in functions]
    class_function_names = []
    for class_name, class_content in classes:
        class_functions = re.findall(function_pattern, class_content)
        class_function_names.extend([f'{class_name}.{class_function[0]}' for class_function in class_functions])

    return {"answer": function_names + class_function_names}

def main():
    if len(sys.argv) != 2:
        print("Usage: python script_name.py file_path")
        sys.exit(1)

    file_path = sys.argv[1]
    result = extract_functions_and_classes(file_path)
    output_json = json.dumps(result, indent=4)
    print(output_json)

if __name__ == "__main__":
    main()
