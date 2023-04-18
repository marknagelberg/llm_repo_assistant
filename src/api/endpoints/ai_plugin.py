
from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

# Create a new APIRouter instance
router = APIRouter()

# Define the path to the file you want to serve

@router.get("/.well-known/ai-plugin.json")
async def serve_ai_plugin_json():
    plugin_json_file_path = Path("src/ai-plugin.json")
    # Check if the file exists
    if not plugin_json_file_path.is_file():
        return {"detail": "File not found"}, 404

    # Serve the file using FileResponse
    return FileResponse(plugin_json_file_path)


@router.get("/logo.png")
async def serve_logo_png():
    logo_file_path = Path("src/logo.png")
    # Check if the file exists
    if not logo_file_path.is_file():
        return {"detail": "File not found"}, 404

    # Serve the file using FileResponse
    return FileResponse(logo_file_path)

