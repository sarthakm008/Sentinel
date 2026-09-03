"""Sentinel Backend Entry Point.

This module provides the entry point for running the Sentinel backend.
It reads configuration from environment variables and starts the FastAPI application.
"""

import os
import uvicorn

from backend.app.main import app


def main():
    """Run the Sentinel backend server."""
    # Get port from environment variable (Render sets PORT)
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Reload only in development
    reload = os.getenv("BACKEND_RELOAD", "false").lower() == "true"
    
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()