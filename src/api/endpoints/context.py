from fastapi import HTTPException, Query, APIRouter
from pathlib import Path as FilePath
import fnmatch
import os
import shutil
from typing import Any, Dict

from src.utils import get_full_path
from src.core.config import settings
from src.utils import is_llmignored, get_git_diff

router = APIRouter()

def search_files(query: str, root_dir: FilePath):
    matches = []
    for root, dirnames, filenames in os.walk(root_dir):
        for filename in fnmatch.filter(filenames, f"*{query}*"):
            if not is_llmignored(os.path.join(root, filename)):
                matches.append(os.path.join(root, filename))
        for dirname in fnmatch.filter(dirnames, f"*{query}*"):
            if not is_llmignored(os.path.join(root, dirname)):
                matches.append(os.path.join(root, dirname))
    return matches


@router.get("/search")
async def search_files_and_directories(q: str = Query(..., min_length=1)):
    root_dir = FilePath(settings.REPO_ROOT)  # Set your root directory here
    search_results = search_files(q, root_dir)
    return {"matches": search_results}


def get_directory_structure(path: str) -> Dict[str, Any]:
    item = {
        "name": os.path.basename(path),
        "path": path[len(str(settings.REPO_ROOT)):], # Remove the repo root from the path
        "type": "file" if os.path.isfile(path) else "directory"
    }

    # Ignore any path / files that are in .llmignore or are part of a .git directory
    if is_llmignored(item["path"]) or item["path"][-4:] == '.git':
            return None

    if os.path.isfile(path):

        item["metadata"] = {
            "num_tokens": 0,  # Replace with actual token count calculation
            "file_size_bytes": os.path.getsize(path)
        }
    else:
        children = [
            get_directory_structure(os.path.join(path, child))
            for child in os.listdir(path)
        ]
        item["children"] = [child for child in children if child is not None]

    return item


@router.post("/file_structure/{dir_path:path}")
async def get_file_structure(dir_path: str):
    """
    Get file structure of given directory and subdirectories. Ignores `.git` directory
    and any file matching `.llmignore` patterns. `.llmignore` must be in the 
    root directory of repo and follow same structure as `.gitignore`.
    """
    dir_path = get_full_path(dir_path)
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


