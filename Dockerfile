# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install Git
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install virtualenv

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Create a virtual environment for the target repo and install its requirements if available
# This must be defined in a file llm_target_repo_requirements.txt
RUN virtualenv /venv
COPY ./llm_target_repo_requirements.txt /llm_target_repo_requirements.txt
RUN if [ -f /llm_target_repo_requirements.txt ]; then /venv/bin/pip install -r /llm_target_repo_requirements.txt; fi

# Copy the rest of the application code
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
