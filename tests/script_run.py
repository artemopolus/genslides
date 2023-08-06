# import subprocess

# # Specify the path of the Python script to run
# script_path = r"browsing_by_gpt.py"

# # Run the Python script
# process = subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

# # Read the output and error streams
# output, error = process.communicate()

# # Print the execution results
# print("--- Output ---")
# print(output.decode())
# print("--- Error ---")
# print(error.decode())

import subprocess

# Define the path to the Python script
script_path = "browsing_by_gpt.py"

# Run the script and capture the output
result = subprocess.run(["python3.11.exe", script_path], capture_output=True, text=True)

# Print the script output
print(result.stdout)
