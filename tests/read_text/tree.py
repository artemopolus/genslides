import xml.etree.ElementTree as ET

class Node:
    def __init__(self, name, content):
        self.name = name
        self.content = content
        self.children = []

    def add_child(self, child):
        self.children.append(child)

def collect_tree_strings(node, level=0):
    """
    Collects the tree content in a tagged format to reflect structure
    :param node: Current node being processed
    :param level: The current depth level in the tree
    :return: A list of strings representing the serialized tree content
    """
    indent = "  " * level
    parts = []
    
    parts.append(f"{indent}<node>\n")
    parts.append(f"{indent}  <name>{node.name}</name>\n")
    parts.append(f"{indent}  <content>{node.content}</content>\n")
    
    for child in node.children:
        parts.extend(collect_tree_strings(child, level + 1))
    
    parts.append(f"{indent}</node>\n")
    
    return parts

def print_tree(node):
    """
    Produces a string representation of the tree
    :param node: The root node of the tree
    :return: Serialized string of the tree
    """
    parts = collect_tree_strings(node)
    return ''.join(parts)

# Example usage
root = Node("root", "Root Content")
child1 = Node("child1", "Child 1 Content")
child2 = Node("child2", "Child 2 Content")
child3 = Node("child3", "Child 3 Content")
child11 = Node("child1.1", "Child 1.1 Content")
child21 = Node("child2.1", "Child 2.1 Content")

root.add_child(child1)
root.add_child(child2)
root.add_child(child3)
child1.add_child(child11)
child2.add_child(child21)
grch1 = Node("gr1","tttt")
child1.add_child(grch1)


serialized_tree = print_tree(root)
print(serialized_tree)


def parse_node(element):
    """
    Recursively parse XML element to construct tree nodes
    :param element: The starting XML element for parsing
    :return: The constructed Node
    """
    name = element.find('name').text
    content = element.find('content').text
    node = Node(name, content)
    for child_element in element.findall('node'):
        child_node = parse_node(child_element)
        node.add_child(child_node)
    return node

def restore_tree(serialized_text):
    """
    Restores the tree structure from serialized text
    :param serialized_text: The serialized text representing the tree
    :return: The root node of the reconstructed tree
    """
    root_element = ET.fromstring(serialized_text)
    root_node = parse_node(root_element)
    return root_node

# Example serialized text updated for new format with name tags
serialized_text = """
<node>
  <name>root</name>
  <content>Root Content</content>
  <node>
    <name>child1</name>
    <content>Child 1 Content</content>
    <node>
      <name>child1.1</name>
      <content>Child 1.1 Content</content>
    </node>
  </node>
  <node>
    <name>child2</name>
    <content>Child 2 Content</content>
    <node>
      <name>child2.1</name>
      <content>Child 2.1 Content</content>
    </node>
  </node>
  <node>
    <name>child3</name>
    <content>Child 3 Content</content>
  </node>
</node>
"""

# Restore the tree from serialized text
restored_root = restore_tree(serialized_tree)
# restored_root = restore_tree(serialized_text)

# Function to print the restored tree for verification
def print_restored_tree(node, level=0):
    indent = "  " * level
    print(f"{indent}- {node.name}: {node.content}")
    for child in node.children:
        print_restored_tree(child, level + 1)

# Verify the restored tree structure
print_restored_tree(restored_root)

