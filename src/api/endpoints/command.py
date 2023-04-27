import os
import sys
from enum import Enum
import subprocess
from typing import Optional, List
from fastapi import HTTPException, APIRouter
from contextlib import contextmanager

from src.schemas import TestRunRequest
from src.core.config import settings
from src.utils import get_filesystem_path


router = APIRouter()


class TestFramework(str, Enum):
    pytest = "pytest"

def run_tests(test_command: List[str], 
              test_file_path: Optional[str] = None,
              test_function_name: Optional[str] = None) -> str:
    if test_file_path and not test_function_name:
        test_command.extend([test_file_path])
    if test_function_name and not test_file_path:
        test_command.extend([test_function_name])
    if test_function_name and test_file_path:
        test_command.extend([test_file_path + "::" + test_function_name])

    original_cwd = os.getcwd()
    os.chdir(settings.REPO_ROOT)

    try:
        result = subprocess.run(test_command, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stdout + e.stderr
    finally:
        os.chdir(original_cwd)

@contextmanager
def activate_virtualenv(venv_path):
    """Temporarily add the virtual environment to sys.path."""
    original_sys_path = sys.path.copy()
    sys.path.insert(0, venv_path + "/lib/python3.9/site-packages")
    try:
        yield
    finally:
        sys.path = original_sys_path

@router.post("/run_tests/{test_framework}")
async def run_tests_endpoint(test_framework: TestFramework, test_run_request: TestRunRequest):
    """
    Runs tests for repo. Endpoint executes tests with optional specification of test file and test function.
    If no test file or function is specified, all available tests are run. Currently only `pytest` is supported.
    """

    test_file_path = ""
    if test_run_request.test_file_path:
        test_file_path = get_filesystem_path(test_run_request.test_file_path)

    if test_framework.lower() == "pytest":
        test_command = ["pytest"]
    else:
        raise HTTPException(status_code=400, detail="Unsupported test framework")

    venv_path = "/venv"

    if not os.path.exists(venv_path + "/lib/python3.9/site-packages"):
        error_message = """
        Virtual environment for target repo not found. Provide a 'llm_target_repo_requirements.txt' file in your
        target repo to use the run_tests endpoint and re-build the docker container. 
        """
        raise HTTPException(status_code=400, detail=error_message)

    with activate_virtualenv("/venv"):
        test_output = run_tests(test_command, test_file_path, test_run_request.test_function_name)
    return {"status": "success", "test_output": test_output}

