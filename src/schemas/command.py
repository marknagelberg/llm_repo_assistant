import yaml
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

class Flag(BaseModel):
    name: str
    is_short: bool
    type: str
    description: str
    optional: bool = Field(default=True)

class Argument(BaseModel):
    name: str
    is_directory_or_file: bool
    description: str
    optional: bool = Field(default=True)

class Command(BaseModel):
    name: str
    command: str
    description: str
    args: Optional[List[Argument]]
    flags: Optional[List[Flag]]

class CommandResponseModel(BaseModel):
    command: str
    exit_code: int
    output_str: str


def load_commands(file_path: str) -> List[Command]:
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        commands = [Command(**command) for command in data['commands']]
        return commands
    except ValidationError as e:
        print(f"Error in `command_config.yml` configuration file: {e}")
        raise

