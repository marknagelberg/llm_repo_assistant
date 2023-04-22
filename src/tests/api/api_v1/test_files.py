# Test cases for file-related endpoints
import os
import shutil
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.utils import get_filesystem_path, get_endpoint_path
from src.core.config import settings
import tempfile

client = TestClient(app)

# Define a fixture for creating and cleaning up temporary files
@pytest.fixture(scope='function')
def temp_file():
    # Create a temporary file in target repo top-level directory
    with tempfile.NamedTemporaryFile(mode='w', dir=settings.REPO_ROOT, delete=False) as temp_file:
        temp_file.write('Temporary file content')
        temp_file_path = temp_file.name
    yield temp_file_path
    # Teardown logic: remove the temporary file 
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)

# Define a fixture for handling .llmignore file
@pytest.fixture(scope='function')
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
    test_endpoint_path = get_endpoint_path(test_file_path)
    # Use the correct URL path to access the endpoint
    response = client.get(f'/api/v1/files/{test_endpoint_path}')
    assert response.status_code == 200
    assert response.json() == {'content': 'Temporary file content'}

# Remaining test functions...

def test_read_file_ignored_in_llmignore(temp_file, llmignore_handler):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    # Get filename of temp_file
    filename = os.path.basename(test_file_path)
    test_endpoint_path = get_endpoint_path(test_file_path)

    # Create a .llmignore file that ignores the temporary file
    with open('.llmignore', 'w') as llmignore_file:
        llmignore_file.write(filename)

    # Use the correct URL path to access the endpoint
    response = client.get(f'/api/v1/files/{test_endpoint_path}')

    # Assert that the response status code is 404 (Not Found)
    # because the file is ignored in .llmignore
    assert response.status_code == 403
    assert response.json() == {'detail': 'File is ignored in `.llmignore`'}

def test_read_directory_instead_of_file(temp_file):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    test_endpoint_path = get_endpoint_path(test_file_path)

    # Get the parent directory of the temporary file
    test_dir_path = os.path.dirname(test_endpoint_path)

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
    with open(get_filesystem_path('new_file.txt'), 'r') as new_file:
        assert new_file.read() == file_content

    # Teardown logic: remove the new file
    os.unlink(get_filesystem_path('new_file.txt'))

def test_create_file_already_exists(temp_file):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    test_endpoint_file_path = get_endpoint_path(test_file_path)

    # Define the content to be written to the new file
    file_content = 'New file content'

    # Use the correct URL path to access the endpoint
    response = client.post('/api/v1/files/', json={'file_name': test_endpoint_file_path, 'path': '', 'content': file_content})

    # Assert that the response status code is 409 (Conflict)
    # because the file already exists
    assert response.status_code == 409
    assert response.json() == {'detail': 'File already exists'}

def test_create_file_ignored_in_llmignore(temp_file, llmignore_handler):
    new_file_name = 'test_create_file.txt'

    # Create a .llmignore file that ignores the temporary file
    with open(get_filesystem_path('.llmignore'), 'w') as llmignore_file:
        llmignore_file.write(new_file_name)

    # Define the content to be written to the new file
    file_content = 'Create new file content'

    # Use the correct URL path to access the endpoint
    response = client.post('/api/v1/files/', json={'file_name': new_file_name, 'path': '', 'content': file_content})

    # Assert that the response status code is 403 (Forbidden)
    # because the file is ignored in .llmignore
    assert response.status_code == 403
    assert response.json() == {'detail': 'Cannot create file that is ignored in `.llmignore`'}
    if os.path.exists(get_filesystem_path(new_file_name)):
        os.unlink(get_filesystem_path(new_file_name))

def test_create_file_with_directories():
    # Define the content to be written to the new file
    file_content = 'New file content'

    # Define the file name and path with non-existent directories
    new_file_dir = 'new_dir/sub_dir/'
    new_file_name = 'new_file.txt'

    # Use the correct URL path to access the endpoint
    response = client.post('/api/v1/files/', json={'file_name': new_file_name, 
                                                   'path': new_file_dir, 
                                                   'content': file_content, 
                                                   'create_directories': True})

    # Assert that the response status code is 201 (Created)
    assert response.status_code == 201
    assert response.json() == {'message': 'File created successfully'}

    # Assert that the new file exists and contains the expected content
    with open(get_filesystem_path(os.path.join(new_file_dir, new_file_name)), 'r') as new_file:
        assert new_file.read() == file_content

    # Teardown logic: remove the new file and directories
    os.unlink(get_filesystem_path(os.path.join(new_file_dir, new_file_name)))
    os.rmdir(get_filesystem_path('new_dir/sub_dir'))
    os.rmdir(get_filesystem_path('new_dir'))

def test_update_entire_file_success(temp_file):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    test_endpoint_path = get_endpoint_path(test_file_path)

    # Define the new content to be written to the file
    new_content = 'Updated file content'

    # Use the correct URL path to access the endpoint
    response = client.put(f'/api/v1/files/edit_entire_file/{test_endpoint_path}', json={'content': new_content})

    # Assert that the response status code is 200 (Success)
    assert response.status_code == 200
    assert response.json() == {'message': 'File updated successfully'}

    # Assert that the file content is updated as expected
    with open(test_file_path, 'r') as updated_file:
        assert updated_file.read() == new_content

def test_update_entire_file_not_found():
    # Define a non-existent file path
    non_existent_file_path = 'non_existent_file.txt'

    # Define the new content to be written to the file
    new_content = 'Updated file content'

    # Use the correct URL path to access the endpoint
    response = client.put(f'/api/v1/files/edit_entire_file/{non_existent_file_path}', json={'content': new_content})

    # Assert that the response status code is 404 (Not Found)
    assert response.status_code == 404
    assert response.json() == {'detail': 'File not found'}

def test_update_entire_file_ignored_in_llmignore(temp_file, llmignore_handler):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    test_endpoint_path = get_endpoint_path(test_file_path)

    # Get filename of temp_file
    filename = os.path.basename(test_file_path)

    # Create a .llmignore file that ignores the temporary file
    with open('.llmignore', 'w') as llmignore_file:
        llmignore_file.write(filename)

    # Define the new content to be written to the file
    new_content = 'Updated file content'

    # Use the correct URL path to access the endpoint
    response = client.put(f'/api/v1/files/edit_entire_file/{test_endpoint_path}', json={'content': new_content})

    # Assert that the response status code is 403 (Forbidden)
    # because the file is ignored in .llmignore
    assert response.status_code == 403
    assert response.json() == {'detail': 'File is ignored in `.llmignore`'}


def test_edit_file_by_line_number_success(temp_file):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    test_endpoint_path = get_endpoint_path(test_file_path)

    # Define the new content to be written to the file
    new_content = 'Updated line content'

    # Use the correct URL path to access the endpoint
    response = client.post(f'/api/v1/files/edit_by_line_number/{test_endpoint_path}', json={'start_line': 0, 'content': new_content})

    # Assert that the response status code is 200 (Success)
    assert response.status_code == 200
    assert response.json() == {'message': 'File updated successfully'}

    # Assert that the file content is updated as expected
    with open(test_file_path, 'r') as updated_file:
        assert updated_file.read() == new_content

def test_edit_file_by_line_number_not_found():
    # Define a non-existent file path
    non_existent_file_path = 'non_existent_file.txt'

    # Define the new content to be written to the file
    new_content = 'Updated line content'

    # Use the correct URL path to access the endpoint
    response = client.post(f'/api/v1/files/edit_by_line_number/{non_existent_file_path}', json={'start_line': 0, 'content': new_content})

    # Assert that the response status code is 404 (Not Found)
    assert response.status_code == 404
    assert response.json() == {'detail': 'File not found'}

def test_edit_file_by_line_number_ignored_in_llmignore(temp_file, llmignore_handler):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    test_endpoint_path = get_endpoint_path(test_file_path)

    # Get filename of temp_file
    filename = os.path.basename(test_file_path)

    # Create a .llmignore file that ignores the temporary file
    with open('.llmignore', 'w') as llmignore_file:
        llmignore_file.write(filename)

    # Define the new content to be written to the file
    new_content = 'Updated line content'

    # Use the correct URL path to access the endpoint
    response = client.post(f'/api/v1/files/edit_by_line_number/{test_endpoint_path}', json={'start_line': 0, 'content': new_content})

    # Assert that the response status code is 403 (Forbidden)
    # because the file is ignored in .llmignore
    assert response.status_code == 403
    assert response.json() == {'detail': 'File is ignored in `.llmignore`'}

def test_delete_file_success(temp_file):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    test_endpoint_path = get_endpoint_path(test_file_path)

    # Use the correct URL path to access the endpoint
    response = client.delete(f'/api/v1/files/{test_endpoint_path}')

    # Assert that the response status code is 200 (Success)
    assert response.status_code == 200
    assert response.json() == {'message': 'File deleted successfully'}

    # Assert that the file no longer exists
    assert not os.path.exists(test_file_path)


def test_delete_file_not_found():
    # Define a non-existent file path
    non_existent_file_path = 'non_existent_file.txt'

    # Use the correct URL path to access the endpoint
    response = client.delete(f'/api/v1/files/{non_existent_file_path}')

    # Assert that the response status code is 404 (Not Found)
    assert response.status_code == 404
    assert response.json() == {'detail': 'File not found'}


def test_delete_file_ignored_in_llmignore(temp_file, llmignore_handler):
    # Use the fixture to get the path to the temporary file
    test_file_path = temp_file
    test_endpoint_path = get_endpoint_path(test_file_path)

    # Get filename of temp_file
    filename = os.path.basename(test_file_path)

    # Create a .llmignore file that ignores the temporary file
    with open('.llmignore', 'w') as llmignore_file:
        llmignore_file.write(filename)

    # Use the correct URL path to access the endpoint
    response = client.delete(f'/api/v1/files/{test_endpoint_path}')

    # Assert that the response status code is 403 (Forbidden)
    # because the file is ignored in .llmignore
    assert response.status_code == 403
    assert response.json() == {'detail': 'File is ignored in `.llmignore`'}
