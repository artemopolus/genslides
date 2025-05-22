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


def convertJsonDictToText2( trg : dict, opt : dict) -> str:
    """
    Converts a JSON-like dictionary to Markdown text based on provided options.

    Args:
        trg (dict): The JSON-like dictionary to convert.
        opt (dict): A dictionary specifying conversion options for each key.

    Returns:
        str: The Markdown representation of the JSON data.
    """
    text= f""
    # for key, value in trg.items():
    #     if isinstance(value, dict):
    text += convertJsonDictToText2internal(trg, opt)
        #No recursion needed here since top level keys are not processed based on type
    return text

def checkTargetField(opt : dict):
    if "target_field_key" in opt and opt["target_field_key"] != "":
        return True
    return False

def checkValueInDict(opt : dict, point : dict):
    # print("search in", point)
    for tkey, tvalue in opt["target_field_key"].items():
        # print(f"search {tkey} : {tvalue}")
        if tkey in point and point[tkey] == tvalue:
            return True
    return False



def convertJsonDictToText2internal( trg : dict, opt : dict ) -> str:
    """
    Recursively converts a JSON-like dictionary to Markdown text based on provided options.

    Args:
        trg (dict): The JSON-like dictionary to convert.
        opt (dict): A dictionary specifying conversion options for each key.

    Returns:
        str: The Markdown representation of the JSON data.
    """
    text = ""
    for key, value in trg.items():
        if key in opt:
            option = opt[key]
            prefix = option.get("prefix", "")
            suffix = option.get("suffix", "")
            value_type = option.get("type", "text")



            if checkTargetField(opt):
                if checkValueInDict( opt , trg):
                    text += f"{prefix}{value}{suffix}"
            elif value_type == "text":
                text += f"{prefix}{value}{suffix}"
            # elif value_type == "list":
            #     if isinstance(value, list):
            #         for item in value:
            #             if isinstance(item, dict):
            #                 item_text = convertJsonDictToText2internal(item, opt)
            #             else:
            #                 item_text = str(item)
            #             text += f"{prefix}{item_text}{suffix}"
            #     else:
            #         # Handle the case where the value isn't a list but should be treated as one
            #         text += f"{prefix}{value}{suffix}"  # Treat the single value as a list item
            elif value_type == "numerical_list":
                idx = option.get("idx", 0)
                content = f"{prefix}{value}{suffix}".replace("[[number]]", str(idx))
                option['idx'] = idx + 1
                text += content

                # if isinstance(value, list):
                #     for i, item in enumerate(value):
                #         if isinstance(item, dict):
                #             item_text = convertJsonDictToText2internal(item, opt)
                #         else:
                #             item_text = str(item)
                #         text += f"{i}{prefix}{item_text}{suffix}"
                # else:
                #     # Handle the case where the value isn't a list but should be treated as one
                #     text += f"{prefix}{value}{suffix}"  # Treat the single value as a numerical list item

        elif isinstance(value, dict):
            text += convertJsonDictToText2internal(value, opt)
        elif isinstance(value, list):
            # print("List")
            for point in value:
                if isinstance(point, dict):
                    if checkTargetField(opt):
                        if checkValueInDict( opt , point):
                    # if "target_field_key" in opt and opt["target_field_key"] != "":
                        # print("search for", opt["target_field_key"])
                        # for tkey, tvalue in opt["target_field_key"].items():
                            # if tkey in point and point[tkey] == tvalue:
                                # print(f"Found {point[tkey]} == {tvalue}")
                                text += convertJsonDictToText2internal(point, opt)
                    else:
                        text += convertJsonDictToText2internal(point, opt)
    return text


def convertJsonDictToText( args : list[str], trg ):
    tmpargs = args.copy()
    text = f"{args}"
    idx = 0
    keys = ["header","section","point","number"]
    if isinstance(trg, dict):
        text += "dict\n"
        while(len(tmpargs) > 1):
            text += str(tmpargs[0]) + "," + str(tmpargs[1]) + ":" + str(trg)
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
        text += "list\n"
        for part in trg:
            text += convertJsonDictToText(args, part) + "\n"
    else:
        text = f"Target is not list or dict. Arguments: {args}"

    return text
