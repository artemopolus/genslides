import sys
import json
import argparse
from pathlib import Path, PureWindowsPath

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import genslides.task_tools.text as Text

src_text = """
I want to create new IMU Data Analysis project. I've used Gradio before, but I'm willing to learn PyQt if it's better suited for this project. I'm a beginner with PyQt, so I need guidance on getting started and understanding the basics. I need advanced customization options and the ability to embed complex widgets like plot windows. I have intermediate experience with Python, having completed a few projects using libraries like Matplotlib and Pandas. I've used Gradio for simple UIs but haven't worked with PyQt before.
I want create pyqt gui for IMU Data Analysis project.

I've used virtual environments before with uv and venv.

Path to project is J:\SyncFolder\workspace\llmprojects\code_generator\generated\imudatas.

Project goal is analysis of collected data. Project parts:

GUI.
Core.
I'd like the GUI to handle user inputs and then pass them to the core functions for processing.
I don't have any existing code, but I'm familiar with the libraries mentioned and plan to write new code from scratch.
Data format: custom text file. There are three columns in file for X, Y, Z data. The file is a CSV with headers 'X', 'Y', 'Z' and values separated by tabs.

Project functions:

Load saved data from IMU.
Analyze raw data in text format.
Plot data.
Analyze data with different methods.
I would like to include options to export the analyzed data as CSV files.
Methods for Analysis data
Let's start with filtering and smoothing, and we can add more methods later. I would like to start with a simple moving average for smoothing the data. Later, I might consider using a low-pass filter.

GUI elements
Buttons:

Load data via browsing
Reload data. The 'Reload data' button should refresh the current dataset without re-opening the file dialog, allowing users to quickly re-analyze the same data without additional file selection steps.
Draw data
Save as. The analyzed data should be saved in the another CSV format.
Dropdowns:

Select method
Select data to plot: X, Y, Z
Windows:

For plot data
Including a log window for displaying messages or errors would be helpful, as well as a help menu with instructions on how to use the different functionalities of the GUI.
Structure
Folders for store gui and core. I prefer having a structure like this:

`imudatas/
gui/
core/
data/
scripts/`'
Libraries
I'm familiar with Pandas and NumPy, and I've used Matplotlib before. I'm open to using them for this project. I'd like to use Seaborn for better visualization options, but I'm open to suggestions.

Design
A basic template would be great to get started.

I'm open to suggestions for the design. I'm looking for a user-friendly interface that's easy to navigate. I prefer a clean and modern look, maybe something like the default macOS theme.

Embedding Plot Window within the main GUI would be preferable for easier navigation. The plot window should be resizable, with options for zooming and panning to allow users to closely inspect specific data points.

A grid layout with buttons and dropdowns centered and the plot window below them would work well.

Performance is not a major concern, but I'd like the application to be reasonably fast and responsive.

I'd like to use Seaborn's line plots with grid lines and a legend to differentiate between the X, Y, and Z data.

Guidelines for Proposing Changes to the Program Description

Markers in the Program Description Text use the format [Aa123].
Maintain a neutral, objective tone.
Assume the reader has no prior knowledge of the original content.
Read text of Program Description above:

Understand Structure of the Text.
Understand Valid Marker Format.
Identify parts of the Text based on Markers.
Find logical parts of the Text.
Try to break the Text on two half parts and write start Markers of each half part.
Response using provided Json Schema.
"""

before = "I'd like the GUI to handle user inputs and then pass them to the core functions for processing."

after = "Data format: custom text file. There are three columns in file for X, Y, Z data. The file is a CSV with headers 'X', 'Y', 'Z' and values separated by tabs."


similar_sentence, score, start_pos, end_pos_above = Text.find_most_similar_simple( before, src_text )

print("\n--- Results (Simple Word Count) ---")
# print(f"Query Sentence: '{query}'")
print(f"Most Similar Sentence Found: '{similar_sentence}'")
print(f"Shared Word Count: {score}")
print(f"Start Position: {start_pos}")

