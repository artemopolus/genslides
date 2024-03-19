import re
import json
import sys

def extract_functions_and_classes(data):
    function_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*:'
    class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(.*?)\s*:'

    result = []

    for file_name, content in data.items():
        functions = re.findall(function_pattern, content)
        classes = re.findall(class_pattern, content, re.DOTALL)

        for function in functions:
            result.append(function[0])

        for class_name, class_content in classes:
            result.append(f"{class_name}_class")
            class_functions = re.findall(function_pattern, class_content)
            for class_function in class_functions:
                result.append(f"{class_function[0]}_{class_name}")

    return {"answer": result}

def main(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = {
            file_path: file.read()
        }

    result = extract_functions_and_classes(data)
    print(json.dumps(result, indent=4))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path>")
    else:
        file_path = sys.argv[1]
        main(file_path)
