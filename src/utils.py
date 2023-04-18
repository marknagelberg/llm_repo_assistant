import os
import subprocess
import pathlib
from pathlib import Path
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

        else:
            # Top-level statements
            source_code = ast.unparse(node).strip()

            if source_code:
                statement_summary = {
                    "type": "statement",
                    "source": source_code,
                }
                summary.append(statement_summary)

    return summary


def extract_file_summary(file_content: str, language: str) -> List[Dict[str, Any]]:
    if language == "python":
        return extract_python_summary(file_content)
    else:
        raise ValueError(f"Language {language} not supported")


def load_llmignore_patterns() -> List[str]:
    if os.path.exists(settings.LLMIGNORE_PATH):
        with open(settings.LLMIGNORE_PATH, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
    return []


def is_llmignored(file_path: str) -> bool:
    llmignore_patterns = load_llmignore_patterns()
    for pattern in llmignore_patterns:
        path_obj = Path(file_path)
        if path_obj.match(pattern):
            return True
    return False


def is_git_repository(directory: str) -> bool:
    try:
        subprocess.run(
            ["git", "-C", directory, "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_git_diff(directory: str) -> str:
    if not is_git_repository(directory):
        raise ValueError("The directory is not a git repository")

    # Check if there are any commits
    check_commits = subprocess.run(["git", "-C", directory, "rev-parse", "--quiet", "--verify", "HEAD"], 
                                   capture_output=True, 
                                   text=True)

    if check_commits.returncode != 0:
        # No commits, so return an empty diff
        return ""

    result = subprocess.run(
        ["git", "-C", directory, "diff", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout

