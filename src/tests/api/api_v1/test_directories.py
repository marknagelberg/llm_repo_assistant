import pytest
from fastapi.testclient import TestClient
from src.main import app
import os
import shutil

client = TestClient(app)

# Test setup and teardown
@pytest.fixture(scope='module')
def test_directory():
    # Create a temporary test directory
    test_dir = 'test_directory'
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    # Teardown: Remove the test directory
    shutil.rmtree(test_dir)

# Test cases for create_directory endpoint
def test_create_directory_success(test_directory):
    response = client.post('/api/v1/directories', json={'dir_name': 'test_dir', 'path': test_directory})
    assert response.status_code == 200

def test_create_directory_invalid_path():
    response = client.post('/api/v1/directories', json={'dir_name': 'test_dir', 'path': '/invalid_path/'})
    assert response.status_code == 409

# Test cases for list_directory_contents endpoint
def test_list_directory_contents_success(test_directory):
    response = client.get(f'/api/v1/directories/{test_directory}')
    assert response.status_code == 200
    assert 'contents' in response.json()

def test_list_directory_contents_non_existent():
    response = client.get('/api/v1/directories/non_existent')
    assert response.status_code == 404
    assert response.json() == {'detail': 'Directory not found'}

# Test cases for delete_directory endpoint
def test_delete_directory_success(test_directory):
    response = client.delete(f'/api/v1/directories/{test_directory}/test_dir')
    assert response.status_code == 200
    assert response.json() == {'message': 'Directory deleted successfully'}

def test_delete_directory_non_existent():
    response = client.delete('/api/v1/directories/non_existent')
    assert response.status_code == 404
    assert response.json() == {'detail': 'Directory not found'}