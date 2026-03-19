"""
File as an abstraction for different IF models
"""

from abc import ABC

from backend.src.schemas.resource import Resource
from backend.src.services.carbon_service.impact_framework.models.metadata import (
    Metadata,
)


class ModelUtilities(ABC):
    """
    Abstract class for different IF models
    """

    def __init__(
        self,
        path: str,
        model: str,
        config: dict = None,
        output_metadata: list[Metadata] = None,
        input_metadata: list[Metadata] = None,
    ):
        self.path = path
        self.model = model
        self.config = config
        self.output_metadata = output_metadata
        self.input_metadata = input_metadata

    @staticmethod
    def fill_inputs(resource: Resource, time_index: int):
        """
        Fills the time point specific input values.
        Subclasses can override this method if needed.
        """
        raise NotImplementedError("Subclasses can implement this method if needed.")

    # IMP: Can be used if we implement the VM/Pod specific details to the IF input.yaml
    # IMP: add this import to implement
    # from backend.src.schemas.compute_resource import ComputeResource
    # @staticmethod
    # def fill_defaults(compute_resource: ComputeResource):
    #     """
    #     Fills the compute resource specific default values.
    #     Subclasses can override this method if needed.
    #     """
    #     raise NotImplementedError("Subclasses can implement this method if needed.")
