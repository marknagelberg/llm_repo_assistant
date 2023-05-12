import os
import sys
from enum import Enum
import subprocess
from typing import Optional, List, Tuple
from fastapi import HTTPException, APIRouter
from contextlib import contextmanager
import docker

from src.core.config import settings
from src.utils import get_filesystem_path, run_command_in_image
from src.schemas import Command, load_commands


from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict
import subprocess

commands_router = APIRouter()


def create_router_for_command(command: Command) -> APIRouter:
    router = APIRouter()

    @router.post(f"/command/{command.name}")
    async def run_command(
        args: Dict[str, Any] = Depends()
    ) -> Dict[str, Any]:
        command_line = [command.command]

        # Add arguments and flags to the command line
        if command.args:
            for arg in command.args:
                if arg.name in args and args[arg.name] is not None:
                    command_line.extend([arg.name, str(args[arg.name])])

        if command.flags:
            for flag in command.flags:
                if flag.name in args and args[flag.name] is not None:
                    if flag.is_short:
                        flag_str = f"-{flag.name}"
                    else:
                        flag_str = f"--{flag.name}"
                    command_line.append(flag_str)
                    if flag.type == 'str':
                        command_line.append(str(args[flag.name]))

        # Run the command in the specified docker image
        try:
            exit_code, output_str = run_command_in_image(settings.TARGET_REPO_DOCKER_IMAGE_NAME, command_line)
        except docker.errors.ImageNotFound:
            raise HTTPException(status_code=400, 
                                detail=f"Target repo docker image with name '{settings.TARGET_REPO_DOCKER_IMAGE_NAME}' not found.")
        return {"exit_code": exit_code, "output_str": output_str}

    return router

commands = load_commands('command_config.yml')
for command in commands:
    router = create_router_for_command(command)
    commands_router.include_router(router)
