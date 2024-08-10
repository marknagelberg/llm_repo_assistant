# LLM Repo Assistant

LLM Repo Assistant provides an API intended for a Language Model (LLM) to interact with
a target code repository and dramatically increase your productivity as a developer.
The API enables an LLM to view the directory structure, read files, write files,
execute tests, get language-specific code summaries, and write language-specific
code.

It is designed to be usable as a ChatGPT plugin, allowing you do leverage the
power of ChatGPT to edit a repo from within ChatGPT. It can of course also
work with any LLM that is able to understand and interact with HTTP APIs.

See a basic demo [here](https://x.com/MarkNagelberg/status/1652074221898723329)
demonstrating some of LLM Repo Assistant's capabilities.

## WARNING

This is in early stages of development. It provides the LLM with read
and write access to your repo, so use at your own risk. Be sure to track your
repo with version control so you can revert unwanted changes from the LLM and
also create a full backup of your repo.

## Features

- **File System Operations**: Perform common file system operations such as
reading, writing, and deleting files, as well as creating and managing directories.
- **Code Editing**: Retrieve high-level class and function signatures,
get class and function definitions, and update or create new class and function definitions.
Also read and create code documentation. (Python only)
- **Command Line Execution**: Set up a configuration file for particular command line commands
you want the LLM to be able to run in your repo's environment.

## Getting Started

We call the repo you want to edit / work on the "target repo".
To get started with LLM Repo Assistant, follow these steps:

1. Install Docker
2. Clone the LLM Repo Assistant repo
3. Add an `.llmignore` file to the root directory of your target repo - this tells
LLM Repo Assistant about files in your target repo that you want ignored by the LLM.
4. Build the docker image that defines the environment for your target repo. 
5. Navigate to the `llm_repo_assistant` cloned repository and build the
Docker image to run LLM Repo Assistant with `docker build -t llm_repo_assistant .`
6. Create an `.env` file in the `llm_repo_assistant` root directory that follows the template
of `.env-template`.
7. Run LLM Repo Assistant with `make run`.
8. View and test the API endpoints by visiting `localhost:8000/docs`

## Adding ChatGPT plugin

To add a ChatGPT plugin to work with the API, follow these steps:

1. Gain access to OpenAPI ChatGPT plugin development
2. Run LLM Repo Assistant locally using the instructions above
3. Go to `Plugin store` -> `Develop your own plugin`, enter `localhost:8000`,
and click `Find manifest file`
4. The plugin should now be available to use by ChatGPT

## Configuring Command Endpoints

Command endpoints in the FastAPI application can be dynamically configured using the `command_config.yml` file. 
This YAML configuration file allows you to specify a variety of command line commands that the Language Learning Model (LLM) can execute.

Here's the basic structure of a command configuration:

```yaml
commands:
  - name: endpoint_name
    command: command_name
    description: endpoint_description
    args:
      - name: arg_name
        description: arg_description
        is_directory_or_file: true/false
        optional: true/false
    flags:
      - name: flag_name
        is_short: true/false
        type: flag_type
        description: flag_description
        optional: true/false
```

### Fields

Each configuration contains the following fields:

-  `name`: The name of the command endpoint. This will be used in the URL route.
-  `command`: The command line command the LLM should run.
-  `description`: A brief explanation of what the command does.

Under `args`, you can specify arguments for the command:

-  `name`: The name of the argument or flag.
-  `description`: A brief explanation of what the argument or flag does.
-  `is_directory_or_file`: Specifies whether the argument represents a directory or file in the target repo. This ensures the file / directory is prepended with the appropriate path in the target repo docker container. Accepts `true` or `false`.
-  `optional`: Specifies whether the argument or flag is optional. Accepts `true` or `false`.

Under `flags`, you can specify  flags for the command:

-  `name`: The name of the argument or flag.
-  `description`: A brief explanation of what the argument or flag does.
-  `is_short`: Specifies if the flag name is short (e.g., `-x`) or long (e.g., `--exclude`). Accepts true or false.
-  `type`: The data type of the argument or flag. Can be `str` or `bool`. If `bool`, the flag does not have a value.
-  `optional`: Specifies whether the argument or flag is optional. Accepts `true` or `false`.


## Future Features

- Add support for other languages

## Contributing

We appreciate any contributions to the LLM Repo Assistant project! To get started with contributing, please read our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on reporting issues, suggesting features, and submitting code changes.
