import os
from fastapi.testclient import TestClient
from src.main import app
import pytest
from src.utils import get_endpoint_path

client = TestClient(app)


@pytest.fixture
def temp_python_file_with_function(custom_tmpdir):
    # Create a temporary Python file with a known function and docstring
    file_content = (
        "def sample_function():\n"
        "    \"\"\"This is a sample function.\"\"\"\n"
        "    pass\n"
    )
    file_path = os.path.join(custom_tmpdir, 'sample.py')
    with open(file_path, 'w') as file:
        file.write(file_content)
    function_name = 'sample_function'
    expected_docstring = 'This is a sample function.'
    yield str(file_path), function_name, expected_docstring
    # Clean up by deleting the temporary file
    os.remove(file_path)


@pytest.fixture
def temp_python_file_without_docstring(custom_tmpdir):
    # Create a temporary Python file without a module-level docstring
    file_content = "class SampleClass:\n    pass\n"
    file_path = os.path.join(custom_tmpdir, "temp_file_without_docstring.py")
    with open(file_path, "w") as file:
        file.write(file_content)
    return str(file_path), file_content


@pytest.fixture
def temp_python_file_with_class(custom_tmpdir):
    # Create a temporary Python file with a known class and docstring
    file_content = (
        "class SampleClass:\n"
        "    \"\"\"This is a sample class.\"\"\"\n"
        "    pass\n"
    )
    file_path = os.path.join(custom_tmpdir, 'sample.py')
    with open(file_path, 'w') as file:
        file.write(file_content)
    class_name = 'SampleClass'
    expected_docstring = 'This is a sample class.'
    yield str(file_path), class_name, expected_docstring
    # Clean up by deleting the temporary file
    os.remove(file_path)


def test_get_function_docstring_success(temp_python_file_with_function):
    # Use the temporary Python file created by the fixture `temp_python_file_with_function`
    file_path, function_name, expected_docstring = temp_python_file_with_function
    endpoint_path = get_endpoint_path(file_path)
    print(file_path)
    print(endpoint_path)

    # Call the get_function_docstring endpoint
    response = client.get(f"/api/v1/programming/get_function_docstring/python/{endpoint_path}/{function_name}")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected docstring
    assert response.json() == {'docstring': expected_docstring}


def test_get_function_docstring_nonexistent_function(temp_python_file_with_function):
    # Use the temporary Python file created by the fixture `temp_python_file_with_function`
    file_path, _, _ = temp_python_file_with_function
    endpoint_path = get_endpoint_path(file_path)
    nonexistent_function_name = 'nonexistent_function'

    # Call the get_function_docstring endpoint with a nonexistent function name
    response = client.get(f"/api/v1/programming/get_function_docstring/python/{endpoint_path}/{nonexistent_function_name}")

def test_update_function_docstring_success(temp_python_file_with_function):
    # Use the temporary Python file created by the fixture `temp_python_file_with_function`
    file_path, function_name, _ = temp_python_file_with_function
    endpoint_path = get_endpoint_path(file_path)
    new_docstring = 'This is the updated docstring.'

    # Call the update_function_docstring endpoint
    response = client.put(
        f"/api/v1/programming/update_function_docstring/python/{endpoint_path}/{function_name}",
        json={"new_docstring": new_docstring}
    )

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected message
    assert response.json() == {"status": "success", "message": "Function docstring updated"}

    # Verify that the docstring was actually updated in the file
    with open(file_path, 'r') as file:
        content = file.read()
    assert new_docstring in content


def test_get_function_docstring_nonexistent_file():
    # Define a nonexistent file path and a sample function name
    nonexistent_file_path = 'nonexistent_file.py'
    function_name = 'sample_function'

    # Call the get_function_docstring endpoint with a nonexistent file path
    response = client.get(f"/api/v1/programming/get_function_docstring/python/{nonexistent_file_path}/{function_name}")

    # Assert that the response status code is 404 (Not Found)
    assert response.status_code == 404

    # Assert that the response contains the expected error message
    assert response.json() == {'detail': 'File not found'}

def test_get_class_docstring_no_docstring(temp_python_file_with_class):
    # Modify the temporary Python file created by the fixture `temp_python_file_with_class`
    # to remove the docstring from the class
    file_path, class_name, _ = temp_python_file_with_class
    with open(file_path, 'w') as file:
        file.write("class SampleClass:\n    pass\n")

    endpoint_path = get_endpoint_path(file_path)
    # Call the get_class_docstring endpoint
    response = client.get(f"/api/v1/programming/get_class_docstring/python/{endpoint_path}/{class_name}")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response indicates that no docstring was found
    assert response.json() == {'docstring': None}


def test_update_class_docstring_no_docstring(temp_python_file_with_class):
    # Modify the temporary Python file created by the fixture `temp_python_file_with_class`
    # to remove the docstring from the class
    file_path, class_name, _ = temp_python_file_with_class
    with open(file_path, 'w') as file:
        file.write("class SampleClass:\n    pass\n")
    new_docstring = 'This is the new docstring.'

    endpoint_path = get_endpoint_path(file_path)
    # Call the update_class_docstring endpoint
    response = client.put(
        f"/api/v1/programming/update_class_docstring/python/{endpoint_path}/{class_name}",
        json={"new_docstring": new_docstring}
    )

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected message
    assert response.json() == {"status": "success", "message": "Class docstring updated"}

    # Verify that the docstring was actually added to the class in the file
    with open(file_path, 'r') as file:
        content = file.read()
    assert new_docstring in content

def test_get_module_docstring_success(temp_python_file_with_class):
    # Use the temporary Python file created by the fixture `temp_python_file_with_class`
    file_path, _, _ = temp_python_file_with_class
    # Add a module-level docstring to the file
    with open(file_path, 'r+') as file:
        content = file.read()
        file.seek(0, 0)
        file.write('''\"\"\"This is a module-level docstring.\"\"\"\n''' + content)
    expected_docstring = 'This is a module-level docstring.'

    endpoint_path = get_endpoint_path(file_path)
    # Call the get_module_docstring endpoint
    response = client.get("/api/v1/programming/get_module_docstring/python/" + endpoint_path)

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected docstring
    assert response.json() == {"docstring": expected_docstring}

def test_get_module_docstring_no_docstring(temp_python_file_without_docstring):
    # Use the temporary Python file created by the fixture `temp_python_file_without_docstring`
    file_path, _ = temp_python_file_without_docstring
    expected_docstring = None
    endpoint_path = get_endpoint_path(file_path)

    # Call the get_module_docstring endpoint
    response = client.get(f"/api/v1/programming/get_module_docstring/python/{endpoint_path}")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected docstring
    assert response.json() == {'docstring': expected_docstring}

def test_update_module_docstring_success(temp_python_file_with_class):
    # Use the temporary Python file created by the fixture `temp_python_file_with_class`
    file_path, _, _ = temp_python_file_with_class
    # Add a module-level docstring to the file
    with open(file_path, 'r+') as file:
        content = file.read()
        file.seek(0, 0)
        file.write('''\"\"\"This is the original module-level docstring.\"\"\"\n''' + content)
    new_docstring = 'This is the new module-level docstring.'
    endpoint_path = get_endpoint_path(file_path)

    # Call the update_module_docstring endpoint
    response = client.put(
        f"/api/v1/programming/update_module_docstring/python/{endpoint_path}",
        json={"new_docstring": new_docstring}
    )

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected message
    assert response.json() == {"status": "success", "message": "Module docstring updated"}

    # Verify that the docstring was actually updated in the file
    with open(file_path, 'r') as file:
        content = file.read()
    assert new_docstring in content

def test_update_module_docstring_no_docstring(temp_python_file_with_class):
    # Use the temporary Python file created by the fixture `temp_python_file_with_class`
    file_path, _, _ = temp_python_file_with_class
    new_docstring = 'This is the new module-level docstring.'

    endpoint_path = get_endpoint_path(file_path)
    # Call the update_module_docstring endpoint
    response = client.put(
        f"/api/v1/programming/update_module_docstring/python/{endpoint_path}",
        json={"new_docstring": new_docstring}
    )

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected message
    assert response.json() == {"status": "success", "message": "Module docstring updated"}

    # Verify that the docstring was actually added to the file
    with open(file_path, 'r') as file:
        content = file.read()
    assert new_docstring in content

def test_get_class_docstring_success(temp_python_file_with_class):
    # Use the temporary Python file created by the fixture `temp_python_file_with_class`
    file_path, class_name, _ = temp_python_file_with_class
    expected_docstring = 'This is a sample class.'
    endpoint_path = get_endpoint_path(file_path)

    # Call the get_class_docstring endpoint
    response = client.get(f"/api/v1/programming/get_class_docstring/python/{endpoint_path}/{class_name}")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected docstring
    assert response.json() == {'docstring': expected_docstring}

def test_update_class_docstring_success(temp_python_file_with_class):
    # Use the temporary Python file created by the fixture `temp_python_file_with_class`
    file_path, class_name, _ = temp_python_file_with_class
    new_docstring = 'This is the updated class docstring.'
    endpoint_path = get_endpoint_path(file_path)

    # Call the update_class_docstring endpoint
    response = client.put(
        f"/api/v1/programming/update_class_docstring/python/{endpoint_path}/{class_name}",
        json={"new_docstring": new_docstring}
    )

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected message
    assert response.json() == {"status": "success", "message": "Class docstring updated"}

