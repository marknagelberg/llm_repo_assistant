# Test cases for file-related endpoints
import os
import shutil
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.utils import get_full_path
from src.core.config import settings
import tempfile

client = TestClient(app)

# Define a fixture for creating and cleaning up temporary files
@pytest.fixture
def temp_file():
    # Create a temporary file in target repo top-level directory
    with tempfile.NamedTemporaryFile(mode='w', dir=settings.REPO_ROOT, delete=False) as temp_file:
        temp_file.write('Temporary file content')
        temp_file_path = temp_file.name
    yield os.path.basename(temp_file.name)  # Provide the name of the test file which is same as path to the file since it's at the top-level
    # Teardown logic: remove the temporary file 
    os.unlink(temp_file_path)

# Define a fixture for handling .llmignore file
@pytest.fixture
def llmignore_handler():
    # Check if .llmignore already exists and back it up if it does
    llmignore_exists = os.path.exists('.llmignore')
    if llmignore_exists:
        shutil.copyfile('.llmignore', '.llmignore.bak')
    yield
    # Teardown logic: remove the temporary .llmignore file created by the test
    if os.path.exists('.llmignore'):
        os.remove('.llmignore')
    # Restore the original .llmignore file if it existed
    if llmignore_exists:
        shutil.move('.llmignore.bak', '.llmignore')

# Test cases for the endpoint: GET /{file_path:path} (Read a file)

def test_read_file_success(temp_file):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    # Use the correct URL path to access the endpoint
    response = client.get(f'/api/v1/files/{test_file_path}')
    assert response.status_code == 200
    assert response.json() == {'content': 'Temporary file content'}

# Remaining test functions...

def test_read_file_ignored_in_llmignore(temp_file, llmignore_handler):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    # Get filename of temp_file
    filename = os.path.basename(test_file_path)

    # Create a .llmignore file that ignores the temporary file
    with open('.llmignore', 'w') as llmignore_file:
        llmignore_file.write(filename)

    # Use the correct URL path to access the endpoint
    response = client.get(f'/api/v1/files/{test_file_path}')

    # Assert that the response status code is 404 (Not Found)
    # because the file is ignored in .llmignore
    assert response.status_code == 404
    assert response.json() == {'detail': 'File is ignored in `.llmignore`'}

def test_read_directory_instead_of_file(temp_file):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file

    # Get the parent directory of the temporary file
    test_dir_path = os.path.dirname(test_file_path)

    # Use the correct URL path to access the endpoint
    response = client.get(f'/api/v1/files/{test_dir_path}')

    # Assert that the response status code is 400 (Bad Request)
    # because the path is not a file
    assert response.status_code == 400
    assert response.json() == {'detail': 'Path is not a file'}

def test_create_file_success(temp_file):
    # Define the content to be written to the new file
    file_content = 'New file content'

    # Use the correct URL path to access the endpoint
    response = client.post('/api/v1/files/', json={'file_name': 'new_file.txt', 'path': '', 'content': file_content})

    # Assert that the response status code is 201 (file created)
    assert response.status_code == 201
    assert response.json() == {'message': 'File created successfully'}

    # Assert that the new file exists and contains the expected content
    with open('new_file.txt', 'r') as new_file:
        assert new_file.read() == file_content

    # Teardown logic: remove the new file
    os.unlink('new_file.txt')

def test_create_file_already_exists(temp_file):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file

    # Define the content to be written to the new file
    file_content = 'New file content'

    # Use the correct URL path to access the endpoint
    response = client.post('/api/v1/files/', json={'file_name': test_file_path, 'path': '', 'content': file_content})

    # Assert that the response status code is 409 (Conflict)
    # because the file already exists
    assert response.status_code == 409
    assert response.json() == {'detail': 'File already exists'}
