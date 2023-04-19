# **** Commands to Run LLM Repo Assistant API Locally ****
# Set the image and container names
IMAGE_NAME := llm_repo_assistant
CONTAINER_NAME := llm_repo_assistant

# Environment variables here are examples, should be set as environment
# variables when running this makefile.
# Set the path for the LLM Repo Assistant FastAPI app
FASTAPI_APP_PATH ?=
# Set the path for the code repository the app will work with
CODE_REPO_PATH ?=

.PHONY: build
build:
ifndef FASTAPI_APP_PATH
	$(error FASTAPI_APP_PATH is not set. Please set it to the path of your FastAPI app directory)
endif
ifndef CODE_REPO_PATH
	$(error CODE_REPO_PATH is not set. Please set it to the path of your code repository)
endif
	docker build -t $(IMAGE_NAME) .

.PHONY: run
run:
ifndef FASTAPI_APP_PATH
	$(error FASTAPI_APP_PATH is not set. Please set it to the path of your FastAPI app directory)
endif
ifndef CODE_REPO_PATH
	$(error CODE_REPO_PATH is not set. Please set it to the path of your code repository)
endif
	docker run -v "$(FASTAPI_APP_PATH):/app" -v "$(CODE_REPO_PATH):/repo" -p 8000:8000 --name $(CONTAINER_NAME) $(IMAGE_NAME)

.PHONY: test
test:
ifndef FASTAPI_APP_PATH
	$(error FASTAPI_APP_PATH is not set. Please set it to the path of your FastAPI app directory)
endif
ifndef CODE_REPO_PATH
	$(error CODE_REPO_PATH is not set. Please set it to the path of your code repository)
endif
	docker exec -it $(CONTAINER_NAME) pytest

.PHONY: stop
stop:
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)
