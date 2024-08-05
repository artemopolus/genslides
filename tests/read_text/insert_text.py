import json
import sys

def insert_text_from_json(target_text, json_instructions):
    """
    Inserts text into the target text based on 'after' markers defined in the JSON instructions.
    
    Parameters:
      target_text (str): The original text where new content will be inserted.
      json_instructions (str): A JSON-formatted string containing insertion instructions.
      
    Returns:
      str: The modified text with the inserted contents.
    """
    instructions = json.loads(json_instructions)
    
    # Ensure the instructions are processed in reverse to maintain correct insertion positions
    for item in reversed(instructions["answer"]):
        after_text = item['after']
        text_to_insert = item['text']
        insert_index = target_text.rfind(after_text)
        
        if insert_index != -1:  # If the 'after' marker is found
            insert_index += len(after_text)  # Adjust to insert after the 'after' marker
            target_text = f"{target_text[:insert_index]}\n{text_to_insert}{target_text[insert_index:]}"
            
    return target_text

def main():
    # Retrieve target text and JSON data from script arguments
    if len(sys.argv) < 3:
        print("Usage: python script.py <target_text_file> <json_instructions_file>")
        sys.exit(1)
    
    target_text_file = sys.argv[1]
    json_instructions_file = sys.argv[2]
    
    with open(target_text_file, 'r', encoding='utf-8') as file:
        target_text = file.read()
        
    with open(json_instructions_file, 'r', encoding='utf-8') as file:
        json_instructions = file.read()
    
    # Insert text based on JSON instructions
    modified_text = insert_text_from_json(target_text, json_instructions)
    
    # Display or save the modified text
    print(modified_text)

if __name__ == "__main__":
    main()
