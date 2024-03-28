import re

def extract_functions_and_classes(file_name):
    with open(file_name, 'r') as file:
        content = file.read()

    function_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*:'
    class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(.*?)\s*:'

    functions = re.findall(function_pattern, content)
    classes = re.findall(class_pattern, content, re.DOTALL)

    for function in functions:
        print(f"Function: {function[0]}")

    for class_name, class_content in classes:
        print(f"Class: {class_name}")
        class_functions = re.findall(function_pattern, class_content)
        for class_function in class_functions:
            print(f"    Function: {class_function[0]}")

file_name = "sample_file.py"

test_data = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def getValue(name: str, age: int) -> str:
    return f"{name} is {age} years old."

class Calculator:
    def __init__(self):
        self.result = 0

    def add(self, num):
        self.result += num

    def subtract(self, num):
        self.result -= num

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        return f"Hello, my name is {self.name} and I am {self.age} years old."

if __name__ == "__main__":
    calc = Calculator()
    calc.add(5)
    calc.subtract(2)

    john = Person("John", 30)
    print(john.greet())
"""

with open(file_name, 'w') as file:
    file.write(test_data)

extract_functions_and_classes(file_name)
