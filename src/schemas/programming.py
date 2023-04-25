from pydantic import BaseModel
from typing import Optional


class UpdateFunctionDefinitionRequest(BaseModel):
    new_function_definition: Optional[str] = None


class NewFunctionDefinitionRequest(BaseModel):
    new_function_definition: str


class UpdateClassDefinitionRequest(BaseModel):
    new_class_definition: Optional[str] = None


class NewClassDefinitionRequest(BaseModel):
    new_class_definition: str


class UpdateFunctionDocstringRequest(BaseModel):
    new_docstring: str
