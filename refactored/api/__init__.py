from .routes import router
from .upload_routes import router as upload_router
from .config_routes import router as config_router

__all__ = ["router", "upload_router", "config_router"]
