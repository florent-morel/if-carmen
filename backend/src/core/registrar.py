"""
This module handles the registration of FastAPI application, routers, and carbon measurement models.
"""

from fastapi import FastAPI
from backend.src.core.settings import settings
from backend.src.common.exception_handler import register_exception_handlers
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.services.carbon_service.impact_framework.service.if_app_service import (
    IFAppService,
)
from backend.src.services.carbon_service.impact_framework.service.if_misc_services_service import (
    IFMiscServicesService,
)
from backend.src.services.carbon_service.impact_framework.service.if_vm_service import (
    IFVMService,
)
from backend.src.services.carbon_service.impact_framework.service.if_storage_service import (
    IFStorageService,
)
from backend.src.utils.ioc_util import IocRegistrationModel, ioc_registered_models


def register_app() -> FastAPI:
    """
    Registers FastAPI application.

    Returns:
        FastAPI: The registered FastAPI application.
    """
    app = FastAPI(
        title=settings.FASTAPI.TITLE,
        description=settings.FASTAPI.DESCRIPTION,
        docs_url=settings.FASTAPI.DOCS_URL,
        redoc_url=settings.FASTAPI.REDOCS_URL,
        openapi_url=settings.FASTAPI.OPENAPI_URL,
    )
    register_router(app)
    register_models()
    register_exception_handlers(app)

    return app


def register_router(app: FastAPI):
    """
    Registers the router.

    Args:
        app (FastAPI): The FastAPI application to register the router with.
    """
    from backend.src.api.api import api_router

    app.include_router(api_router)


def register_models() -> None:
    """
    Register carbon calculation models with IoC container.

    Registers services for:
    - IFApp: Application-level carbon calculations
    - IFVm: Virtual Machine carbon calculations
    - IFStorage: Storage resource carbon calculations
    - IFMiscServices: Misc Services model calculations
    """
    ioc_registered_models.append(
        IocRegistrationModel("IFApp", CarbonService, IFAppService)
    )
    ioc_registered_models.append(
        IocRegistrationModel("IFVm", CarbonService, IFVMService)
    )
    ioc_registered_models.append(
        IocRegistrationModel("IFStorage", CarbonService, IFStorageService)
    )
    ioc_registered_models.append(
        IocRegistrationModel("IFMiscServices", CarbonService, IFMiscServicesService)
    )
