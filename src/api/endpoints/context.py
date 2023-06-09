from fastapi import HTTPException, Query, APIRouter
from pathlib import Path as FilePath
import fnmatch
import os
import shutil
from typing import Any, Dict

from src.utils import get_filesystem_path
from src.core.config import settings
from src.utils import is_llmignored, get_git_diff

router = APIRouter()


def get_directory_structure(path: str) -> Dict[str, Any]:
    item = {
        "name": os.path.basename(path),
        "path": path[len(str(settings.REPO_ROOT)):], # Remove the repo root from the path
        "type": "file" if os.path.isfile(path) else "directory"
    }

    try:
        # Ignore any path / files that are in .llmignore or are part of a .git directory
        if is_llmignored(item["path"]) or item["path"][-4:] == '.git':
                return None

        if os.path.isfile(path):

            item["metadata"] = {
                "file_size_bytes": os.path.getsize(path)
            }
        else:
            children = [
                get_directory_structure(os.path.join(path, child))
                for child in os.listdir(path)
            ]
            item["children"] = [child for child in children if child is not None]

        return item
    except FileNotFoundError:
        # TODO - there are some situations, particularly in python environment, where
        # the file does seem to exist but we get a FileNotFoundError. This is a hacky
        # workaround for now. Example of error that has happened:
        # E.g FileNotFoundError: [Errno 2] No such file or directory: '/repo/venv/bin/python'
        return None


@router.post("/file_structure/{dir_path:path}")
async def get_file_structure(dir_path: str):
    """
    Get file structure of given directory and subdirectories. Ignores `.git` directory
    and any file matching `.llmignore` patterns. `.llmignore` must be in the 
    root directory of repo and follow same structure as `.gitignore`.
    """
    dir_path = get_filesystem_path(dir_path)
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="Directory not found")
    structure = get_directory_structure(dir_path)
    return structure


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


