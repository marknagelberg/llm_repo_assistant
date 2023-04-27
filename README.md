# LLM Repo Assistant

LLM Repo Assistant provides an API for a Language Model (LLM) to interact with
a target code repository and dramatically increase your productivity as a developer.
The API enables an LLM to view the directory structure, read files, write files,
execute tests, get language-specific code summaries, and write language-specific
code.

It is designed to be usable as a ChatGPT plugin, allowing you do leverage the
power of ChatGPT to edit a repo from within ChatGPT. It can of course also
work with any LLM that is able to understand and interact with HTTP APIs.

## WARNING

This is in early stages of development. It provides the LLM with read
and write access to your repo, so use at your own risk. Be sure to track your
repo with version control so you can revert unwanted changes from the LLM and
also create a full backup of your repo.

## Features

- **File System Operations**: Perform common file system operations such as
reading, writing, and deleting files, as well as creating and managing directories.
- **Code Editing**: Edit code files by line number, update entire files, and
insert new lines at specific locations.
- **Code Understanding**: Retrieve high-level class and function signatures,
get class and function definitions, and update or create new class and function definitions.
Also read and create code documentation.
- **Test Execution**: Run tests for your code repository using the integrated
test execution feature (only pytest for now)

## Supported Languages

- Python

## Getting Started

We call the repo you want to edit / work on the "target repo".
To get started with LLM Repo Assistant, follow these steps:

1. Install Docker
2. Clone the LLM Repo Assistant repo
3. Add an `.llmignore` file to the root directory of your target repo - this tells
LLM Repo Assistant about files in your target repo that you want ignored by the LLM.
4. If you want the API to be able to run tests on your target repo,
then edit the requirements file to the root directory of the LLM Repo Assistant repo
called `llm_target_repo_requirements.txt`. This file should define the python environment
your tests should run in and should include `pytest`.
5. Navigate to the `llm_repo_assistant` cloned repository and build the
Docker image to run LLM Repo Assistant with `docker build -t llm_repo_assistant .`
6. Run LLM Repo Assistant locally in a docker container with the following command:
`docker run --rm -v "/path/to/cloned/repo/llm_repo_assistant:/app" -v "/path/to/your/code/repo:/repo" -p 8000:8000 --name llm_repo_assistant llm_repo_assistant`
7. View and test the API endpoints by visiting `localhost:8000/docs`

### Adding ChatGPT plugin

To add a ChatGPT plugin to work with the API, follow these steps:

1. Gain access to OpenAPI ChatGPT plugin development
2. Run LLM Repo Assistant locally using the instructions above
3. Go to `Plugin store` -> `Develop your own plugin`, enter `localhost:8000`,
and click `Find manifest file`
4. The plugin should now be available to use by ChatGPT

## Roadmap

- Add support for different test suites
- Add JavaScript support

