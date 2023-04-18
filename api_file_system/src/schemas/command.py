from pydantic import BaseModel
from typing import Optional


class TestRunRequest(BaseModel):
    test_name: Optional[str] = None
