import subprocess

# Define the path to the Python script
script_path = "browsing_by_gpt.py"

path_to_main = "J:/WorkspaceFast/llama.cpp/build/bin/Release/main.exe"

path_to_model = "J:/WorkspaceFast/llm/llama-2-13b-chat.Q5_K_M.gguf"

prompt = "Hello"

# Run the script and capture the output

script_path = "J:\\WorkspaceFast\\llama.cpp\\build\\bin\\Release\\main.exe -m J:\\WorkspaceFast\\llm\\llama-2-13b-chat.Q5_K_M.gguf --prompt \"Hello\" -ngl 5 --responsefile J:\\WorkspaceFast\\genslides\\tests\\llm\\test.txt"

# result = subprocess.run([path_to_main, "-m",path_to_model,"--prompt",prompt,"-ngl 5"], capture_output=True, text=True)
result = subprocess.run(script_path, capture_output=True, text=True)

# Print the script output
print(result.stdout)
