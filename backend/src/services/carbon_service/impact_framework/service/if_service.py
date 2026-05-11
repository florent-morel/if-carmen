"""
This module defines the abstract base class for implementing Impact Framework (IF) service functionality.
"""

from __future__ import annotations
import os
import logging
import time
import copy
from abc import ABC
from collections import defaultdict
import yaml
from jinja2 import exceptions
from backend.src.common.constants import IF_FILES_DIR
from backend.src.common.known_exception import KnownException
from backend.src.common.errors import ErrorCode
from backend.src.schemas.pod import Pod
from backend.src.schemas.resource import Resource
from backend.src.schemas.compute_resource import ComputeResource
from backend.src.services.carbon_service.impact_framework.models.carbon.sci_e_pue import (
    SciEPue,
)
from backend.src.services.carbon_service.impact_framework.models.energy.e_cpu import (
    ECpu,
)
from backend.src.services.carbon_service.impact_framework.models.power.p_mem import PMem
from backend.src.services.carbon_service.impact_framework.models.energy.e_mem import (
    EMem,
)
from backend.src.services.carbon_service.impact_framework.models.energy.e_net import (
    ENet,
)
from backend.src.services.carbon_service.impact_framework.models.carbon.sci import Sci
from backend.src.services.carbon_service.impact_framework.models.carbon.sci_e import (
    SciE,
)
from backend.src.services.carbon_service.impact_framework.models.carbon.sci_m import (
    SciM,
)
from backend.src.services.carbon_service.impact_framework.models.carbon.sci_m_cpu import (
    SciMcpu,
)
from backend.src.services.carbon_service.impact_framework.models.carbon.sci_o import (
    SciO,
)
from backend.src.services.carbon_service.impact_framework.models.teads_curve import (
    TeadsCurve,
)
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)
from backend.src.services.carbon_service.carbon_service import CarbonService
from backend.src.utils.helpers import read_file
from backend.src.utils.metrics_mapper import MetricsMapper

logger = logging.getLogger(__name__)


class IFService(ABC, CarbonService):
    """
    This abstract class defines the methods that should be implemented by IFApp and IFVM service classes
    to compute carbon and energy metrics for given resources.
    """

    # TODO: Should be in conf
    INFILE_PATH = os.path.join(IF_FILES_DIR, "generated", "if_input")
    logger.info(f"IF_FILES_DIR: {IF_FILES_DIR}")
    OUTFILE_PATH = os.path.join(IF_FILES_DIR, "generated", "if_output")
    FILE_EXTENSION = ".yaml"

    def __init__(
        self, template_filename, pipeline_filename, aggregation_type, duration
    ):
        self.template = read_file(os.path.join(IF_FILES_DIR, "templates", template_filename))
        self.data = read_file(
            os.path.join(IF_FILES_DIR, "templates", pipeline_filename)
        )  # named as data even though it reads the pipeline.yml, since it will be filled with input.yaml data for IF
        self.data["aggregation_type"] = aggregation_type
        self.data["duration"] = duration

    def write_if_input(self, data, file_id: int):
        """
        Writes IF input yaml file.
        """

        try:
            with open(
                self.INFILE_PATH + str(file_id) + self.FILE_EXTENSION,
                mode="w",
                encoding="utf-8",
            ) as out_file:
                if_input = yaml.safe_load(self.template.render(data))
                yaml.safe_dump(if_input, out_file, sort_keys=False)
        except FileNotFoundError:
            logger.exception(
                "File not found when writing IF input for file ID %s", file_id
            )
            raise
        except exceptions.UndefinedError:
            logger.exception("Undefined variable in template for file ID %s", file_id)
            raise
        except TypeError:
            logger.exception("Type error in template for file ID %s", file_id)
            raise
        except yaml.parser.ParserError:
            logger.exception("YAML parsing error for template file ID %s", file_id)
            raise

    def run_command_in_shell(self, file_id):
        """
        Runs IF in shell.
        """
        cmd = (
            f'npx if-run --manifest "{self.INFILE_PATH}{file_id}{self.FILE_EXTENSION}" '
            f'--output "{self.OUTFILE_PATH}{file_id}{self.FILE_EXTENSION}"'
        )

        logger.info("Impact Framework command: %s", cmd)

        # throwing exception if the command fails
        exit_code = os.system(cmd)
        if exit_code != 0:
            error_msg = f"Impact Framework command failed with exit code {exit_code}"
            logger.error("%s: %s", error_msg, cmd)
            raise ValueError(error_msg)

    def run_if(self, resources: list[Resource], file_id: int = 0):
        """
        Executes the Impact Framework (IF) process for the given compute resources.

        This method generates the IF input file, runs the IF command in the shell,
        and logs the time taken for each step.

        Args:
            resources (list[Resource]): A list of compute resources (e.g., VMs or pods)
                                                       to be processed by the IF service.
            file_id (int, optional): An identifier for the input/output files. Defaults to 0.
        """
        logger.info(
            "Generating Impact Framework input file %d for %d resources...",
            file_id,
            len(resources),
        )
        data = copy.deepcopy(self.data)
        self.fill_parser_data(data, resources)
        start = time.time()
        self.write_if_input(data, file_id)
        logger.info(
            "Impact Framework input %d generated in %d seconds.",
            file_id,
            round(time.time() - start),
        )
        start = time.time()
        self.run_command_in_shell(file_id)
        logger.info(
            "Impact Framework completed the CO2 computation for file %d in %d seconds.",
            file_id,
            round(time.time() - start),
        )

    @staticmethod
    def get_models_info(data, provider: str = ""):
        """
        Concrete method that fills the model dictionary with basic model information depending on the defined pipeline.

        This is a concrete method in the IFService abstract class because it is commonly shared between
        the two types of IF services as of (21/05/2024).
        """

        model_classes = {
            "teads-curve": TeadsCurve,
            "e-cpu": ECpu,
            "sci-m": SciM,
            "sci-m-cpu": SciMcpu,
            "sci-o": SciO,
            "p-mem": PMem,
            "e-mem": EMem,
            "e-net": ENet,
            "sci": Sci,
            "sci-e": SciE,
            "sci-e-pue": SciEPue,
        }

        for model, cls in model_classes.items():
            if model in data["hardware_models"]:
                data["hardware_models"][model] = cls().__dict__
        return data

    @staticmethod
    def get_resource_inputs(resource: Resource, models: tuple[ModelUtilities] = None):
        """
        Generates input data for each time point of a compute unit using the specified models.

        Args:
            resource (Resource): Resource (e.g., VM or pod) to process.
            models (tuple[ModelUtilities], optional): Additional models to include in the input generation.

        Returns:
            list[dict[str, Any]]: A list of dictionaries containing inputs for each time point.
        """
        resource_inputs = []
        # common models used by VMs and Pods
        common_models = [TeadsCurve, SciO, SciEPue]
        if models:
            common_models.extend(models)
        for time_index in range(len(resource.time_points)):
            combined_inputs = {
                key: value
                for model in common_models
                for key, value in model.fill_inputs(resource, time_index).items()
            }
            resource_inputs.append(combined_inputs)
        return resource_inputs

    def get_resource_data(self, data, resources: list[Resource]):
        """
        Fills the VM dictionary with the data required
        """
        compute_resources = defaultdict(dict)
        for compute_resource in resources:
            compute_resources[compute_resource.id] = self.get_resource_inputs(
                compute_resource
            )
        data["resources"] = compute_resources

    def fill_parser_data(self, data, resources: list[Resource]):
        """
        Fills the data dictionary with the needed values of each model
        """
        provider = resources[0].provider if resources else ""
        self.get_models_info(data, provider or "")
        self.get_resource_data(data, resources)

    @staticmethod
    def get_measurements_from_output(
        if_output: dict[str, Any], compute_resource_id: str
    ) -> dict[str, dict[str, Any]]:
        """
        Extracts and organizes measurements from the IF output for a given compute resource.

        Args:
            if_output (dict[str, Any]): The parsed IF output data.
            compute_resource_id (str): The ID of the compute resource.
        Returns:
            dict[str, dict[str, Any]]: The updated metrics dictionary with aggregated and observation data.
        """

        metrics = {"timestamp": {"observations": []}}
        aggregated_data = if_output[compute_resource_id]["aggregated"]
        # populate aggregated values
        for metric in aggregated_data.keys():
            metrics[metric] = {
                "aggregated": round(aggregated_data[metric], 4),
                "observations": [],
            }
        # populate metric observations
        for timepoint in if_output[compute_resource_id]["outputs"]:
            for metric, metric_data in metrics.items():
                metric_data["observations"].append(
                    round(timepoint[metric], 4)
                    if metric not in ["timestamp", "duration"]
                    else None
                )
        return metrics

    def parse_if_output(
        self,
        resources: list[Resource],
        emission_breakdown_at_pod_level: bool = False,
        file_id: int = 0,
    ) -> list[Resource] | dict[str, dict[str, dict[str, list[Pod]]]]:
        """
        Parses the IF output file by removing the unnecessary information
        :return: parsed output dictionary at application or pod level
        """
        start = time.time()
        logger.info("Parsing output for file %d...", file_id)
        if_output = read_file(self.OUTFILE_PATH + str(file_id) + self.FILE_EXTENSION)
        if if_output["execution"]["status"] != "success":
            err_text = (
                f"IF has failed to calculate the carbon impact for file ID {file_id}."
            )
            logger.error(err_text)
            raise KnownException(ErrorCode.IF_EXECUTION_FAILED, details=err_text)
        if_output = if_output["tree"]["children"]
        if emission_breakdown_at_pod_level:
            output = IFService.aggregate_pod_level(resources, if_output)
        else:
            output = IFService.aggregate_app_level(resources, if_output, file_id)
        logger.info(
            "Output parsing completed in %d seconds for file %d",
            round(time.time() - start),
            file_id,
        )
        return output

    @staticmethod
    def aggregate_app_level(
        resources: list[Resource], if_output: dict, file_id: int
    ) -> list[Resource]:
        """
        Aggregates the application metrics
        """
        logger.info(
            "Parsing IF output for file number %s at application level", str(file_id)
        )
        for resource in resources:
            metrics = IFService.get_measurements_from_output(if_output, resource.id)
            MetricsMapper.map_metrics_to_resource(metrics, resource)
        return resources

    @staticmethod
    def aggregate_pod_level(
        compute_resources: list[ComputeResource], if_output: dict
    ) -> dict[str, dict[str, dict[str, list[Pod]]]]:
        """
        Aggregates the pod metrics
        """
        logger.info("Parsing IF output at pod level")
        output = IFService.initialize_output(compute_resources)
        for compute_resource in compute_resources:
            for pod in compute_resource.pods:
                pod_metrics = IFService.get_measurements_from_output(
                    if_output[compute_resource.id]["children"], pod.id
                )
                MetricsMapper.map_metrics_to_resource(pod_metrics, pod)
                # in order to increase readability of the result
                pod.cpu_util = [round(i, 4) for i in pod.cpu_util]
                output[pod.paas][pod.app][pod.namespace].append(pod)
        return output

    @staticmethod
    def initialize_output(compute_resources: list[ComputeResource]):
        """
        Initializes final output dictionary when emission_breakdown_at_pod_level is True
        Returns:
            output dict[str, dict[str, dict[str, list[Pod]]]]: dictionary with paas, app and namespace keys added
        """
        output: dict[str, dict[str, dict[str, list[Pod]]]] = {}
        for compute_resource in compute_resources:
            for pod in compute_resource.pods:
                if pod.paas not in output:
                    output[pod.paas] = {}
                if pod.app not in output[pod.paas]:
                    output[pod.paas][pod.app] = {}
                if pod.namespace not in output[pod.paas][pod.app]:
                    output[pod.paas][pod.app][pod.namespace] = []
        return output
