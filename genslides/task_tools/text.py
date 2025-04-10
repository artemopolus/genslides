import hashlib
import genslides.utils.loader as Loader

def compute_sha256_hash(input_text: str) -> str:
    """
    Compute the SHA256 hash of the given input text.

    Args:
        input_text (str): The text to be hashed.

    Returns:
        str: The hexadecimal representation of the SHA256 hash of the input text.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(input_text, str):
        raise TypeError("Input must be a string.")

    # Create a new SHA256 hash object
    sha256_hasher = hashlib.sha256()

    # Encode the input text to bytes and update the hash object
    sha256_hasher.update(input_text.encode('utf-8'))

    # Return the hexadecimal digest of the hash
    return sha256_hasher.hexdigest()


def split_text_with_context(input_text, part_symbol_count, text_length_before, text_length_after):
    # Validate input parameters
    if part_symbol_count <= 0:
        raise ValueError("part_symbol_count must be greater than 0")
    if text_length_before < 0 or text_length_after < 0:
        raise ValueError("text_length_before and text_length_after must be non-negative")
    
    result_list = []
    total_length = len(input_text)
    
    for start_index in range(0, total_length, part_symbol_count):
        end_index = min(start_index + part_symbol_count, total_length)
        
        # Get the part of text
        part_text = input_text[start_index:end_index]
        
        # Calculate the indexes for before and after text
        before_start_index = max(0, start_index - text_length_before)
        before_text = input_text[before_start_index:start_index]
        
        after_end_index = min(total_length, end_index + text_length_after)
        after_text = input_text[end_index:after_end_index]
        
        # Combine before, part, and after text
        result_text = before_text + part_text + after_text
        
        # Add to result list
        result_list.append({
            'Result Text': result_text,
            'Start Index of Text': before_start_index,
            'End Index of Text': after_end_index
        })
    
    return result_list


def cut_text_into_parts(text, parts_count, before_length, after_length):
    if parts_count <= 0:
        return []

    # Determine the length of the original text
    text_length = len(text)
    part_length = text_length // parts_count  # Length of each part

    result = []
    for i in range(parts_count):
        start_index = i * part_length
        end_index = start_index + part_length

        # Handle the last part to include any remaining characters
        if i == parts_count - 1:
            end_index = text_length

        # Determine start and end indices for the text to return
        actual_start_index = max(0, start_index - before_length)
        actual_end_index = min(text_length, end_index + after_length)

        # Create the resulting text with 'before' and 'after' text included
        result_text = text[actual_start_index:actual_start_index + (end_index - start_index)] + text[end_index:actual_end_index]

        result.append({
            'Result Text': result_text,
            'Start Index of Text': actual_start_index,
            'End Index of Text': actual_end_index
        })

    return result

def convert_text_with_names_to_list( text : str, delimiter = ',') -> list[str]:
    names = text.split(delimiter)
    for name in names:
        name.replace(" ","")
    return names

def getNumberBySplitting( text : str):
    values = text.split("_")
    if len(values) == 2 and values[1].isalnum():
        return int(values[1])
    return 1

def getMDcode( tmparg ):
    md_code = []
    conv = tmparg.pop(0)
    if conv == 'md':
        while len(tmparg):
            if tmparg[0] == '00':
                tmparg.pop(0)
                break
            else:
                md_code.append(tmparg.pop(0))
    return md_code, tmparg

def convertJsonDictToText2(trg: dict, opt: dict) -> str:
    """
    Converts a JSON dictionary to Markdown text based on the provided options.

    Args:
        trg: The JSON dictionary to convert.
        opt: A dictionary specifying how to handle different keys.

    Returns:
        A Markdown string representation of the JSON dictionary.
    """
    text = ""
    for key, value in trg.items():
        text += convertJsonDictToText2internal(key, value, 0, opt) # Pass key to internal function
    return text


def convertJsonDictToText2internal(key: str, value, idx: int, opt: dict) -> str:
    """
    Recursively processes a nested dictionary or list based on the provided options.

    Args:
        key: The key of the current value.
        value: The value to process (can be a dictionary, list, or primitive).
        idx: The indentation level or header level.
        opt: A dictionary specifying how to handle different keys.

    Returns:
        A Markdown string representation of the value.
    """
    text = ""

    if key in opt:
        option = opt[key]
        option_type = option.get("type", "text")  # Default to "text" if type is missing

        if option_type == "header":
            level = option.get("level", 1)
            text += f"{'#' * level} {value}\n"  # Create header
        elif option_type == "text":
            text += f"{value}\n"  # Add plain text
        elif option_type == "list":
            indent = option.get("indent", 2)
            indent_str = " " * indent
            if isinstance(value, list):
                for item in value:
                    text += f"{indent_str}- {item}\n"  # Create list item
            else:
                text += f"{indent_str}- {value}\n" # Create list item if value is not a list.

        elif option_type == "ignore":
            return ""  # Ignore this key-value pair
    else:
        # If no option is specified, handle based on value type
        if isinstance(value, dict):
            for k, v in value.items():
                text += convertJsonDictToText2internal(k, v, idx + 1, opt) # recursive call
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        text += convertJsonDictToText2internal(k, v, idx+1, opt) #recursive call
                else:
                    text += f"{' ' * (idx+1)}- {item}\n"  # Default list formatting
        else:
            text += f"{value}\n" #Default text formatting

    return text

def convertJsonDictToText( args : list[str], trg ):
    tmpargs = args.copy()
    text = ""
    idx = 0
    keys = ["header","section","point","number"]
    if isinstance(trg, dict):
        while(len(tmpargs) > 1):
            if tmpargs[0].startswith("header") and tmpargs[1] in trg:
                shift = getNumberBySplitting(tmpargs[0])
                text += shift*"#" + " " + trg[tmpargs[1]] + "\n"
            elif tmpargs[0].startswith("section") and tmpargs[1] in trg:
                value = trg[tmpargs[1]]
                if isinstance(value, dict):
                    y = 2
                    while( y < len(tmpargs) ):
                        if isinstance(value, dict) and tmpargs[y] in value and tmpargs[y] not in keys:
                            value = value[tmpargs[y]]
                            y += 1
                        else:
                            break
                    if y > 2:
                        while( y > 2) :
                            tmpargs.pop(0)
                            y -= 1
                if isinstance(value, str):
                    text +=  value + "\n\n"
                elif isinstance(value, dict):
                    text += Loader.Loader.convJsonToText(value)
                
            elif tmpargs[0].startswith("point") and tmpargs[1] in trg:
                shift = getNumberBySplitting(tmpargs[0])
                text += (shift-1)*" " + "- " + trg[tmpargs[1]] + "\n"
            elif tmpargs[0].startswith("number") and tmpargs[1] in trg:
                shift = getNumberBySplitting(tmpargs[0])
                text += (shift-1)*" " + f"{idx}. " + trg[tmpargs[1]] + "\n"
            else:
                text += "\n"
            tmpargs.pop(0)
            tmpargs.pop(0)
            idx += 1
    elif isinstance(trg, list):
        for part in trg:
            text += convertJsonDictToText(args, part) + "\n"

    return text
