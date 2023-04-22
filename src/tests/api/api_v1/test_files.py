# Test cases for file-related endpoints
import os
import shutil
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.utils import get_full_path

client = TestClient(app)

# Define a fixture for creating and cleaning up temporary files
@pytest.fixture
def temp_file(tmpdir):
    # Create a temporary file in the pytest-managed temporary directory
    temp_file = tmpdir.join('temp_file.txt')
    temp_file.write('Temporary file content')
    yield temp_file.strpath  # Provide the path to the test function
    # Teardown logic: remove the temporary file (if needed)
    # Note: pytest's tmpdir automatically handles cleanup, so this is optional

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
