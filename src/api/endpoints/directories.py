from fastapi import APIRouter, HTTPException, Path
from pathlib import Path as FilePath
import shutil

from src.schemas import DirectoryRequest
from src.utils import is_llmignored

router = APIRouter()


@router.get("/{dir_path:path}")
async def list_directory_contents(dir_path: str):
    target_path = FilePath(dir_path)
    if is_llmignored(str(target_path)):
        raise HTTPException(status_code=404, detail="Directory is ignored in `.llmignore`")
    if target_path.is_dir():
        contents = [str(item) for item in target_path.iterdir()]
        return {"contents": contents}
    else:
        raise HTTPException(status_code=404, detail="Directory not found")


@router.post("/")
async def create_directory(directory_request: DirectoryRequest):
    target_path = FilePath(directory_request.path) / directory_request.dir_name
    if is_llmignored(str(target_path)):
        raise HTTPException(status_code=404, detail="Directory is ignored in `.llmignore`")
    if not target_path.exists():
        target_path.mkdir(parents=True, exist_ok=True)
        return {"message": "Directory created successfully"}
    else:
        raise HTTPException(status_code=409, detail="Directory already exists")


@router.delete("/{dir_path:path}")
async def delete_directory(dir_path: str):
    target_path = FilePath(dir_path)
    if is_llmignored(str(target_path)):
        raise HTTPException(status_code=404, detail="Directory is ignored in `.llmignore`")
    if target_path.is_dir():
        shutil.rmtree(target_path)
        return {"message": "Directory deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Directory not found")


