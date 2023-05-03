import os
import subprocess
import pathlib
from pathlib import Path
import ast
from typing import List, Dict, Any
from fastapi import HTTPException
import fnmatch
import docker
from typing import Tuple

from src.core.config import settings


def sanitize_path(path: str) -> str:
    return path.lstrip('/')


def get_filesystem_path(endpoint_path: str) -> str:
    """
    Given a target repo path specified by an endpoint, return the actual
    path on the filesystem.
    """
    sanitized_path = sanitize_path(endpoint_path)
    full_path = os.path.join(settings.REPO_ROOT, sanitized_path)

    if not str(full_path).startswith(str(settings.REPO_ROOT)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    return str(full_path)

def get_endpoint_path(file_path: str) -> str:
    """
    Given a file path to target repo, return the path that should be used for the endpoint.
    """
    if not str(file_path).startswith(str(settings.REPO_ROOT)):
        raise HTTPException(status_code=400, 
                            detail="Invalid file path - must start with repo root {}".format(str(settings.REPO_ROOT)))
    # Remove settings.REPO_ROOT from the beginning of file_path
    endpoint_path = file_path[len(settings.REPO_ROOT):]
    # Remove leading slash
    endpoint_path = endpoint_path.lstrip("/")
    return endpoint_path


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


def is_llmignored(filesystem_path: str) -> bool:
    llmignore_patterns = load_llmignore_patterns()
    path_obj = Path(filesystem_path)
    for pattern in llmignore_patterns:
        if fnmatch.fnmatch(path_obj.name, pattern):
            return True
        if fnmatch.fnmatch(str(path_obj), pattern):
            return True
        if fnmatch.fnmatch(str(path_obj.relative_to(path_obj.anchor)), pattern):
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


def run_command_in_image(image_name: str, command: List[str]) -> Tuple[int, str]:
    client = docker.from_env()

    # Run the command in a new container
    container = client.containers.run(image=image_name, 
                                      command=command, 
                                      detach=True,
                                      working_dir=settings.REPO_ROOT,
                                      volumes={settings.TARGET_REPO_PATH: {"bind": settings.REPO_ROOT, "mode": "rw"}})

    # Wait for the container to finish executing
    result = container.wait()

    # Fetch the logs (standard output and standard error)
    output = container.logs()

    # Clean up the container
    container.remove()

    # Decode the output to a string
    output_str = output.decode("utf-8")

    # The result contains a dictionary with status and StatusCode (exit code)
    exit_code = result['StatusCode']

    return exit_code, output_str
