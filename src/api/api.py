from fastapi import APIRouter

from src.api.endpoints import files, directories, utils, programming, command, context, ai_plugin

api_router = APIRouter()
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(directories.router, prefix="/directories", tags=["directories"])
api_router.include_router(programming.router, prefix="/programming", tags=["programming"])
api_router.include_router(command.router, prefix="/command", tags=["command"])
api_router.include_router(context.router, prefix="/context", tags=["context"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])

ai_plugin_router = APIRouter()
ai_plugin_router.include_router(ai_plugin.router, tags=['ai_plugin'])
