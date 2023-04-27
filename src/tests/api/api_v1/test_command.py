from fastapi.testclient import TestClient
from src.main import app
import pytest
import os
from src.core.config import settings
import tempfile
from src.utils import get_filesystem_path, get_endpoint_path

client = TestClient(app)

@pytest.fixture(scope='function')
def temp_test_file():
    test_emoji_content = '''
import emoji

def test_emoji():
    result = emoji.emojize('Python is :thumbs_up:')
    assert 'Python is 👍' in result
'''
    with tempfile.NamedTemporaryFile(mode='w', dir=settings.REPO_ROOT, delete=False, prefix='test_', suffix='.py') as temp_file:
        temp_file.write(test_emoji_content)
        temp_file_path = temp_file.name

    yield temp_file_path

    # Teardown logic: remove the temporary file
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)

def test_can_run_tests():
    # Test case for the get_file_structure endpoint
    # Use the root directory of the repository as the test directory
    response = client.post("/api/v1/command/run_tests/pytest", json={})
    assert response.status_code == 200

def test_tests_use_separate_testing_virtualenv(temp_test_file):
    # Test case for the get_file_structure endpoint
    # Use the root directory of the repository as the test directory

    # temp_file contains emoji package that is not in the requirements.txt for the app but is in 
    # the requirements.txt for the target repo. If the tests are run in the same virtualenv as the app,
    # the tests will fail because the emoji package is not installed. This test ensures that the tests
    # are run in a separate virtualenv that has the target repo's requirements.txt installed.
    response = client.post("/api/v1/command/run_tests/pytest", json={'test_file_path': get_endpoint_path(temp_test_file)})
    assert response.status_code == 200
    assert 'collected 1 item' in response.text
    assert '1 passed' in response.text

