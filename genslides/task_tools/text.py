import hashlib

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
