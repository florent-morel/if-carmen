"""
This module defines the Impact Framework service class for VMs use case, which implements the IFService interface.
It provides functionality to compute carbon and energy metrics at infrastructure level using IF models.
"""

import concurrent
import logging
from abc import ABC

from backend.src.core.yaml_config_loader import config
from backend.src.services.carbon_service.impact_framework.models.cloud_metadata import (
    CloudMetadata,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)
from backend.src.services.carbon_service.impact_framework.models.power.p_vm_storage import (
    PVmStorage,
)
from backend.src.services.carbon_service.impact_framework.models.energy.e_vm_storage import (
    EVmStorage,
)
from backend.src.services.carbon_service.impact_framework.models.carbon.m_vm_storage import (
    MVmStorage,
)
from backend.src.services.carbon_service.impact_framework.models.carbon.sci_m import (
    SciM,
)
from backend.src.schemas.virtual_machine import VirtualMachine
from backend.src.services.carbon_service.impact_framework.models.power.p_cpu import PCpu
from backend.src.services.carbon_service.impact_framework.service.if_service import (
    IFService,
)
from backend.src.common.constants import DAILY_SECONDS

logger = logging.getLogger(__name__)

class IFVMService(IFService, ABC):
    """
    This class implements the CarbonService interface and provides functionality to compute
    carbon and energy metrics at infrastructure level using IF models.
    """

    def __init__(self, duration):
        super().__init__(
            "infrastructure_template.yml.j2",
            "infrastructure_pipeline.yml",
            "horizontal",
            duration,
        )

    def run_engine(self, vms: list[VirtualMachine]) -> list[VirtualMachine]:
        """
        Runs the IF model and returns the VMs with their computed energy and CO2 values.
        """
        all_chunks = self._chunk_by_provider(vms, config.impact_framework.chunk_size_vm)

        def compute_metrics_for_chunk(chunk: list[VirtualMachine], index: int) -> None:
            self.run_if(chunk, file_id=index)
            self.parse_if_output(chunk, file_id=index)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(compute_metrics_for_chunk, chunk, i)
                for i, chunk in enumerate(all_chunks)
            ]
            concurrent.futures.wait(futures)
        return vms

    def get_models_info(self, data, provider: str = ""):
        """
        Fill the model dictionary with IF plugin configurations for the VM pipeline.

        CloudMetadata is not an IF plugin and is not registered here; it populates
        VM inputs in Python via fill_inputs before the IF pipeline runs.
        """
        provider_config = config.provider_configs.get(provider)
        super().get_models_info(data, provider)
        if "p-cpu" in data["hardware_models"]:
            data["hardware_models"]["p-cpu"] = PCpu().__dict__
        if "p-vm-storage" in data["hardware_models"]:
            data["hardware_models"]["p-vm-storage"] = PVmStorage(provider_config).__dict__
        if "e-vm-storage" in data["hardware_models"]:
            data["hardware_models"]["e-vm-storage"] = EVmStorage().__dict__
        if "m-vm-storage" in data["hardware_models"]:
            data["hardware_models"]["m-vm-storage"] = MVmStorage().__dict__
        if "sci-m" in data["hardware_models"]:
            data["hardware_models"]["sci-m"] = SciM().__dict__

    @staticmethod
    def get_resource_inputs(
        virtual_machine: VirtualMachine,
        models: tuple[ModelUtilities, ...] = (
            CloudMetadata,
            PVmStorage,
        ),
        fallback_duration: int = DAILY_SECONDS,
    ):
        """
        Generate input data for each time point of a VM using the specified models.

        CloudMetadata resolves the instance type from the provider CSV and injects
        cpu/thermal-design-power, vcpus-total, vcpus-allocated, and memory/requested
        for downstream IF pipeline steps.
        """
        return IFService.get_resource_inputs(virtual_machine, models, fallback_duration)
