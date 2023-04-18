import pathlib
import ast
from typing import List, Dict, Any
from fastapi import HTTPException

from src.core.config import settings

def sanitize_path(path: str) -> str:
    return path.lstrip('/')

def get_full_path(path: str) -> str:
    sanitized_path = sanitize_path(path)
    full_path = pathlib.Path(settings.REPO_ROOT / sanitized_path).resolve()

    if not str(full_path).startswith(str(settings.REPO_ROOT)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    return str(full_path)


def extract_python_summary(file_content: str) -> List[Dict[str, Any]]:
    summary = []
    parsed_ast = ast.parse(file_content)

    for node in ast.iter_child_nodes(parsed_ast):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arg_names = [arg.arg for arg in node.args.args]
            arg_types = [getattr(arg.annotation, "id", None) for arg in node.args.args]
            return_type = getattr(node.returns, "id", None) if node.returns else None

            function_summary = {
                "type": "function",
                "name": node.name,
                "args": [{"name": name, "type": type_} for name, type_ in zip(arg_names, arg_types)],
                "return_type": return_type,
            }
            summary.append(function_summary)

        elif isinstance(node, ast.ClassDef):
            class_summary = {
                "type": "class",
                "name": node.name,
                "methods": [],
            }

            for method_node in ast.iter_child_nodes(node):
                if isinstance(method_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    arg_names = [arg.arg for arg in method_node.args.args]
                    arg_types = [getattr(arg.annotation, "id", None) for arg in method_node.args.args]
                    return_type = getattr(method_node.returns, "id", None) if method_node.returns else None

                    method_summary = {
                        "type": "function",
                        "name": method_node.name,
                        "args": [{"name": name, "type": type_} for name, type_ in zip(arg_names, arg_types)],
                        "return_type": return_type,
                    }
                    class_summary["methods"].append(method_summary)

            summary.append(class_summary)

    return summary


def extract_file_summary(file_content: str, language: str) -> List[Dict[str, Any]]:
    if language == "python":
        return extract_python_summary(file_content)
    else:
        raise ValueError(f"Language {language} not supported")

