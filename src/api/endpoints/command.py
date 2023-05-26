from typing import Optional
from fastapi import HTTPException, APIRouter
import docker

from src.core.config import settings
from src.utils import run_command_in_image, get_filesystem_path
from src.schemas import Command, CommandResponseModel, load_commands


from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Any, Dict
from pydantic import create_model
from pydantic.fields import Field, FieldInfo
from pydantic.schema import model_schema


commands_router = APIRouter()


def clean_name(flag_or_arg_name: str) -> str:
    # Function to clean argument names to be valid Python identifiers
    flag_or_arg_name = flag_or_arg_name.replace('-', '_')
    # If flag_name begins with digits, prepend 'flag_' to make it a valid Python identifier
    if flag_or_arg_name[0].isdigit():
        flag_or_arg_name = 'flag_' + flag_or_arg_name
    if flag_or_arg_name[0] == '_':
        flag_or_arg_name = 'flag' + flag_or_arg_name
    return flag_or_arg_name

def create_router_for_command(command: Command) -> APIRouter:
    router = APIRouter()

    # Create a Pydantic model for the command
    # Field(Query()) is used as only using Field() will not allow the field description to be added.
    # Seems to be an issue in Pydantic or FastAPI when handling dynamically created models. 
    fields = {}
    if command.args is not None:
        for arg in command.args:
            python_friendly_arg_name = clean_name(arg.name)
            fields[python_friendly_arg_name] = (str, Field(Query(..., description=arg.description))) if not arg.optional else (Optional[str], Field(Query(None, description=arg.description)))
        
    if command.flags is not None:
        for flag in command.flags:
            if flag.optional:  # Only optional flags are added as fields
                python_friendly_flag_name = clean_name(flag.name)
                if flag.type == "bool":
                    fields[python_friendly_flag_name] = (bool, Field(Query(False, description="Flag: " + flag.description)))
                if flag.type == "str":
                    fields[python_friendly_flag_name] = (str, Field(Query("", description="Flag: " + flag.description)))

    CommandModel = create_model(command.name.capitalize(), **fields)

    @router.post(f"/command/{command.name}", response_model=CommandResponseModel, description=command.description)
    async def run_command(
        command_model: CommandModel = Depends()
    ) -> Dict[str, Any]:
        command_line = [command.command]

        # Add arguments and flags to the command line
        if command.args is not None:
            for arg in command.args:
                python_friendly_arg_name = clean_name(arg.name)
                value = getattr(command_model, python_friendly_arg_name, None)
                if value is not None:
                    if arg.is_directory_or_file:
                        command_line.extend([get_filesystem_path(str(value))])
                    else:
                        command_line.extend([str(value)])
                    
        if command.flags is not None:
            for flag in command.flags:
                python_friendly_flag_name = clean_name(flag.name)
                if not flag.optional:  # Required flags are added automatically
                    if flag.is_short:
                        flag_str = f"-{flag.name}"
                    else:
                        flag_str = f"--{flag.name}"
                    command_line.append(flag_str)
                else:  # Optional flags are added only if their value is True
                    value = getattr(command_model, python_friendly_flag_name, None)
                    if value:
                        if flag.is_short:
                            flag_str = f"-{flag.name}"
                        else:
                            flag_str = f"--{flag.name}"
                        if flag.type == "str":  # Use the provided value as the flag's value
                            flag_value = str(value)
                            command_line.append(f"{flag_str}={flag_value}")
                        else:
                            command_line.append(flag_str)

        try:
            exit_code, output_str = run_command_in_image(settings.TARGET_REPO_DOCKER_IMAGE_NAME, command_line)
        except docker.errors.ImageNotFound:
            raise HTTPException(status_code=400, 
                                detail=f"Target repo docker image with name '{settings.TARGET_REPO_DOCKER_IMAGE_NAME}' not found.")
        return {"command": ' '.join(command_line), "exit_code": exit_code, "output_str": output_str}

    return router


commands = load_commands('command_config.yml')
for command in commands:
    router = create_router_for_command(command)
    commands_router.include_router(router)
