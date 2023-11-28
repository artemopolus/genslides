import re

def convert_md_to_script(md_text, script_file):
    code_pattern = r'```python\n(.*?)\n```'
    
    with open(script_file, 'w') as file:
        parts = re.split(code_pattern, md_text, flags=re.DOTALL)
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Non-code parts treated as comments
                lines = part.strip().split('\n')
                comment_lines = ['# ' + line for line in lines]
                file.write('\n'.join(comment_lines) + '\n')
            else:  # Code parts
                file.write(part.strip() + "\n")


# Example usage
md_text = """
This is a sample Markdown text with Python code:

## Markdown Heading

This is some Markdown text.

```python
# Python code example
name = "John"
print("Hello, " + name + "!")
```

More Markdown text here.
"""

convert_md_to_script(md_text, 'script.py')