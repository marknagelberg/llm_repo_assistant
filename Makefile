# **** Commands to Run LLM Repo Assistant API Locally ****

# Load environment variables from .env file
include .env
export

# Set the image and container names
IMAGE_NAME := llm_repo_assistant
CONTAINER_NAME := llm_repo_assistant

# Environment variables here are examples, should be set as environment
# variables when running this makefile.
# Set the path for the LLM Repo Assistant FastAPI app
LLM_REPO_ASSISTANT_PATH ?=
# Set the path for the code repository the app will work with
CODE_REPO_PATH ?=

.PHONY: run
run:
ifndef LLM_REPO_ASSISTANT_PATH
	$(error LLM_REPO_ASSISTANT_PATH is not set. Please set it to the path of your FastAPI app directory)
endif
ifndef TARGET_REPO_PATH
	$(error TARGET_REPO_PATH is not set. Please set it to the path of your code repository)
endif
	docker run --rm -v "/var/run/docker.sock:/var/run/docker.sock" -v "$(LLM_REPO_ASSISTANT_PATH):/app" -v "$(TARGET_REPO_PATH):/repo" -p 8000:8000 --name $(CONTAINER_NAME) $(IMAGE_NAME)
