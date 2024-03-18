import ast
import sys

def main(file_path):
    # Read the content of the file
    with open(file_path, 'r', encoding='utf-8') as file:
        test_code = file.read()

    # Parse the code into an AST
    tree = ast.parse(test_code)

    class ClassVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            print(f'class {node.name}')  # Print the class name
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef):
                    print(body_item.name)  # Print the function name
            self.generic_visit(node)  # Continue visiting the tree

    # Instantiate the visitor and walk the AST
    visitor = ClassVisitor()
    visitor.visit(tree)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the path to the file containing the test_code")
    else:
        file_path = sys.argv[1]
        main(file_path)
