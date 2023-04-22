from fastapi import FastAPI, APIRouter, HTTPException, Path, status
from fastapi.responses import JSONResponse
from pathlib import Path as FilePath
import os
from typing import Optional
from src.schemas import CreateFileRequest, UpdateEntireFileRequest, UpdateFileLineNumberRequest
from src.core.config import settings
from src.utils import get_filesystem_path, is_llmignored

router = APIRouter()


@router.get("/{file_path:path}")
async def read_file(file_path: str):
    path = get_filesystem_path(file_path)

    if is_llmignored(path):
        raise HTTPException(status_code=403, detail="File is ignored in `.llmignore`")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    if os.path.isfile(path):
        try:
            with open(path, "r") as file:
                content = file.read()
            return {"content": content}
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    else:
        raise HTTPException(status_code=400, detail="Path is not a file")


@router.post("/")
async def create_file(file_request: CreateFileRequest):
    target_path = file_request.path + '/' + file_request.file_name
    if is_llmignored(file_request.file_name):
        raise HTTPException(status_code=403, detail="Cannot create file that is ignored in `.llmignore`")
    if file_request.create_directories and not os.path.exists(file_request.path):
        path = FilePath(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)
    if not file_request.create_directories and not os.path.exists(file_request.path):
        raise HTTPException(status_code=404, detail="Directory not found")
    if not os.path.exists(target_path):
        with open(target_path, "w") as file:
            file.write(file_request.content)
        return JSONResponse(content={"message": "File created successfully"}, status_code=status.HTTP_201_CREATED)
    else:
        raise HTTPException(status_code=409, detail="File already exists")


@router.put("/edit_entire_file/{file_path:path}")
async def update_entire_file(file_path: str, update_request: UpdateEntireFileRequest):
    path = get_filesystem_path(file_path)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    if is_llmignored(path):
        raise HTTPException(status_code=403, detail="File is ignored in `.llmignore`")

    if os.path.isfile(path):
        try:
            with open(path, "w") as file:
                file.write(update_request.content)
            return {"message": "File updated successfully"}
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    else:
        raise HTTPException(status_code=400, detail="Path is not a file")


@router.post("/edit_by_line_number/{file_path:path}")
async def edit_file_by_line_number(file_path: str, edit_request: UpdateFileLineNumberRequest):
    '''
    This function edits a file by line number, where the first line in the file is 0.
    If no end_line is specified, it will only edit the start_line.
    '''

    path = get_filesystem_path(file_path)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    if is_llmignored(path):
        raise HTTPException(status_code=403, detail="File is ignored in `.llmignore`")

    if os.path.isfile(path):
        try:
            start_line = edit_request.start_line
            end_line = edit_request.end_line or start_line
            content = edit_request.content

            with open(path, "r") as file:
                lines = file.readlines()

            if start_line < 0 or start_line > len(lines) - 1 or end_line < start_line or end_line > len(lines) - 1:
                raise HTTPException(status_code=400, detail="Invalid line numbers")

            # Replace the specified lines with the new content
            lines[start_line:end_line + 1] = content.splitlines(keepends=True)

            with open(path, "w") as file:
                file.writelines(lines)

            return {"message": "File updated successfully"}

        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        raise HTTPException(status_code=400, detail="Path is not a file")


@router.delete("/{file_path:path}")
async def delete_file(file_path: str):
    path = get_filesystem_path(file_path)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    if is_llmignored(path):
        raise HTTPException(status_code=403, detail="File is ignored in `.llmignore`")
    if os.path.isfile(path):
        os.remove(path)
        return {"message": "File deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")


