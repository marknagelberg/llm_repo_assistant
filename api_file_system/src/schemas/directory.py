from pydantic import BaseModel

class DirectoryRequest(BaseModel):
    dir_name: str
    path: str
