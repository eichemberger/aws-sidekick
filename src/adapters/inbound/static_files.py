"""
Static file serving configuration for FastAPI application
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pathlib

from infrastructure.logging import get_logger


def setup_static_files(app: FastAPI) -> None:
    """
    Setup static file serving for the Vue.js client
    
    Args:
        app: FastAPI application instance
    """
    logger = get_logger(__name__)
    logger.info("setting_up_static_files | configuring_vue_client_serving")
    
    current_dir = pathlib.Path(__file__).parent.parent.parent.parent
    client_dist_dir = current_dir / "client" / "dist"
    
    if not client_dist_dir.exists():
        logger.warning(f"client_dist_directory_not_found | path={client_dist_dir}")
        return
    
    logger.info(f"client_dist_directory_found | path={client_dist_dir}")
    
    assets_dir = client_dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        logger.info("assets_directory_mounted | route=/assets")
    
    static_directories = ["css", "js", "img", "fonts"]
    for static_dir in static_directories:
        static_path = client_dist_dir / static_dir
        if static_path.exists():
            app.mount(f"/{static_dir}", StaticFiles(directory=str(static_path)), name=static_dir)
            logger.info(f"static_directory_mounted | route=/{static_dir}")
    
    logger.info("static_files_setup_complete | vue_client_ready")


def setup_spa_fallback(app: FastAPI) -> None:
    """
    Setup SPA fallback route to serve Vue.js index.html for all non-API routes
    
    Args:
        app: FastAPI application instance
    """
    logger = get_logger(__name__)
    
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Serve the Vue.js SPA for all non-API routes"""
        current_dir = pathlib.Path(__file__).parent.parent.parent.parent
        client_dist_dir = current_dir / "client" / "dist"
        index_file = client_dist_dir / "index.html"
        
        if not client_dist_dir.exists():
            logger.warning("vue_client_not_built | returning_instructions")
            return {
                "message": "Vue.js client not built",
                "instructions": "Run 'cd client && npm run build' to build the client"
            }
        
        if not index_file.exists():
            logger.warning("vue_build_incomplete | returning_instructions")
            return {
                "message": "Vue.js build incomplete",
                "instructions": "Run 'cd client && npm run build' to build the client"
            }
        
        logger.debug(f"serving_spa_route | path={path}")
        return FileResponse(str(index_file))
    
    logger.info("spa_fallback_route_configured | catch_all_route_ready")


def setup_all_static_serving(app: FastAPI) -> None:
    """
    Configure all static file serving for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    logger = get_logger(__name__)
    logger.info("setting_up_all_static_serving | starting_static_configuration")
    
    setup_static_files(app)
    
    logger.info("static_serving_configured | static_setup_complete") 