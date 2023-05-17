from typing import Optional
from fastapi import HTTPException, APIRouter
import docker

from src.core.config import settings
from src.utils import run_command_in_image
from src.schemas import Command, CommandResponseModel, load_commands


from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Any, Dict
from pydantic import create_model, BaseModel
from pydantic.fields import Field, FieldInfo
from pydantic.schema import model_schema

commands_router = APIRouter()


def create_router_for_command(command: Command) -> APIRouter:
    router = APIRouter()

    # Create a Pydantic model for the command
    # Field(Query()) is used as only using Field() will not allow the field description to be added.
    # Seems to be an issue in Pydantic or FastAPI when handling dynamically created models. 
    fields = {}
    for arg in command.args:
        fields[arg.name] = (str, Field(Query(..., description=arg.description))) if not arg.optional else (Optional[str], Field(Query(None, description=arg.description)))
    
    for flag in command.flags:
        if flag.optional:  # Only optional flags are added as fields
            if flag.type == "bool":
                fields[flag.name] = (bool, Field(Query(False, description="Flag: " + flag.description)))
            if flag.type == "str":
                fields[flag.name] = (str, Field(Query("", description="Flag: " + flag.description)))

    CommandModel = create_model(command.name.capitalize(), **fields)

    @router.post(f"/command/{command.name}", response_model=CommandResponseModel, description=command.description)
    async def run_command(
        command_model: CommandModel = Depends()
    ) -> Dict[str, Any]:
        command_line = [command.command]

        # Add arguments and flags to the command line
        for arg in command.args:
            value = getattr(command_model, arg.name, None)
            if value is not None:
                command_line.extend([arg.name, str(value)])

        for flag in command.flags:
            if not flag.optional:  # Required flags are added automatically
                if flag.is_short:
                    flag_str = f"-{flag.name}"
                else:
                    flag_str = f"--{flag.name}"
                command_line.append(flag_str)
            else:  # Optional flags are added only if their value is True
                value = getattr(command_model, flag.name, None)
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
        print(command_line)
        return {"command": ' '.join(command_line), "exit_code": exit_code, "output_str": output_str}

    return router


commands = load_commands('command_config.yml')
for command in commands:
    router = create_router_for_command(command)
    commands_router.include_router(router)
