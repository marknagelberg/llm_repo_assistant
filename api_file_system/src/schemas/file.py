import re
from typing import Optional
from pydantic import BaseModel, validator, FilePath, DirectoryPath
import pathlib

from src.utils import get_full_path


class CreateFileRequest(BaseModel):
    file_name: str
    path: str
    content: str
    create_directories: bool = False

    @validator('file_name')
    def validate_file_name(cls, file_name: str) -> str:
        # Check if the file_name contains only valid characters
        if not re.match(r'^[\w\-. ]+$', file_name):
            raise ValueError('Invalid file name')

        # Sanitize the file_name by removing leading and trailing whitespace
        return file_name.strip()

    # Validate and sanitize the path field
    @validator('path')
    def validate_path(cls, path: str) -> pathlib.Path:
        # Remove any leading slashes and ensure it's a relative path
        sanitized_path = get_full_path(path)

        # Check if the sanitized_path contains only valid characters
        if not re.match(r'^[\w\-./ ]*$', sanitized_path):
            raise ValueError('Invalid path')

        return sanitized_path

class UpdateEntireFileRequest(BaseModel):
    content: str


class UpdateFileLineNumberRequest(BaseModel):
    start_line: int
    end_line: Optional[int] = None
    content: str
