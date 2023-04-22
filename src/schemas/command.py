from pydantic import BaseModel, Field
from typing import Optional


class TestRunRequest(BaseModel):
    test_file_path: Optional[str] = None
    test_function_name: Optional[str] = None

