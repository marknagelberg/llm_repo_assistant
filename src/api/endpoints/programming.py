import os
import ast
import astunparse
from enum import Enum
from fastapi import FastAPI, HTTPException, Query, APIRouter, Body
from typing import Optional

from src.schemas import UpdateFunctionDefinitionRequest, UpdateClassDefinitionRequest, NewFunctionDefinitionRequest, NewClassDefinitionRequest, UpdateFunctionDocstringRequest
from src.utils import extract_file_summary, get_filesystem_path
from src.core.config import settings
from src.utils import is_llmignored

#TODO:
# - Endpoint to run test suite
# - Endpoint to run a single test
#     Perhaps an endpoint to run a command line command, from a list specified in the config file?
# - Add support for javascript

router = APIRouter()

class Language(str, Enum):
    python = "python"
    #javascript = "javascript"


@router.get("/summary/{language}/{file_path:path}")
async def get_summary(file_path: str, language: Language):
    """
    Retrieve high level class and function signatures of a programming file
    to understand what it does.
    """
    full_file_path = get_filesystem_path(file_path)
    if is_llmignored(full_file_path):
        raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
    if not os.path.isfile(full_file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(full_file_path, "r") as file:
        file_content = file.read()

    try:
        summary = extract_file_summary(file_content, language)
        return {"summary": summary}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"File {language} syntax is invalid")


def extract_python_function_definition(file_content: str, function_name: str):
    parsed_ast = ast.parse(file_content)

    function_node = None

    for node in ast.walk(parsed_ast):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            function_node = node
            break

    if function_node is None:
        raise HTTPException(status_code=404, detail="Function not found")

    decorators = [astunparse.unparse(decorator).strip() for decorator in function_node.decorator_list]
    function_definition = astunparse.unparse(function_node).strip()

    return {"decorators": decorators, "function_definition": function_definition}


@router.get("/function_definition/{language}/{file_path:path}/{function_name}")
async def get_function_definition(file_path: str, 
                                  function_name: str, 
                                  language: Language):
    full_file_path = get_filesystem_path(file_path)
    if is_llmignored(full_file_path):
        raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
    if not os.path.isfile(full_file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(full_file_path, "r") as file:
        file_content = file.read()

    if language.lower() == Language.python:
        try:
            return extract_python_function_definition(file_content, function_name)
        except SyntaxError as e:
            raise HTTPException(status_code=400, detail="Failed to parse the python file")
    else:
        raise HTTPException(status_code=400, detail="Unsupported language")


def extract_python_class_definition(file_content: str, class_name: str):
    parsed_ast = ast.parse(file_content)

    class_node = None

    for node in ast.walk(parsed_ast):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            class_node = node
            break

    if class_node is None:
        raise HTTPException(status_code=404, detail="Class not found")

    decorators = [astunparse.unparse(decorator).strip() for decorator in class_node.decorator_list]
    class_definition = astunparse.unparse(class_node).strip()

    return {"decorators": decorators, "class_definition": class_definition}


@router.get("/class_definition/{language}/{file_path:path}/{class_name}")
async def get_class_definition(language: Language, file_path: str, class_name: str):
    full_file_path = get_filesystem_path(file_path)
    if is_llmignored(full_file_path):
        raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
    if not os.path.isfile(full_file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(full_file_path, "r") as file:
        file_content = file.read()

    if language.lower() == Language.python:
        try:
            return extract_python_class_definition(file_content, class_name)
        except SyntaxError as e:
            raise HTTPException(status_code=400, detail="Failed to parse the python file")
    else:
        raise HTTPException(status_code=400, detail="Unsupported language")


def update_python_function_definition(full_file_path: str, file_content: str, function_name: str, new_function_definition: Optional[str] = None):
    try:
        parsed_ast = ast.parse(file_content)
    except SyntaxError:
        raise HTTPException(status_code=400, detail="Failed to parse the file")

    function_node = None
    for node in ast.walk(parsed_ast):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            function_node = node
            break

    if function_node is None:
        raise HTTPException(status_code=404, detail="Function not found")

    if new_function_definition is not None and new_function_definition.strip() != "":
        try:
            new_function_ast = ast.parse(new_function_definition)
            if not isinstance(new_function_ast.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
                raise ValueError("Invalid function definition")
        except (SyntaxError, ValueError) as e:
            raise HTTPException(status_code=400, detail="Invalid function definition")

    start_lineno = function_node.lineno - 1
    if function_node.decorator_list:
        start_lineno = min(dec.lineno for dec in function_node.decorator_list) - 1

    end_lineno = function_node.end_lineno
    lines = file_content.splitlines()

    if new_function_definition is not None and new_function_definition.strip() != "":
        new_file_content_lines = lines[:start_lineno] + new_function_definition.splitlines() + lines[end_lineno:]
        message = f"Function {function_name} updated"
    else:
        new_file_content_lines = lines[:start_lineno] + lines[end_lineno:]
        message = f"Function {function_name} deleted"

    new_file_content = '\n'.join(new_file_content_lines)

    with open(full_file_path, "w") as file:
        file.write(new_file_content)

    return {"status": "success", "message": message}


@router.put("/function_definition/{language}/{file_path:path}/{function_name}")
async def update_function_definition(
    language: Language,
    file_path: str,
    function_name: str,
    new_function_definition_request: UpdateFunctionDefinitionRequest
):
    """
    Update the definition of a function in a programming file. Completely rewrites the function,
    according to the provided `new_function_definition`, including the function signature.
    If no new function definition is provided, the function is deleted.
    """
    full_file_path = get_filesystem_path(file_path)
    if is_llmignored(full_file_path):
        raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
    if not os.path.isfile(full_file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(full_file_path, "r") as file:
        file_content = file.read()

    if language.lower() == "python":
        try:
            return update_python_function_definition(full_file_path, 
                                                     file_content, 
                                                     function_name, 
                                                     new_function_definition_request.new_function_definition)
        except SyntaxError as e:
            raise HTTPException(status_code=400, detail="Failed to parse the python file")
    else:
        raise HTTPException(status_code=400, detail="Unsupported language")



def update_python_class_definition(full_file_path: str, file_content: str, class_name: str, new_class_definition: Optional[str] = None):
    try:
        parsed_ast = ast.parse(file_content)
    except SyntaxError:
        raise HTTPException(status_code=400, detail="Failed to parse the file")

    class_node = None
    for node in ast.walk(parsed_ast):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            class_node = node
            break

    if class_node is None:
        raise HTTPException(status_code=404, detail="Class not found")

    if new_class_definition is not None and new_class_definition.strip() != "":
        try:
            new_class_ast = ast.parse(new_class_definition)
            if not isinstance(new_class_ast.body[0], ast.ClassDef):
                raise ValueError("Invalid class definition")
        except (SyntaxError, ValueError) as e:
            raise HTTPException(status_code=400, detail="Invalid class definition")

    start_lineno = class_node.lineno - 1
    end_lineno = class_node.end_lineno
    lines = file_content.splitlines()

    if new_class_definition is not None and new_class_definition.strip() != "":
        new_file_content_lines = lines[:start_lineno] + new_class_definition.splitlines() + lines[end_lineno:]
        message = f"Class {class_name} updated"
    else:
        new_file_content_lines = lines[:start_lineno] + lines[end_lineno:]
        message = f"Class {class_name} deleted"

    new_file_content = '\n'.join(new_file_content_lines)

    with open(full_file_path, "w") as file:
        file.write(new_file_content)

    return {"status": "success", "message": message}


@router.put("/class_definition/{language}/{file_path:path}/{class_name}")
async def update_class_definition(
    language: Language,
    file_path: str,
    class_name: str,
    new_class_definition_request: UpdateClassDefinitionRequest
):
    """
    Update the definition of a class in a programming file. Completely rewrites the class,
    according to the provided `new_class_definition`, including the class signature.
    If no new class definition is provided, the class is deleted.
    """
    full_file_path = get_filesystem_path(file_path)
    if is_llmignored(full_file_path):
        raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
    if not os.path.isfile(full_file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(full_file_path, "r") as file:
        file_content = file.read()

    if language.lower() == "python":
        try:
            return update_python_class_definition(full_file_path, 
                                                     file_content, 
                                                     class_name, 
                                                     new_class_definition_request.new_class_definition)
        except SyntaxError as e:
            raise HTTPException(status_code=400, detail="Failed to parse the python file")
    else:
        raise HTTPException(status_code=400, detail="Unsupported language")



def insert_python_function_definition(full_file_path: str, file_content: str, new_function_definition: str) -> None:
    try:
        new_function_ast = ast.parse(new_function_definition)
        if not new_function_ast.body:
            raise ValueError("Invalid function definition")
        if not isinstance(new_function_ast.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise ValueError("Invalid function definition")
    except (SyntaxError, ValueError) as e:
        raise HTTPException(status_code=400, detail="Invalid function definition")

    new_file_content = file_content.strip() + '\n\n' + new_function_definition.strip() + '\n'

    with open(full_file_path, "w") as file:
        file.write(new_file_content)


@router.post("/function_definition/{language}/{file_path:path}")
async def insert_new_function_definition(
    language: Language,
    file_path: str,
    new_function_request: NewFunctionDefinitionRequest,
):
    full_file_path = get_filesystem_path(file_path)
    if is_llmignored(full_file_path):
        raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
    if not os.path.isfile(full_file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(full_file_path, "r") as file:
        file_content = file.read()

    if language == Language.python:
        try:
            insert_python_function_definition(full_file_path, file_content, new_function_request.new_function_definition)
        except HTTPException as e:
            raise e
    else:
        raise HTTPException(status_code=400, detail="Unsupported language")

    return {"status": "success", "message": "Function definition created"}


def insert_python_class_definition(full_file_path: str, file_content: str, new_class_definition: str) -> None:
    try:
        new_class_ast = ast.parse(new_class_definition)
        if not new_class_ast.body:
            raise ValueError("Invalid class definition")
        if not isinstance(new_class_ast.body[0], ast.ClassDef):
            raise ValueError("Invalid class definition")
    except (SyntaxError, ValueError) as e:
        raise HTTPException(status_code=400, detail="Invalid class definition")

    new_file_content = file_content.strip() + '\n\n' + new_class_definition.strip() + '\n'

    with open(full_file_path, "w") as file:
        file.write(new_file_content)


@router.post("/class_definition/{language}/{file_path:path}")
async def create_class_definition(
    language: Language,
    file_path: str,
    new_class_request: NewClassDefinitionRequest,
):
    full_file_path = get_filesystem_path(file_path)
    if is_llmignored(full_file_path):
        raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
    if not os.path.isfile(full_file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(full_file_path, "r") as file:
        file_content = file.read()

    if language == Language.python:
        try:
            insert_python_class_definition(full_file_path, file_content, new_class_request.new_class_definition)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to insert the class definition")
    else:
        raise HTTPException(status_code=400, detail="Unsupported language")

    return {"status": "success", "message": "Class definition created"}


@router.get("/get_function_docstring/{language}/{file_path:path}/{function_name}")
async def get_function_docstring(language: Language, file_path: str, function_name: str):
    try:
        full_file_path = get_filesystem_path(file_path)
        if is_llmignored(full_file_path):
            raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
        if not os.path.isfile(full_file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Read the content of the file
        with open(full_file_path, 'r') as file:
            content = file.read()

        if language == Language.python:
            # Parse the content using the ast module
            parsed_content = ast.parse(content)

            # Find the specified function and extract its docstring
            for node in parsed_content.body:
                if (isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef)) and node.name == function_name:
                    docstring = ast.get_docstring(node)
                    return {"docstring": docstring}

            # If the function is not found, raise an exception
            raise HTTPException(status_code=404, detail="Function not found")
        else:
            raise HTTPException(status_code=400, detail="Unsupported language")

    except FileNotFoundError:
        # If the file is not found, raise an exception
        raise HTTPException(status_code=404, detail="File not found")

@router.put('/update_function_docstring/{language}/{file_path:path}/{function_name}')
async def update_function_docstring(
    language: Language,
    file_path: str,
    function_name: str,
    update_docstring_request: UpdateFunctionDocstringRequest
):
    try:
        full_file_path = get_filesystem_path(file_path)
        if is_llmignored(full_file_path):
            raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
        if not os.path.isfile(full_file_path):
            raise HTTPException(status_code=404, detail="File not found")

        with open(full_file_path, 'r') as file:
            content = file.read()

        if language == Language.python:
            parsed_content = ast.parse(content)
            for node in parsed_content.body:
                if (isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef)) and node.name == function_name:
                    node.body[0] = ast.Expr(value=ast.Str(s=update_docstring_request.new_docstring))
                    with open(full_file_path, 'w') as file:
                        file.write(astunparse.unparse(parsed_content))
                    return {'status': 'success', 'message': 'Function docstring updated'}
            raise HTTPException(status_code=404, detail='Function not found')
        else:
            raise HTTPException(status_code=400, detail="Unsupported language")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='File not found')

@router.get('/get_class_docstring/{language}/{file_path:path}/{class_name}')
async def get_class_docstring(language: Language, file_path: str, class_name: str):
    try:
        full_file_path = get_filesystem_path(file_path)
        if is_llmignored(full_file_path):
            raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
        if not os.path.isfile(full_file_path):
            raise HTTPException(status_code=404, detail="File not found")

        with open(full_file_path, 'r') as file:
            content = file.read()

        if language == Language.python:
            parsed_content = ast.parse(content)
            for node in parsed_content.body:
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    docstring = ast.get_docstring(node)
                    return {'docstring': docstring}
            raise HTTPException(status_code=404, detail='Class not found')
        else:
            raise HTTPException(status_code=400, detail="Unsupported language")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='File not found')

@router.put('/update_class_docstring/{language}/{file_path:path}/{class_name}')
async def update_class_docstring(
    language: Language,
    file_path: str,
    class_name: str,
    update_docstring_request: UpdateFunctionDocstringRequest
):
    try:
        full_file_path = get_filesystem_path(file_path)
        if is_llmignored(full_file_path):
            raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
        if not os.path.isfile(full_file_path):
            raise HTTPException(status_code=404, detail="File not found")

        with open(full_file_path, 'r') as file:
            content = file.read()

        if language == Language.python:
            parsed_content = ast.parse(content)
            for node in parsed_content.body:
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    node.body[0] = ast.Expr(value=ast.Str(s=update_docstring_request.new_docstring))
                    with open(full_file_path, 'w') as file:
                        file.write(astunparse.unparse(parsed_content))
                    return {'status': 'success', 'message': 'Class docstring updated'}
            raise HTTPException(status_code=404, detail='Class not found')
        else:
            raise HTTPException(status_code=400, detail="Unsupported language")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='File not found')

@router.get('/get_module_docstring/{language}/{file_path:path}')
async def get_module_docstring(language: Language, file_path: str):
    try:
        full_file_path = get_filesystem_path(file_path)
        if is_llmignored(full_file_path):
            raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
        if not os.path.isfile(full_file_path):
            raise HTTPException(status_code=404, detail="File not found")

        with open(full_file_path, 'r') as file:
            content = file.read()
        if language == Language.python:
            parsed_content = ast.parse(content)
            docstring = ast.get_docstring(parsed_content)
            return {'docstring': docstring}
        else:
            raise HTTPException(status_code=400, detail="Unsupported language")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='File not found')

@router.put('/update_module_docstring/{language}/{file_path:path}')
async def update_module_docstring(
    language: Language,
    file_path: str,
    update_docstring_request: UpdateFunctionDocstringRequest
):
    try:
        full_file_path = get_filesystem_path(file_path)
        if is_llmignored(full_file_path):
            raise HTTPException(status_code=404, detail="File is ignored in `.llmignore`")
        if not os.path.isfile(full_file_path):
            raise HTTPException(status_code=404, detail="File not found")

        with open(full_file_path, 'r') as file:
            content = file.read()

        if language == Language.python:
            parsed_content = ast.parse(content)
            parsed_content.body.insert(0, ast.Expr(value=ast.Str(s=update_docstring_request.new_docstring)))
            with open(full_file_path, 'w') as file:
                file.write(astunparse.unparse(parsed_content))
            return {'status': 'success', 'message': 'Module docstring updated'}
        else:
            raise HTTPException(status_code=400, detail="Unsupported language")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='File not found')
