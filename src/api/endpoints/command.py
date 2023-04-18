import os
from enum import Enum
import subprocess
from typing import Optional, List
from fastapi import HTTPException, APIRouter

from src.schemas import TestRunRequest
from src.core.config import settings
from src.utils import get_git_diff



router = APIRouter()


class TestFramework(str, Enum):
    pytest = "pytest"

def run_tests(test_command: List[str], test_name: Optional[str] = None) -> str:
    if test_name:
        test_command.extend(["-k", test_name])

    test_script = os.path.join(settings.REPO_ROOT, "run_tests.sh")
    test_command.insert(0, test_script)

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
    Runs tests for repo. Endpoint executes file named `run_tests.sh` 
    in root of repo which activates programming environment and runs tests.
    `run_tests.sh` should be executable and contain
    `exec python -m pytest "$@"` after activating the environment.
    """

    if test_framework.lower() == "pytest":
        test_command = ["pytest"]
    else:
        raise HTTPException(status_code=400, detail="Unsupported test framework")

    test_output = run_tests(test_command, test_run_request.test_name)
    return {"status": "success", "test_output": test_output}



@router.get("/git_diff")
async def git_diff():
    """
    Returns `git diff` for the repo (changes since last commit).
    """
    try:
        diff = get_git_diff(settings.REPO_ROOT)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"diff": diff}

