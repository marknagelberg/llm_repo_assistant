import os
import stat
from enum import Enum
import subprocess
from typing import Optional, List
from fastapi import HTTPException, APIRouter

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

    test_output = run_tests(test_command, test_file_path, test_run_request.test_function_name)
    return {"status": "success", "test_output": test_output}



