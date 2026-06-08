"""
sci-m-cpu model of IF
"""

from backend.src.schemas.pod import Pod
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)

from backend.src.common.constants import (
    IF_INPUT_RESOURCES_RESERVED,
    IF_INPUT_RESOURCES_TOTAL,
)


class SciMcpu(ModelUtilities):
    """
    Concrete class for the Sci-M-CPU model of IF
    """

    def __init__(self):
        super().__init__('"@grnsft/if-plugins"', "SciM")

    @staticmethod
    def fill_inputs(pod: Pod, time_index: int):
        """
        Fills the sci-m-cpu input val. from the pod, returns an empty dict if there is no values
        """
        #TODO: Magic number: 66? To be moved to carbon_values.yaml
        return {
            IF_INPUT_RESOURCES_RESERVED: pod.requested_cpu[time_index],
            IF_INPUT_RESOURCES_TOTAL: 66,
        }
