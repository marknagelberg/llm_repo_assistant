# LLM Repo Assistant

LLM Repo Assistant provides an API for a Language Model (LLM) to interact with
your code repository and dramatically increase your productivity as a developer.
The API enables an LLM to view the directory structure, read files, write files,
execute tests, get language-specific code summaries, and write language-specific
code.

It is designed to be usable as a ChatGPT plugin, allowing you do leverage the
power of ChatGPT to edit your repo from within ChatGPT.

WARNING: This is in early stages of development. It provides the LLM with read
and write access to your repo, so use at your own risk. Be sure to track your
repo with version control so you can revert unwanted changes from the LLM.

## Features

- **File System Operations**: Perform common file system operations such as
reading, writing, and deleting files, as well as creating and managing directories.
- **Code Editing**: Edit code files by line number, update entire files, and
insert new lines at specific locations.
- **Code Understanding**: Retrieve high-level class and function signatures,
get class and function definitions, and update or create new class and function definitions.
- **Test Execution**: Run tests for your code repository using the integrated
test execution feature.
- **Code Summaries**: Get language-specific code summaries to understand the
structure and content of your code files.
- **Search and Utility Functions**: Search for files and directories,
move files or directories, and get the file structure of your repository.

## Supported Languages

- Python

## Getting Started

To get started with LLM Repo Assistant, follow these steps:

1. Clone the repo
2. Follow the `.env-template` example to create an `.env` file in the top
directory of this repo to define `REPO_ROOT` which points to the top level directory
of the repo you want the API to be able to read / edit.
3. Add an `.llmignore` file to the `REPO_ROOT` directory - this tells the API about
files in your repo that you want ignored by the LLM.
4. Run the API with `source start.sh`. The API should then be running on `localhost:8000`
5. View and test the API by visiting `localhost:8000/docs`

## Adding ChatGPT plugin

To add a ChatGPT plugin, follow these steps:

1. Gain access to OpenAPI ChatGPT plugin development
2. Run LLM Repo Assistant locally using the instructions earlier
3. Go to `Plugin store` -> `Develop your own plugin`, enter `localhost:8000`,
and click `Find manifest file`
4. The plugin should now be available to use by ChatGPT

