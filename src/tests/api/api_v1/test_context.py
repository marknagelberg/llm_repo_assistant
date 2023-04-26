from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_get_file_structure():
    # Test case for the get_file_structure endpoint
    # Use the root directory of the repository as the test directory
    response = client.post("/api/v1/context/file_structure/")
    assert response.status_code == 200
    # Add more assertions based on expected response


def test_git_diff():
    # Test case for the git_diff endpoint
    response = client.get("/api/v1/context/git_diff")
    assert response.status_code == 200
    # Add more assertions based on expected response

# Add more test cases if needed
