from fastapi.staticfiles import StaticFiles

def mount_static_files(app):
    """Mount static files directory to the FastAPI app"""
    app.mount("/static", StaticFiles(directory="static"), name="static")