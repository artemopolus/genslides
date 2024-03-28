
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
