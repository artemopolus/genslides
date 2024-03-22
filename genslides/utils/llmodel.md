# Main part
# Examples

### LLModel_class Features and Functionalities:

1. Initialization with model parameters.
2. Creation of chat completions based on messages.
3. Tracking and adding a counter to prompts based on token usage.
4. Calculating the number of tokens and price for text input.
5. Getting user, assistant, and system tags.
6. Handling token count limit for messages.

### Simple Usage Example 1: Initialization

```python
from llmodel import LLModel

# Initialize LLModel with default parameters
model = LLModel()

# Check the active status of the model
print(model.active)
```

**Expected Output:**  
```
True
```

### Simple Usage Example 2: Creating Chat Completion

```python
from llmodel import LLModel

model = LLModel()
messages = [{"role": "user", "content": "Hello"}]
success, response, output = model.createChatCompletion(messages)

print(success)
print(response)
print(output)
```

**Expected Output:**  
```
True
<generated response from the model>
{'type': 'response', 'model': 'gpt-3.5-turbo', 'intok': <input_tokens_used>, 'outtok': <output_tokens_generated>, ...}
```

### Advanced Example: Adding Counter to Prompts

```python
from llmodel import LLModel

model = LLModel()
model.addCounterToPromts(100, 0.002)

# Check the stored counter data
with open(model.path_to_file, 'r') as f:
    data = json.load(f)
    print(data)
```

**Expected Output:**  
```
[{'date': 'YYYY-MM-DD', 'sum': <total_sum_of_counters>}]
```

### Common Pitfall:

If the token count exceeds the maximum limit, the `checkTokens` function in LLModel removes messages iteratively to meet the limit. Ensure that the input messages are appropriately handled to prevent data loss.

The examples provided demonstrate the basic and advanced functionalities of the `LLModel` class for handling chat completions, price calculations, and counter tracking. Your feedback on the clarity and utility of these examples is valuable for further improvements.
### Function: checkTokens

#### Introduction:
The `checkTokens` function in the `LLModel` class is used to ensure that the total number of tokens in a list of messages does not exceed the maximum token limit specified in the parameters. If the total tokens surpass the limit, the function removes messages from the beginning of the list until the token count is within the threshold.

#### Key Features:
1. Calculate the total number of tokens in a given text.
2. Check and adjust the token count in a list of messages based on a maximum token limit.
3. Ensure messages do not exceed the maximum token limit by removing excess messages.

#### Example 1: Basic Usage
This example demonstrates the function with a list of messages and ensures the total tokens do not exceed the maximum limit.

```python
# Sample list of messages
messages = [
    {"content": "Hello, how are you?"},
    {"content": "I'm doing well, thank you for asking."},
    {"content": "What have you been up to lately?"}
]

# Initialize LLModel instance
llmodel = LLModel()

# Check and adjust tokens in the messages list
processed_messages = llmodel.checkTokens(messages)

print(processed_messages)
```

**Expected Output:** The function will adjust the list of messages to ensure the total token count is within the specified limit.

#### Example 2: Handling Exceeding Tokens
This example showcases the function when the total tokens in messages exceed the maximum token limit, requiring adjustment.

```python
# Sample list of messages with high token count
messages = [
    {"content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."},
    {"content": "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."},
    {"content": "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."},
    {"content": "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."}
]

# Initialize LLModel instance
llmodel = LLModel()

# Check and adjust tokens in the messages list
processed_messages = llmodel.checkTokens(messages)

print(processed_messages)
```

**Expected Output:** The function will trim the messages in the list to ensure the total token count does not exceed the maximum limit specified.

#### Troubleshooting:
- If the function does not properly adjust the messages, ensure that the token count calculation is accurate and correctly compares it with the maximum limit.
- Check the logic for removing excess messages to guarantee that only the necessary messages are trimmed based on token count.
Below is an example for the `getPriceFromMsgs` function from the `llmodel.py` file:

### Function Overview:
The `getPriceFromMsgs` function calculates the price based on the number of tokens in a list of messages, considering the input price specified in the model parameters.

### Example:
```python
def getPriceFromMsgs(msgs):
    """
    Calculate the price based on the total number of tokens in a list of messages.
    
    Args:
    msgs (list): List of messages containing text content.
    
    Returns:
    tokens (int): Total number of tokens in the messages.
    price (float): Price calculated based on the token count and input price.
    """
    tokens = 0
    for msg in msgs:
        tokens += getTokensCount(msg["content"])  # Assuming getTokensCount function is defined and returns token count for text
    price = tokens * self.params['input'] / 1000  # Calculating price based on input price per token
    return tokens, price
```

### Basic Usage:
```python
# Define a list of messages
messages = [
    {"content": "Hello, how are you?"},
    {"content": "I'm doing well, thank you."},
    {"content": "What are you up to today?"}
]

# Calculate the price based on the messages
total_tokens, total_price = getPriceFromMsgs(messages)

print("Total Tokens:", total_tokens)
print("Total Price:", total_price)
```

### Advanced Usage:
```python
# Extend the messages list with additional messages
messages.append({"content": "Just finished a project and relaxing now."})

# Adjust the input price in the model parameters
# Assuming model price is in tokens per $0.001
model_params['input'] = 1  # Updated input price to 1 token per $0.001

# Recalculate the price based on updated parameters
new_total_tokens, new_total_price = getPriceFromMsgs(messages)

print("New Total Tokens:", new_total_tokens)
print("New Total Price:", new_total_price)
```

### Expected Output:
```
Total Tokens: 20
Total Price: 0.02
New Total Tokens: 25
New Total Price: 0.025
```

### Troubleshooting Tips:
- Ensure the `getTokensCount` function is implemented correctly to get the token count for text.
- Check and update the model parameters if needed for accurate price calculations.

### Feedback:
Feel free to test the example and provide feedback on its clarity and usefulness! Let me know if you have any suggestions for improvement or need further assistance.
### Function: `addCounterToPromts`

#### Introduction:
This function is responsible for updating a counter with the cost of tokens used for generating responses based on the pricing specified for the model. It tracks and aggregates the price of tokens used for chat completions on a daily basis.

#### Key Features:
1. Updates a counter with the cost of tokens used.
2. Aggregates the price of tokens daily in a JSON file.
3. Handles token pricing based on the model configurations.

#### Example 1: Basic Usage
```python
def addCounterToPrompts(token_num=1, price=0.002):
    """
    Adds the cost of tokens used for generating responses to the counter.

    Parameters:
    - token_num (int): Number of tokens used.
    - price (float): Price per token in cents.
    """
    addCounterToPrompts()  # Default parameters
```

#### Expected Output:
No output as the function is for updating the counter internally.

#### Example 2: Adding Real Data
```python
# Assuming 200 tokens were used at $0.0015 per token
addCounterToPrompts(token_num=200, price=0.0015)
```

#### Expected Output:
The function will update the counter with the calculated cost based on the provided token count and price.

#### Troubleshooting Tips:
- Ensure the `token_num` and `price` parameters are correctly passed to the function.
- Check the format and validity of the JSON file storing the daily aggregated token prices.
- Verify that the function is called in the appropriate context within the application flow.

#### Additional Note:
Make sure to monitor the counter regularly to track the costs accurately and manage the budget effectively.
**Function: createChatCompletion**

**Description:**
This function generates chat completions based on input messages using a specified language model. It checks for the number of tokens in the messages, manages pricing based on token count, and stores pricing information for each interaction.

**Key Features and Functionalities:**
1. Select language model based on parameters.
2. Handle token count and pricing for messages.
3. Store pricing information for interactions.
4. Generate chat completions using the specified model.

**Example 1: Basic Usage**
```python
# Create an instance of LLModel
model = LLModel()

# Define input messages
messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "How can I help you?"}]

# Generate chat completion
success, response, output = model.createChatCompletion(messages)

if success:
    print(response)
```

**Expected Output:**  
The function should generate a chat completion response for the input messages using the default language model.

**Example 2: Managing Token Count**
```python
# Create an instance of LLModel with custom parameters
params = {'model': 'gpt-3.5-turbo', 'max_tokens': 100}
model = LLModel(params)

# Define input messages exceeding maximum token count
messages = [{"role": "user", "content": "Lorem ipsum " * 50}]

# Generate chat completion considering token count limit
success, response, output = model.createChatCompletion(messages)

if success:
    print(response)
```

**Expected Output:**  
The function should trim the input messages to stay within the specified token count limit and generate a chat completion response.

**Example 3: Pricing Information**
```python
# Create an instance of LLModel with pricing parameters
params = {'model': 'gpt-3.5-turbo', 'input': 2}
model = LLModel(params)

# Define input messages for price calculation
messages = [{"role": "user", "content": "How are you?"}]

# Calculate the price for the input messages
tokens, price = model.getPriceFromMsgs(messages)
print(f"Token count: {tokens}, Price: ${price}")
```

**Expected Output:**  
The function should calculate the token count and pricing based on the input messages and the specified price per token.

**Troubleshooting Tips:**  
- Ensure the input messages conform to the expected format.
- Check that the specified language model and parameters are valid.
- Verify that the token count calculation aligns with the tokenization method used.

Feel free to test these examples and provide any feedback or suggestions for improvement!
### LLModel_class

**Brief Description:**
The `LLModel_class` represents a class that initializes and interacts with language models for generating chat completions.

**Parameters (`Args`):**
- `params` (dict): A dictionary containing parameters for setting up the language model and interaction.
- `messages` (list): A list of message dictionaries representing the conversation context for generating chat completions.

**Returns:**
- A tuple containing:
    - `success` (bool): Indicates if the generation process was successful.
    - `response` (str): The generated chat completion response.
    - `output` (dict): Additional information about the completion process.

**Raises:**
- No specific exceptions are raised by this function.

**Examples:**
```python
params = {'type': 'model', 'model': 'gpt-3.5-turbo'}
ll_model = LLModel(params)
messages = [{'role': 'user', 'content': 'Hello'}]
success, response, output = ll_model.createChatCompletion(messages)
print(success, response)
```

**Notes or Warnings (Optional):**
- This class interacts with different language models such as OpenAI and Ollama based on the provided parameters.
- It includes methods for creating chat completions, calculating token counts, and determining pricing based on input text.

**Other Sections (Optional):**
- The class handles counter updates for prompt tokens and saves pricing information to a JSON file for tracking costs.
```python
def checkTokens(in_msgs: list) -> list:
    """
    Brief Description:
    Check the total number of tokens in the concatenated messages and adjust if it exceeds the maximum token limit.

    Parameters (Args):
    - in_msgs (list): List of messages where each message is a dictionary with 'content' key containing the text content.

    Returns:
    - list: Modified list of messages after adjusting to comply with the maximum token limit.

    Raises:
    - None

    Examples:
    1. msgs = [
        {"content": "Hello, how are you?"},
        {"content": "I'm doing well, thanks for asking."},
        {"content": "What do you think about this topic?"}
    ]
    adjusted_msgs = checkTokens(msgs)
    # Output: [{'content': "I'm doing well, thanks for asking."}, {'content': 'What do you think about this topic?'}]

    2. msgs = [
        {"content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."},
        {"content": "Pellentesque habitant morbi tristique senectus et netus et."},
        {"content": "Curabitur vel porttitor quam."}
    ]
    adjusted_msgs = checkTokens(msgs)
    # Output: [{'content': 'Pellentesque habitant morbi tristique senectus et netus et.'}, {'content': 'Curabitur vel porttitor quam.'}]

    Notes or Warnings:
    - This function ensures that the total number of tokens in the messages does not exceed the specified maximum token limit.
    - If the total number of tokens is higher than the limit, messages are trimmed from the beginning until the limit is met.
    """
    # Function logic goes here
    pass
```
This template provides a structured and informative overview of the `checkTokens` function. Feel free to integrate it into your documentation.
### getPriceFromMsgs Function

#### Brief Description:
The `getPriceFromMsgs` function calculates the total price based on the number of tokens extracted from a list of messages, considering the specified input price per token.

#### Parameters:
- `msgs`: List of dictionaries representing messages.
  - Type: List
  - Description: The list of messages from which the total number of tokens is calculated.

#### Returns:
- Tuple containing the total number of tokens and the corresponding price.
  - Type: Tuple (int, float)
  - Description: The first value represents the total number of tokens calculated from the messages, and the second value indicates the total price derived from multiplying the input price per token.

#### Raises:
None

#### Examples:
```python
# Example 1:
messages = [
    {"content": "Hello, how are you?"},
    {"content": "I'm doing well, thank you for asking!"},
    {"content": "What have you been up to lately?"}
]

total_tokens, total_price = getPriceFromMsgs(messages)
print("Total Tokens:", total_tokens)
print("Total Price:", total_price)

# Expected Output:
# Total Tokens: [Number of tokens calculated from messages]
# Total Price: [Total price calculated based on the input price per token]

```

#### Notes or Warnings:
- Ensure that the `msgs` parameter is in the correct format, containing the required message information.
- The function solely calculates the total price based on the token count and the specified input price without external dependencies or complex computations.

#### Other Sections:
None
**`addCounterToPromts` Function**

**Brief Description:**
This function updates the counter for the prompts used during model interactions. It calculates the price based on the number of tokens and adds it to the total sum for the current date.

**Parameters (`Args`):**
- `token_num` (int): The number of tokens to be added to the counter.
- `price` (float): The price per token in the specified currency.

**Returns:**
- None

**Raises:**
This function does not raise any exceptions.

**Examples:**
```python
# Example 1:
addCounterToPromts(token_num=500, price=0.002)
# Output: price=  1.0

# Example 2:
addCounterToPromts(token_num=1000, price=0.0015)
# Output: price=  1.5
```

**Notes or Warnings (Optional):**
- Ensure that the `token_num` and `price` parameters are provided with the correct data types to calculate the sum accurately.

**Other Sections (Optional):**
- This function interacts with the file system to update the total sum for the current date in a JSON file.
### `createChatCompletion`

- **Brief Description:** This function generates a response based on the input messages using a specified model.

- **Parameters (`Args`):**
    - `messages` (list): A list of dictionaries where each dictionary represents a message with keys `"role"` and `"content"`. The `"role"` indicates the sender of the message, and `"content"` contains the message text.

- **Returns:** 
    - A tuple `(bool, str, dict)` where:
        - `bool`: Represents the success status of the operation.
        - `str`: The generated response text.
        - `dict`: Additional information such as the model used and other parameters.

- **Raises:** This function does not raise any exceptions.

- **Examples:**
    ```python
    messages = [
        {"role": "user", "content": "Hi, how are you?"},
        {"role": "assistant", "content": "I'm doing fine. How can I help you?"},
        {"role": "user", "content": "Can you provide some information about python programming?"},
    ]
    
    success, response, details = createChatCompletion(messages)
    print(success)  # True if successful
    print(response)  # Generated response based on input messages
    print(details)  # Additional information about the model and parameters used
    ```

- **Notes or Warnings (Optional):** 
    - Ensure that the `messages` list is properly formatted with `"role"` and `"content"` keys in each dictionary.
    - The function may adjust the input messages if the total token count exceeds the maximum allowed tokens for the model.

- **Other Sections (Optional):** 
    - The function internally handles token count checks and response generation, ensuring efficient use of the specified model.

# Recomendations
##Recommendations for function

LLModel_class


```python
from typing import List, Dict, Optional, Callable, NoReturn

class LLModel:
    def __init__(self, params: Optional[Dict[str, str]] = None) -> None:
        """
        Initialize the LLModel with the specified parameters.

        Args:
            params (Optional[Dict[str, str]]): Parameters to configure the model.
        """
        self.temperature: Optional[float] = None  # Temperature parameter for text generation
        self.active: bool = False  # Indicates if the model is active
        self.path: str = ""  # Path to configuration file
        self.path_to_file: str = ""  # Path to the output file
        self.method: Callable = lambda: None  # Function for model interaction
        self.vendor: str = ""  # Model vendor
        self.model: str = ""  # Model name
        self.api_key: str = ""  # API key for model access
        self.params: Dict[str, str] = {}  # Model parameters

    def createChatCompletion(self, messages: List[Dict[str, str]]) -> Tuple[bool, str, Dict]:
        """
        Generate chat completions based on input messages.

        Args:
            messages (List[Dict[str, str]]): List of messages exchanged in the chat.

        Returns:
            Tuple[bool, str, Dict]: A tuple containing success status, response text, and additional data.
        """
        return False, '', {}

    def addCounterToPrompts(self, token_num: int = 1, price: float = 0.002) -> None:
        """
        Update the cost counter based on the number of tokens and price.

        Args:
            token_num (int): Number of tokens to add to the counter
            price (float): Price per token
        """
        pass

    # Other method docstrings follow a similar format
```

In the `LLModel` class, inline comments are utilized to provide brief explanations of the purpose and usage of attributes and methods. This approach helps in understanding the code structure and functionality without overwhelming the reader with extensive comments. The comments focus on essential information and guide the reader through the class implementation.

##Recommendations for function

checkTokens


In the `checkTokens` function, comments are added to provide insights into the purpose and logic behind the code:

```python
from typing import List

def checkTokens(in_msgs: List[dict]) -> List[dict]:
    """
    Check if the total number of tokens in the concatenated messages exceeds the maximum allowed tokens.

    Args:
    in_msgs (List[dict]): List of messages where each message is a dictionary with the 'content' key.

    Returns:
    List[dict]: Filtered list of messages that do not exceed the maximum token limit.
    """
    
    msgs: List[dict] = in_msgs.copy()
    text: str = ''
    
    # Concatenate messages to calculate the total token count
    for msg in msgs:
        text += msg["content"]
    
    token_cnt: int = getTokensCount(text)
    
    # Ensure the total number of tokens in the concatenated messages does not exceed the maximum allowed tokens

    if token_cnt > self.params['max_tokens']:
        idx: int = 0
        
        # Remove messages until the token count is within the limit
        while idx < 1000 and token_cnt > self.params['max_tokens']:
            msgs.pop(0)
            text = ""
            for msg in msgs:
                text += msg["content"]
            token_cnt = getTokensCount(text)
            idx += 1
    
    return msgs
```

In the updated version:
- Comments are added to explain the purpose of concatenating messages and tracking the token count.
- The logic of removing messages to adhere to the token limit is clarified using comments.
- Inline comments provide insight into why specific actions are taken to optimize the code.
- By documenting the code decisions and functionalities in comments, the readability and maintainability of the function are enhanced.

##Recommendations for function

getPriceFromMsgs


```python
from typing import List, Tuple

def getPriceFromMsgs(msgs: List[dict]) -> Tuple[int, float]:
    # Calculate the total token count and price based on the input messages

    tokens = 0

    # If the vendor is OpenAI, determine the total token count
    # This calculation is specific to the OpenAI vendor
    if self.vendor == 'openai':
        tokens = openai_num_tokens_from_messages(msgs, self.model)

    # Retrieve the input price from the model parameters
    price = self.params['input']

    # Calculate the total price by multiplying the token count with the price per token
    total_price = tokens * price / 1000

    return tokens, total_price
```

In this version:
- The purpose of the function is explained at the beginning of the code comment.
- Inline comments clarify the logic behind calculating the token count and price.
- Comments document the specific logic related to the OpenAI vendor's token count calculation.
- The code is kept concise to ensure that comments supplement understanding without overshadowing the code itself.

##Recommendations for function

addCounterToPromts


In the updated `addCounterToPromts` function, comments have been added to explain the purpose and logic of the code:

```python
from typing import NoReturn

class LLModel:
    """
    Implements a model for handling chat completions and updating counters.

    This module provides functionality related to chat completions using different models 
    and updates counters with calculated prices.
    """

    # Other class methods...

    def addCounterToPromts(self, token_num: int = 1, price: float = 0.002) -> NoReturn:
        """
        Update the counter with the calculated price based on token count and price per token.

        Parameters:
            token_num (int): Number of tokens to add to the counter.
            price (float): Price per token in the specified currency.

        Returns:
            None

        Example:
            model = LLModel()
            model.addCounterToPromts(100, 0.002)
        """
        
        # Calculate the total price based on the token count
        sum_price = token_num * price / 1000

        # Print the calculated price
        print('price= ', sum_price)

        # Update the counter in the file
        cur_date = str(datetime.date.today())
        if os.path.exists(self.path_to_file):  # Check if the output file exists
            with open(self.path_to_file, 'r') as f:
                dates = json.load(f)
                found = False
                for dt in dates:
                    # Update the existing date's sum
                    if dt["date"] == cur_date:
                        found = True
                        sum_val = dt["sum"] + sum_price
                        dt["sum"] = sum_val
                if not found:
                    # Add a new entry for the current date
                    dates.append({"date": cur_date, "sum": sum_price})
            with open(self.path_to_file, 'w') as f:
                # Save the updated data back to the file
                json.dump(dates, f, indent=1)
        else:
            # If the file does not exist, create a new entry
            with open(self.path_to_file, 'w') as f:
                val = []
                val.append({"date": cur_date, "sum": sum_price})
                json.dump(val, f, indent=1)

    # Other methods...
```

The comments added aim to clarify the purpose of the code, explain complex logic involved, and provide insights into the flow of the function for better understanding.

##Recommendations for function

createChatCompletion


```python
class LLModel:
    def createChatCompletion(self, messages: List[Dict[str, str]]) -> Tuple[bool, str, Dict[str, Union[str, str]]]:
        """
        Generates a chat completion response based on input messages.

        Parameters:
        - messages (List[Dict[str, str]]): A list of message dictionaries containing role and content.

        Returns:
        Tuple[bool, str, Dict[str, str]]: A tuple containing completion success status, response text, and additional info.

        This method is essential for processing user messages and generating chat completions. 
        It acts as the core functionality of the LLModel class by interacting with language models.

        The logic of this function involves tokenizing input messages, calling the corresponding model method,
        and handling the response generation process based on the model's output.
        
        Performance: The function aims to optimize token usage and manage response generation efficiently.
        Comments are used to explain the token count calculations and price updates for billing purposes.

        It's crucial to keep the inline comments concise and relevant to ensure clarity and facilitate code review.
        Consider updating comments as code changes to maintain synchronization between comments and the code.

        It's advisable to avoid over-commenting to prevent unnecessary clutter and ensure that essential comments are prominent.
        Peers are encouraged to review the comments to confirm their coherence and value during code reviews.
        """

        if not self.active:
            return False, '', {}
        
        # Check and adjust message tokens to optimize for maximum token limit
        messages = self.checkTokens(messages)
        
        out: Dict[str, str] = {
            'type': 'response',
            'model': self.params['model']
        }
        
        res: bool
        response: str
        p: Dict[str, str]
        
        # Call the model method for generating chat completions
        res, response, p = self.method(messages, self.params)
        
        # Update token counts and prices based on the response parameters
        if res and 'intok' in p and 'outtok' in p:
            intok: str = p['intok']
            outtok: str = p['outtok']
            out.update(p)
    
            self.addCounterToPromts(intok, self.params['input'])
            self.addCounterToPromts(outtok, self.params['output'])
        
        return res, response, out
```

In the updated `createChatCompletion` function, inline comments are used to explain the purpose of the code, highlight the logic flow, and document performance considerations.These comments provide insights into the functionality, optimization strategies, and billing-related operations within the function.


