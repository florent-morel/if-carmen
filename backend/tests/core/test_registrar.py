"""
Module containing unit tests for the registration of a FastAPI application.

This module includes test cases for registering routes, models, and configuring a FastAPI application
using the functions defined in the `backend.src.core.registrar` module.
"""

from unittest.mock import MagicMock, patch

from fastapi import FastAPI

from backend.src.core.registrar import register_app, register_router, register_models
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


@patch("backend.src.core.registrar.FastAPI")
@patch("backend.src.core.registrar.register_router")
@patch("backend.src.core.registrar.register_models")
def test_register_app(mock_register_models, mock_register_router, mock_fastapi):
    """
    Test registering FastAPI application.
    """
    mock_settings = MagicMock()
    mock_settings.FASTAPI.TITLE = "Test Title"
    mock_settings.FASTAPI.DESCRIPTION = "Test Description"
    mock_settings.FASTAPI.DOCS_URL = "/test/docs"
    mock_settings.FASTAPI.REDOCS_URL = "/test/redocs"
    mock_settings.FASTAPI.OPENAPI_URL = "/test/openapi"
    with patch("backend.src.core.registrar.settings", mock_settings):
        app = register_app()

    mock_register_router.assert_called_once_with(app)
    mock_fastapi.assert_called_once_with(
        title="Test Title",
        description="Test Description",
        docs_url="/test/docs",
        redoc_url="/test/redocs",
        openapi_url="/test/openapi",
    )
    mock_register_models.assert_called_once()


@patch("backend.src.api.api.api_router")
def test_register_router(mock_api_router):
    """
    Test registering router with FastAPI application.
    """
    mock_app = MagicMock(spec=FastAPI)
    register_router(mock_app)
    mock_app.include_router.assert_called_once_with(mock_api_router)


@patch("backend.src.core.registrar.ioc_registered_models")
@patch("backend.src.core.registrar.IocRegistrationModel")
def test_register_models(mock_ioc_registration_model, mock_ioc_registered_models):
    """
    Test registering models with IoC container.
    """
    register_models()

    expected_calls = [
        (("IFApp", CarbonService, IFAppService),),
        (("IFVm", CarbonService, IFVMService),),
        (("IFStorage", CarbonService, IFStorageService),),
        (("IFMiscServices", CarbonService, IFMiscServicesService),),
    ]

    mock_ioc_registration_model.assert_has_calls(expected_calls)
    assert len(mock_ioc_registered_models.append.call_args_list) == 4
