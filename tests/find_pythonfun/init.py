import re

def extract_functions_and_classes(data):
    function_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*:'
    class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(.*?)\s*:'

    for file_name, content in data.items():
        print(f"File: {file_name}")
        functions = re.findall(function_pattern, content)
        classes = re.findall(class_pattern, content, re.DOTALL)

        for function in functions:
            print(f"Function: {function[0]}")

        for class_name, class_content in classes:
            print(f"Class: {class_name}")
            class_functions = re.findall(function_pattern, class_content)
            for class_function in class_functions:
                print(f"    Function: {class_function[0]}")

data = {
    "sample_file.py": "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n\nclass Calculator:\n    def __init__(self):\n        self.result = 0\n\n    def add(self, num):\n        self.result += num\n\n    def subtract(self, num):\n        self.result -= num\n\nclass Person:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n\n    def greet(self):\n        return f\"Hello, my name is {self.name} and I am {self.age} years old.\"\n\nif __name__ == \"__main__\":\n    calc = Calculator()\n    calc.add(5)\n    calc.subtract(2)\n\n    john = Person(\"John\", 30)\n    print(john.greet())"
}

extract_functions_and_classes(data)
