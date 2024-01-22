import os
import sys

def find_todos(code, filename):
    todo_list = []

    lines = code.split('\n')

    for line in lines:
        if "TODO" in line:
            todo_content = line.split("TODO")[1].strip()

            if "def" in line:
                function_name = line.split("def")[1].split("(")[0].strip()
                todo_list.append([f"{filename}:{function_name}", todo_content])
            else:
                todo_list.append([f"{filename}:body", todo_content])

    return todo_list

def find_todos_in_files(folder):
    todos = []
    
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding="utf-8") as f:
                    code = f.read()
                    todos.extend(find_todos(code, file_path))
    
    return todos

def main(folder_path):
    todos = find_todos_in_files(folder_path)

    for todo in todos:
        print(todo)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder_path>")
    else:
        folder_path = sys.argv[1]
        main(folder_path)
