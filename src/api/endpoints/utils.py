from fastapi import HTTPException, APIRouter
from pathlib import Path as FilePath
import shutil

from src.schemas import MoveRequest
from src.utils import is_llmignored

router = APIRouter()


@router.post("/move")
async def move_file_or_directory(move_request: MoveRequest):
    src_path = FilePath(move_request.src_path)
    dest_path = FilePath(move_request.dest_path)
    if is_llmignored(str(src_path)):
        raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
    if src_path.exists():
        shutil.move(src_path, dest_path)
        return {"message": "Moved successfully"}
    else:
        raise HTTPException(status_code=404, detail="Source not found")

