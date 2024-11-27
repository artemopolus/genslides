## Quick Start

To quickly set up GenSlides, follow these steps:

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
1.1 Maybe you have to install:
```shell
sudo apt-get install python3.12-venv
```
change 3.12 on your version

2. Install the necessary dependencies:
    ```shell
    python -m pip install -r requirements.txt
    python -m nltk.downloader popular
    ```
2.1 Install tkinter for your version of python

   ```shell
   sudo apt-get install python3-tk
   ```
2.2 If error: ModuleNotFoundError: No module named 'distutils'

```shell
   python -m pip install setuptools
```

3. Install Graphviz:

   - Windows: Download and install from [Graphviz Download Page](https://www.graphviz.org/download/)
   - Ubuntu: Run 
   ```shell
   sudo apt-get install graphviz
   ```

4. Obtain your API keys:
   - OpenAI API: Obtain from [OpenAI API Keys](https://platform.openai.com/account/api-keys)
   - Google API: Follow the quickstart guide at [Google Docs API](https://developers.google.com/docs/api/quickstart/python)

5. Set up your API configuration:
   - Copy the `config` folder from the examples to the root directory.
   - Input your API keys into `google.json` and `openai.json`.

6. Finally, run the following command to start GenSlides:
    ```shell
    python -m genslides
    ```

## How to Update

For developers looking to update requirements or install new libraries, use:

```shell
python -m pip freeze > requirements.txt
python -m pip install target_lib
```

