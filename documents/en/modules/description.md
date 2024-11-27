# Democratizing Software Development with Natural Language

The main goal of this project is to democratize software development by enabling the creation of fully functional programs using **natural language**, eliminating the need for traditional programming languages like Python, Java, or C++. This empowers anyone, regardless of coding expertise, to bring their software ideas to life. Users won't require programming knowledge or even see the underlying source code; the system handles the technical details behind the scenes.

## The Problem

Currently, the biggest barrier to software development is the need for deep knowledge of programming languages and specialized (often outdated and inaccessible) libraries (legacy code). This expertise requirement excludes a vast majority and makes development costly and time-consuming.

## Our Solution

Our approach simplifies development through **interactive blocks**, like a construction set. Users connect these blocks visually, describing the desired functionality.  By linking blocks and specifying actions, users define the software's behavior.

* **LLM-powered Code Generation:**  An LLM interprets the block connections and generates the underlying code, automating the translation from design to working program.

* **Built-in Documentation:** Each block contains an instruction, and these instructions collectively form the documentation.  This inherent link between functionality and documentation ensures clarity and keeps it always up-to-date. The instructions used to create the program *are* the documentation, simplifying understanding and maintenance. This eliminates the gap between code and documentation common in traditional development.

* **Graphical Dialogues for Libraries:** We transform libraries into graphical dialogues – instructions linked to code.  These dialogues provide a visual and interactive way to access and utilize library functionalities. The system maintains perfect synchronization between instructions and the program. Any changes to instructions are automatically reflected in the code, ensuring consistently up-to-date documentation.

## Empowering Domain Experts

This approach empowers specialists from diverse fields (physicists, medical professionals, construction workers) to create their own tools using their professional knowledge. They can leverage their expertise to build tailored software without needing programming skills.

# LLM Prompt Engineering Project

This open-source project (MIT License) simplifies working with Large Language Models (LLMs) by enabling rapid creation and testing of prompts for text and code generation.  Developed by a single programmer over a year, a basic working version (MVP) is now available.  The primary goal is to discover optimal prompts for solving programming problems with LLMs.

## Core Hypothesis

By strategically combining and ordering prompts, any code can be generated from any LLM.  The user acts as a constructor, blending data, instructions, and the model's synthetic output to refine the final result.

## Features

* **Dialogue Creation:**  Establish and maintain a dialogue with LLMs.
* **Prompt Engineering:**  Craft and refine prompts for optimal performance.
* **Dialogue Management:** Edit, modify, and reorder prompts within a dialogue. Transfer context and information between dialogues to preserve coherent LLM interaction.
* **Auxiliary Tools:**  Facilitate data manipulation (reading/writing) and execution of generated scripts.

## Example Use Cases

* **Encryption Mapping Verification Tool:** Develop tools to verify mapping in encryption tasks.
* **Automated Article Relevance Analysis:** Automate the analysis of articles for relevance to a specific topic.
* **Text Enhancement & Editing:** Improve and edit text using LLMs.
* [**No-Code Programming:**](no-code.md) Generate programs solely through LLM prompts, eliminating manual coding.
