"""
Main file where the application starts.
"""

import logging

import uvicorn
from fastapi import FastAPI

from backend.src.common.constants import CARMEN_LOGO
from backend.src.common.carmen_exception import CarmenException
from backend.src.core.registrar import register_app
from backend.src.core.settings import settings

logger = logging.getLogger(__name__)

app: FastAPI = register_app()


def main():
    """
    Main entry point for the Carbon Engine API.
    This function is used when running via the installed package.
    """
    try:
        logger.info(CARMEN_LOGO)
        logger.info("Running Fast API application.")
        uvicorn.run(
            "backend.src.main:app",
            host=settings.UVICORN.HOST,
            port=settings.UVICORN.PORT,
            reload=settings.UVICORN.RELOAD,
            timeout_keep_alive=settings.UVICORN.TIME_OUT,
        )
    except CarmenException:
        logger.exception("FastAPI start failed")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    main()
