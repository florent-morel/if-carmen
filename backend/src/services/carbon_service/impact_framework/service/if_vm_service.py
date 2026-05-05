"""
This module defines the Impact Framework service class for VMs use case, which implements the IFService interface.
It provides functionality to compute carbon and energy metrics at infrastructure level using IF models.
"""

import concurrent
from abc import ABC
from itertools import groupby
from typing import List, Tuple

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

    def run_engine(self, vms: List[VirtualMachine]) -> List[VirtualMachine]:
        """
        Runs the IF model and returns the VMs with
        their computed energy and CO2 values.
        Args:
            vms: List of the VM objects,
             each of the VM objects includes the info of different times during the day.

        Returns:
            List[Pod]: List of VMs with updated energy consumption and carbon emissions' metrics.
        """
        chunk_size = 430

        # Group by provider so each IF run uses the correct provider-specific CSV and config.
        # Sort first so groupby sees consecutive equal keys.
        def _provider_key(vm: VirtualMachine) -> str:
            return vm.provider if isinstance(vm.provider, str) else ""

        sorted_vms = sorted(vms, key=_provider_key)
        all_chunks: list[list[VirtualMachine]] = []
        for _, group in groupby(sorted_vms, key=_provider_key):
            group_list = list(group)
            for x in range(0, len(group_list), chunk_size):
                all_chunks.append(group_list[x : x + chunk_size])

        def compute_metrics_for_chunk(chunk, index):
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
        Concrete method that fills the model dictionary with basic model information depending on the defined pipeline.

        This is a concrete method in the IFService abstract class because it is commonly shared between
        the two types of IF services as of (21/05/2024).
        """
        provider_config = config.provider_configs.get(provider)
        super().get_models_info(data, provider)
        if "cloud-metadata" in data["hardware_models"]:
            if not provider:
                # cloud-metadata is a mandatory pipeline step (infrastructure_pipeline.yml)
                # that performs a CSV lookup to resolve cpu-tdp, vcpus-total, etc. from the
                # provider instances file. Without a provider there is no CSV, so IF would
                # crash with an unhelpful error deep inside the pipeline. Fail early instead.
                raise ValueError(
                    "provider is required for VM carbon calculation: cloud-metadata "
                    "needs a provider instances CSV to resolve CPU specs."
                )
            data["hardware_models"]["cloud-metadata"] = CloudMetadata(provider).__dict__
        if "p-cpu" in data["hardware_models"]:
            data["hardware_models"]["p-cpu"] = PCpu().__dict__
        if "p-vm-storage" in data["hardware_models"]:
            data["hardware_models"]["p-vm-storage"] = PVmStorage(
                provider_config
            ).__dict__
        if "e-vm-storage" in data["hardware_models"]:
            data["hardware_models"]["e-vm-storage"] = EVmStorage().__dict__
        if "m-vm-storage" in data["hardware_models"]:
            data["hardware_models"]["m-vm-storage"] = MVmStorage().__dict__
        if "sci-m" in data["hardware_models"]:
            data["hardware_models"]["sci-m"] = SciM().__dict__

    # noinspection PyRedundantParentheses
    @staticmethod
    def get_resource_inputs(
        virtual_machine: VirtualMachine,
        models: Tuple[ModelUtilities] = (
            CloudMetadata,
            PVmStorage,
        ),
    ):
        """
        Generates input data for each time point of a compute unit using the specified models.

        Args:
            virtual_machine (VirtualMachine): The virtual machine to process.
            models (Tuple[ModelUtilities], optional): Additional models to include in the input generation.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing inputs for each time point.
        """
        return IFService.get_resource_inputs(virtual_machine, models)
