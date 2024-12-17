# GenSlides

GenSlides is an innovative program designed to offer a user-friendly interface for interacting with language learning models (LLMs) like GPT-4. Instead of manually inputting data into the LLM and waiting for results, GenSlides streamlines the process through an intuitive dialog tree structure, where each branch is an independent dialog.

# Easy LLM Prompting Tool (Open Source)

This open-source project (MIT license) simplifies working with Large Language Models (LLMs) by allowing you to quickly create, test, and refine prompts for text and code generation.  Developed by a single programmer over a year, a basic working version (MVP) is now available. The primary goal is to discover optimal prompts for solving programming problems with LLMs.

The core hypothesis is that by strategically combining and ordering prompts, any code can be generated from any LLM.  The user acts as a constructor, blending data, instructions, and the model's output to refine the final result.

## Features

* **Dialogue Creation:**  Engage in a back-and-forth dialogue with LLMs.
* **Prompt Editing & Formulation:**  Craft and refine prompts for precise control.
* **Dialogue Management:** Edit, modify, and reorder prompts within a dialogue. Transfer context and information between dialogues to maintain coherent interaction with LLMs.
* **Auxiliary Tools:**  Utilize tools for data manipulation (reading/writing) and executing generated scripts.

## Use Cases

* Developing tools for verifying mapping in encryption tasks.
* Automated analysis of articles for topical relevance.
* Text improvement and editing using LLMs.
* Creating programs without manual coding through LLM prompts.


## Demo Video (Changing Dialogs)

[![Changing Dialogs](https://img.youtube.com/vi/R94lPnOrSY0/0.jpg)](https://www.youtube.com/watch?v=R94lPnOrSY0)

Versions:

- [на русском](./README.ru.md)

![Alt text](images/code.png)

- [Quick Start](./documents/en/modules/quick_start.md)
- [Description](./documents/en/modules/description.md)
- [Features](./documents/en/modules/features.md)




## Limitations

Please note that GenSlides is currently a prototype. Always report any errors you encounter and monitor your OpenAI API usage to avoid exceeding limits.

## Usage Examples

Here are some ways you can utilize GenSlides:

- Engage in step-by-step learning on various themes.
- Decompose problems and explore multiple solutions.
- Automate code generation and testing processes.
- Collect datasets from your thought chains for later use.
- Create automatic instructions and discover additional steps needed.
- Use sequential summarization to analyze tasks and improve comprehension.
- Test and iterate on scripts until the desired outcome is achieved.

## Roadmap

The following upcoming changes are scheduled for development:

- Creating project templates for users: Program Creation, Translator, Article/Message Analysis

- After creating project templates, the next step is to create detailed documentation on their use, which will provide users with the necessary information for their work.

- The developed project templates and their documentation will be tested in a closed user group to identify potential problems and get feedback before the public release.

- After successful testing in the closed group, we will publish a series of articles detailing the functionality and benefits of using the developed project templates.

- In the long term, we plan to improve the process of working with project templates by developing a more user-friendly and intuitive editor based on a modern 3D interface.


Please, check Issues

## License

GenSlides is released under the MIT License.

## Contact Information

For any inquiries, feel free to email us at artem.o.kuznecov@gmail.com.

## FAQ

**Q: How to disable debugging?**
A: Set the "active" flag in openai.json to "false" to prevent requests from being sent via OpenAI API.

**Q: Where can I find example projects?**
A: Check out the `examples` directory for project samples, and remember to copy them to the root for exploration.

For a visual guide, watch the explanatory video below:

[![GenSlides Guide](http://img.youtube.com/vi/tOZpFCOcqNA/0.jpg)](http://www.youtube.com/watch?v=tOZpFCOcqNA)

---

Genslides, proposing a new way to enhance your dialogue with AI.