



"""
Carbon daemon for processing infrastructure resources and generating carbon emission reports.

This module provides a clean, extensible architecture for reading infrastructure data,
processing it through the carbon engine, and generating emission reports.
"""

from __future__ import annotations

from backend.src.schemas.resource import Resource
import csv
import logging
import time
from enum import Enum
from typing import Protocol, runtime_checkable

from backend.src.common.constants import (
    CARMEN_LOGO,
    HOURLY_INTERVAL_SECONDS,
    DAILY_SECONDS,
    UploadType,
)
from backend.src.common.errors import ErrorCode
from backend.src.common.known_exception import KnownException
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.daemon.cost_helpers import (
    create_cost_report,
    get_carbon_and_energy_values,
    process_cost_csv,
)
from backend.src.daemon.readers.abstract_reader import Reader
from backend.src.daemon.readers.compute.azure_compute_reader import (
    AzureComputeReaderStrategy,
)
from backend.src.daemon.readers.compute.local_compute_reader import (
    LocalComputeReaderStrategy,
)
from backend.src.daemon.readers.storage_reader import (
    StorageReaderStrategy,
)
from backend.src.daemon.writers.compute.azure_compute_writer import AzureComputeWriter
from backend.src.daemon.writers.compute.compute_writer import ComputeWriter
from backend.src.daemon.writers.compute.local_compute_writer import LocalComputeWriter
from backend.src.schemas.costResource import CostResource
from backend.src.schemas.storage_resource import StorageResource
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.utils import ioc_util

logger = logging.getLogger(__name__)


from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.utils import ioc_util

logger = logging.getLogger(__name__)




