# ThoughtTuner

ThoughtTuner is an innovative program designed to offer a user-friendly interface for interacting with language learning models (LLMs) like GPT-4. Instead of manually inputting data into the LLM and waiting for results, ThoughtTuner streamlines the process through an intuitive dialog tree structure, where each branch is an independent dialog.

## Quick Start

To quickly set up ThoughtTuner, follow these steps:

1. Create a virtual environment and activate it:

   For window user:
    ```shell
    python -m venv .env
    .env\Scripts\Activate.ps1
    ```
 
   For Linux user:
    ```shell
    python3 -m venv .env
    source .env/bin/activate
    ```

2. Install the necessary dependencies:
    ```shell
    python -m pip install -r requirements.txt
    python -m nltk.downloader popular
    ```

3. Install Graphviz:

   - Windows: Download and install from [Graphviz Download Page](https://www.graphviz.org/download/)
   - Ubuntu: Run `sudo apt-get install graphviz`

4. Obtain your API keys:
   - OpenAI API: Obtain from [OpenAI API Keys](https://platform.openai.com/account/api-keys)
   - Google API: Follow the quickstart guide at [Google Docs API](https://developers.google.com/docs/api/quickstart/python)

5. Set up your API configuration:
   - Copy the `config` folder from the examples to the root directory.
   - Input your API keys into `google.json` and `openai.json`.

6. Finally, run the following command to start ThoughtTuner:
    ```shell
    python -m genslides
    ```

## How to Update

For developers looking to update requirements or install new libraries, use:

```shell
python -m pip freeze > requirements.txt
python -m pip install target_lib
```

## Limitations

Please note that ThoughtTuner is currently a prototype. Always report any errors you encounter and monitor your OpenAI API usage to avoid exceeding limits.

## Program Functionality

ThoughtTuner provides the following features:

- Create dialogs with user requests and LLM responses.
- Select which LLM model to use.
- Modify messages within dialogs.
- Record the history of changes to dialogs.
- Initiate new dialogs with portions of existing conversations.
- Merge different dialogs for comprehensive information.
- File reading and writing capabilities.
- Execute Python scripts and share your dialogs or dialog sets.
- Implement Automated Thought-Branch Transfer for replicating data branches.
- Facilitate Automated Inter-Tree Data Mirroring across different thought trees.

## Usage Examples

Here are some ways you can utilize ThoughtTuner:

- Engage in step-by-step learning on various themes.
- Decompose problems and explore multiple solutions.
- Automate code generation and testing processes.
- Collect datasets from your thought chains for later use.
- Create automatic instructions and discover additional steps needed.
- Use sequential summarization to analyze tasks and improve comprehension.
- Test and iterate on scripts until the desired outcome is achieved.

## Roadmap

The following upcoming changes are scheduled for development:

### General Enhancements:
- Task duplication and execution order modification tools.
- Project-centric ownership management with "projecter".

### Command Manager Updates:
- Default value settings and conventions-based task starting adjustments.
- Consolidation of settings in "projecter" and an introduction of "MakeAction."

### Task Management Improvements:
- Enhanced task copying and freezing for modification support.
- New test insertion and validation methods.

### Messaging System and UI/UX Optimizations:
- Improved notification system and parameter configuration.
- Functions for displaying the last message in tasks.

### Utility Functions Enhancements:
- Syntax and security updates, including random key generation for requests.

### Notes:
- Developers should clarify tasks during implementation.
- All changes will be tested and are subject to modification.

## License

ThoughtTuner is released under the MIT License.

## Contact Information

For any inquiries, feel free to email us at exactosim@gmail.com.

## FAQ

**Q: How to disable debugging?**
A: Set the "active" flag in openai.json to "false" to prevent requests from being sent via OpenAI API.

**Q: Where can I find example projects?**
A: Check out the `examples` directory for project samples, and remember to copy them to the root for exploration.

For a visual guide, watch the explanatory video below:

[![ThoughtTuner Guide](http://img.youtube.com/vi/tOZpFCOcqNA/0.jpg)](http://www.youtube.com/watch?v=tOZpFCOcqNA)

---

ThoughtTuner, proposing a new way to enhance your dialogue with AI.