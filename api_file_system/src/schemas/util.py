from pydantic import BaseModel
from typing import Optional


class MoveRequest(BaseModel):
    src_path: str
    dest_path: str

