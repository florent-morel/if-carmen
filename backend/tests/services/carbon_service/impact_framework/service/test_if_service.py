# pylint: disable=too-many-arguments,no-value-for-parameter
"""
Unit tests for the IF_Service in impact framework.
"""
import unittest
from unittest.mock import patch, mock_open as open_mock, MagicMock
from itertools import cycle
import yaml
from jinja2 import Template, exceptions
from backend.src.schemas.application import Application
from backend.src.schemas.pod import Pod
from backend.src.services.carbon_service.impact_framework.service.if_service import (
    IFService,
)
from backend.src.schemas.compute_resource import ComputeResource
from backend.src.services.carbon_service.impact_framework.models.model_utilities import (
    ModelUtilities,
)
from backend.src.common.carmen_exception import CarmenException
from backend.src.common.constants import DAILY_SECONDS


class TestIFService(unittest.TestCase):
    """
    Unit tests for IFService.
    """

    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.read_file"
    )
    def test_init(self, mock_read_file):
        """
        Test that IFService initializes correctly with the provided parameters.
        """
        mock_read_file.side_effect = [
            Template("template_content"),  # Return as a Jinja2 Template
            {"hardware_models": {}},  # Return for config.yml
        ]

        service = IFService(
            "app_template.yml.j2", "app_pipeline.yml", "aggregation", "duration"
        )

        self.assertEqual(mock_read_file.call_count, 2)

        self.assertIn("aggregation_type", service.data)
        self.assertEqual(service.data["aggregation_type"], "aggregation")
        self.assertEqual(service.data["duration"], "duration")

    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    @patch("builtins.open", new_callable=MagicMock)
    @patch("yaml.safe_dump")
    @patch("yaml.safe_load")
    def test_write_if_input_success(
        self, mock_safe_load, mock_safe_dump, mock_open_file
    ):
        """
        Test that write_if_input writes the IF input file successfully.
        """
        mock_service = MagicMock()
        mock_service.INFILE_PATH = "mock_path"
        mock_service.FILE_EXTENSION = ".yaml"
        mock_service.template.render.return_value = {"mock_key": "mock_value"}
        mock_data = {
            "aggregation_type": "mock_aggregation",
            "duration": "mock_duration",
        }

        mock_safe_load.return_value = {"mock_key": "mock_value"}
        mock_safe_dump.return_value = None  # just writes the file so none

        IFService.write_if_input(mock_service, mock_data, file_id=0)
        mock_open_file.assert_called_once_with(
            mock_service.INFILE_PATH + "0" + mock_service.FILE_EXTENSION,
            mode="w",
            encoding="utf-8",
        )

        mock_service.template.render.assert_called_once_with(mock_data)

        mock_safe_dump.assert_called_once_with(
            mock_safe_load.return_value,
            mock_open_file.return_value.__enter__(),
            sort_keys=False,
        )

        with patch("logging.warning") as mock_warning, patch(
            "logging.error"
        ) as mock_error:
            mock_error.assert_not_called()
            mock_warning.assert_not_called()

    @patch("builtins.open", new_callable=open_mock)
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.logger.error"
    )
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_write_if_input_file_not_found(self, mock_logging_error, mock_open_file):
        """
        Test that write_if_input raises a FileNotFoundError if the file path is not found
        and logs an error message.
        """
        mock_service = MagicMock()

        mock_service.INFILE_PATH = "mock_path.yaml"
        mock_service.template.render.return_value = "rendered_template"
        mock_data = {"aggregation_type": "aggregation", "duration": "duration"}

        mock_open_file.side_effect = FileNotFoundError("File not found")

        with self.assertRaises(FileNotFoundError):
            IFService.write_if_input(mock_service, mock_data, file_id=0)

        mock_logging_error.assert_called_once()
        self.assertIn(
            "File not found when writing IF input", mock_logging_error.call_args[0][0]
        )

    @patch("builtins.open", new_callable=open_mock)
    @patch("yaml.safe_load")
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.logger.error"
    )
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_write_if_input_yaml_parser_error(
        self, mock_logging_error, mock_safe_load, mock_open_file
    ):
        """
        Test that write_if_input raises a yaml.parser.ParserError if the YAML content is invalid
        and logs a warning message.
        """
        mock_service = MagicMock()

        mock_service.INFILE_PATH = "mock_path"
        mock_service.FILE_EXTENSION = ".yaml"
        mock_service.template.render.return_value = "rendered_template"
        mock_data = {"aggregation_type": "aggregation", "duration": "duration"}

        mock_safe_load.side_effect = yaml.parser.ParserError("Error parsing YAML")

        with self.assertRaises(yaml.parser.ParserError):
            IFService.write_if_input(mock_service, mock_data, 0)
        mock_logging_error.assert_called_once()
        mock_open_file.assert_called_once()

        # Reset mocks
        mock_logging_error.reset_mock()
        mock_open_file.reset_mock()

        mock_safe_load.side_effect = exceptions.UndefinedError(
            "Undefined variable in template"
        )
        with self.assertRaises(exceptions.UndefinedError):
            IFService.write_if_input(mock_service, mock_data, 0)
        mock_logging_error.assert_called_once()

        # Reset mocks
        mock_logging_error.reset_mock()
        mock_open_file.reset_mock()

        mock_safe_load.side_effect = TypeError("Type error in template")
        with self.assertRaises(TypeError):
            IFService.write_if_input(mock_service, mock_data, 0)
        mock_logging_error.assert_called_once()

    @patch("os.system")
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_run_command_in_shell_success(self, mock_os_system):
        """
        Test that the run_command_in_shell method runs the command successfully.
        """
        mock_service = MagicMock(spec=IFService)
        mock_service.INFILE_PATH = "mock_infile_path"
        mock_service.OUTFILE_PATH = "mock_outfile_path"
        mock_service.FILE_EXTENSION = "mock_file_extension"
        mock_os_system.return_value = 0

        result = IFService.run_command_in_shell(mock_service, 0)

        mock_os_system.assert_called_once_with(
            f'npx if-run --manifest "{mock_service.INFILE_PATH}{0}{mock_service.FILE_EXTENSION}" '
            f'--output "{mock_service.OUTFILE_PATH}{0}{mock_service.FILE_EXTENSION}"'
        )
        self.assertIsNone(result)

    @patch("os.system")
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.logger.error"
    )
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_run_command_in_shell_failure(self, mock_logging_error, mock_os_system):
        """
        Test that the run_command_in_shell method raises an exception on failure.
        """
        mock_service = MagicMock(spec=IFService)
        mock_service.INFILE_PATH = "mock_infile_path"
        mock_service.OUTFILE_PATH = "mock_outfile_path"
        mock_service.FILE_EXTENSTION = "mock_extension"
        mock_os_system.return_value = 1

        with self.assertRaises(ValueError):
            IFService.run_command_in_shell(mock_service, file_id=0)

        npx_if_run_cmd = "npx if-run --manifest "
        output_flag = " --output "
        expected_cmd = (
            f'npx if-run --manifest "{mock_service.INFILE_PATH}{0}{mock_service.FILE_EXTENSION}" '
            f'--output "{mock_service.OUTFILE_PATH}{0}{mock_service.FILE_EXTENSION}"'
        )

        mock_logging_error.assert_called_once_with(
            "%s: %s", "Impact Framework command failed with exit code 1", expected_cmd
        )

        mock_os_system.assert_called_once_with(expected_cmd)

    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.IFService.fill_parser_data"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.IFService.write_if_input",
        autospec=True,
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.IFService.run_command_in_shell",
        autospec=True,
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.time.time",
        autospec=True,
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.logger"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.read_file",
        autospec=True,
    )
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_run_if(
        self,
        mock_read_file,
        mock_logging,
        mock_time,
        mock_run_command_in_shell,
        mock_write_if_input,
        mock_fill_parser_data,
    ):
        """
        Test that run_if generates the IF input, runs the command, and logs the time taken.
        """
        mock_time.side_effect = cycle([0, 1])
        mock_read_file.side_effect = [
            Template("template_content"),  # Mock return for template.yaml
            {"pipeline_key": "pipeline_value"},  # Mock return for pipeline.yaml
        ]
        compute_resources = [MagicMock(spec=ComputeResource)]
        service = IFService()
        service.template = MagicMock()

        mock_data = {"aggregation_type": "aggregation", "duration": "duration"}
        service.data = mock_data

        service.run_if(compute_resources)

        mock_fill_parser_data.assert_called_once_with(mock_data, compute_resources)
        mock_write_if_input.assert_called_once()
        mock_run_command_in_shell.assert_called_once()
        mock_logging.info.assert_any_call(
            "Generating Impact Framework input file id %d for %d resources...", 0, 1
        )
        mock_logging.info.assert_any_call(
            "Impact Framework input %d generated in %d seconds.", 0, 1
        )
        mock_logging.info.assert_any_call(
            "Impact Framework completed the CO2 computation for file %d in %d seconds.",
            0,
            1,
        )

    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.SciEPue"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.SciM"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.ECpu"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.TeadsCurve"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.SciMcpu"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.SciO"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.EMem"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.ENet"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.Sci"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.SciE"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.PMem"
    )
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_get_models_info(
        self,
        mock_p_mem,
        mock_sci_e,
        mock_sci,
        mock_enet,
        mock_emem,
        mock_scio,
        mock_scimcpu,
        mock_teads_curve,
        mock_e_cpu,
        mock_sci_m,
        mock_sci_e_pue,
    ):
        """
        Test that get_models_info correctly populates the hardware_models dictionary.
        """
        mock_teads_curve.return_value.__dict__ = {"key": "value_teads_curve"}
        mock_scimcpu.return_value.__dict__ = {"key": "value_scimcpu"}
        mock_scio.return_value.__dict__ = {"key": "value_scio"}
        mock_emem.return_value.__dict__ = {"key": "value_emem"}
        mock_enet.return_value.__dict__ = {"key": "value_enet"}
        mock_sci.return_value.__dict__ = {"key": "value_sci"}
        mock_sci_e.return_value.__dict__ = {"key": "value_sci_e"}
        mock_p_mem.return_value.__dict__ = {"key": "value_p_mem"}
        mock_e_cpu.return_value.__dict__ = {"key": "value_e_cpu"}
        mock_sci_m.return_value.__dict__ = {"key": "value_sci_m"}
        mock_sci_e_pue.return_value.__dict__ = {"key": "value_sci_e_pue"}

        mock_data = {
            "hardware_models": {
                "teads-curve": {},
                "sci-m-cpu": {},
                "sci-o": {},
                "e-mem": {},
                "e-net": {},
                "sci": {},
                "sci-e": {},
                "p-mem": {},
                "e-cpu": {},
                "sci-m": {},
                "sci-e-pue": {},
            }
        }

        IFService.get_models_info(mock_data, provider="")

        self.assertEqual(
            mock_data["hardware_models"]["teads-curve"],
            {"key": "value_teads_curve"},
        )
        self.assertEqual(
            mock_data["hardware_models"]["sci-m-cpu"], {"key": "value_scimcpu"}
        )
        self.assertEqual(mock_data["hardware_models"]["sci-o"], {"key": "value_scio"})
        self.assertEqual(mock_data["hardware_models"]["e-mem"], {"key": "value_emem"})
        self.assertEqual(mock_data["hardware_models"]["e-net"], {"key": "value_enet"})
        self.assertEqual(mock_data["hardware_models"]["sci"], {"key": "value_sci"})
        self.assertEqual(mock_data["hardware_models"]["sci-e"], {"key": "value_sci_e"})
        self.assertEqual(mock_data["hardware_models"]["p-mem"], {"key": "value_p_mem"})
        self.assertEqual(mock_data["hardware_models"]["e-cpu"], {"key": "value_e_cpu"})
        self.assertEqual(mock_data["hardware_models"]["sci-m"], {"key": "value_sci_m"})
        self.assertEqual(
            mock_data["hardware_models"]["sci-e-pue"],
            {"key": "value_sci_e_pue"},
        )

    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.SciEPue"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.SciO"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.TeadsCurve"
    )
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_get_resource_inputs_with_default_models(
        self, mock_teads_curve, mock_sci_o, mock_sci_e_pue
    ):
        """
        Test get_resource_inputs with default models (TeadsCurve, SciO, SciEPue) only.
        """
        mock_teads_curve.fill_inputs.side_effect = lambda compute_unit, time_index: {
            "timestamp": compute_unit.time_points[time_index],
            "teads_cpu_util": compute_unit.cpu_util[time_index] + 50,
        }
        mock_sci_o.fill_inputs.side_effect = lambda compute_unit, time_index: {
            "sci_o_carbon_intensity": f"carbon_intensity_{time_index}"
        }
        mock_sci_e_pue.fill_inputs.side_effect = lambda compute_unit, time_index: {
            "sci_e_pue": f"pue_{time_index}"
        }

        mock_compute_resource = MagicMock(spec=ComputeResource)
        mock_compute_resource.time_points = [0, 1, 2]
        mock_compute_resource.cpu_util = [50, 60, 70]
        mock_compute_resource.carbon_intensity = 10.0
        mock_compute_resource.duration_seconds = [120, 240, 360]

        resource_inputs = IFService.get_resource_inputs(mock_compute_resource)

        expected_inputs = [
            {
                "timestamp": 0,
                "teads_cpu_util": 100,
                "sci_o_carbon_intensity": "carbon_intensity_0",
                "sci_e_pue": "pue_0",
                "duration": 120,
                "duration/seconds": 120,
            },
            {
                "timestamp": 1,
                "teads_cpu_util": 110,
                "sci_o_carbon_intensity": "carbon_intensity_1",
                "sci_e_pue": "pue_1",
                "duration": 240,
                "duration/seconds": 240,
            },
            {
                "timestamp": 2,
                "teads_cpu_util": 120,
                "sci_o_carbon_intensity": "carbon_intensity_2",
                "sci_e_pue": "pue_2",
                "duration": 360,
                "duration/seconds": 360,
            },
        ]

        self.assertEqual(resource_inputs, expected_inputs)
        self.assertEqual(
            mock_teads_curve.fill_inputs.call_count,
            len(mock_compute_resource.time_points),
        )
        self.assertEqual(
            mock_sci_o.fill_inputs.call_count, len(mock_compute_resource.time_points)
        )
        self.assertEqual(
            mock_sci_e_pue.fill_inputs.call_count,
            len(mock_compute_resource.time_points),
        )

    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.SciEPue"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.SciO"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.TeadsCurve"
    )
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_get_resource_inputs_with_additional_models(
        self, mock_teads_curve, mock_sci_o, mock_sci_e_pue
    ):
        """
        Test get_resource_inputs with additional models passed in.
        """
        mock_teads_curve.fill_inputs.side_effect = lambda compute_unit, time_index: {
            "teads_cpu_util": f"cpu_util_{time_index}"
        }
        mock_sci_o.fill_inputs.side_effect = lambda compute_unit, time_index: {
            "sci_o_carbon_intensity": f"carbon_intensity_{time_index}"
        }
        mock_sci_e_pue.fill_inputs.side_effect = lambda compute_unit, time_index: {
            "sci_e_pue": f"pue_{time_index}"
        }
        mock_additional_model = MagicMock(spec=ModelUtilities)
        mock_additional_model.fill_inputs.side_effect = (
            lambda compute_unit, time_index: {
                "additional_model_input": f"additional_input_{time_index}"
            }
        )

        mock_compute_resource = MagicMock(spec=ComputeResource)
        mock_compute_resource.time_points = [0, 1]
        mock_compute_resource.duration_seconds = [DAILY_SECONDS, DAILY_SECONDS]

        resource_inputs = IFService.get_resource_inputs(
            mock_compute_resource, models=(mock_additional_model,)
        )

        expected_inputs = [
            {
                "teads_cpu_util": "cpu_util_0",
                "sci_o_carbon_intensity": "carbon_intensity_0",
                "additional_model_input": "additional_input_0",
                "sci_e_pue": "pue_0",
                "duration": DAILY_SECONDS,
                "duration/seconds": DAILY_SECONDS,
            },
            {
                "teads_cpu_util": "cpu_util_1",
                "sci_o_carbon_intensity": "carbon_intensity_1",
                "additional_model_input": "additional_input_1",
                "sci_e_pue": "pue_1",
                "duration": DAILY_SECONDS,
                "duration/seconds": DAILY_SECONDS,
            },
        ]

        self.assertEqual(resource_inputs, expected_inputs)
        self.assertEqual(
            mock_teads_curve.fill_inputs.call_count,
            len(mock_compute_resource.time_points),
        )
        self.assertEqual(
            mock_sci_o.fill_inputs.call_count, len(mock_compute_resource.time_points)
        )
        self.assertEqual(
            mock_additional_model.fill_inputs.call_count,
            len(mock_compute_resource.time_points),
        )
        self.assertEqual(
            mock_sci_e_pue.fill_inputs.call_count,
            len(mock_compute_resource.time_points),
        )

    @patch.object(IFService, "get_resource_inputs")
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_get_resource_data(self, mock_get_resource_inputs):
        """
        Test that get_resource_data correctly maps compute_units to their inputs.
        """
        mock_compute_unit_1 = MagicMock()
        mock_compute_unit_1.id = "compute_unit_1"
        mock_compute_unit_2 = MagicMock()
        mock_compute_unit_2.id = "compute_unit_2"

        compute_units = [mock_compute_unit_1, mock_compute_unit_2]

        mock_get_resource_inputs.side_effect = [
            {"mock_key_1": "mock_value_1"},
            {"mock_key_2": "mock_value_2"},
        ]

        mock_service = MagicMock(spec=IFService)
        mock_service.get_resource_inputs = mock_get_resource_inputs
        data = {}
        IFService.get_resource_data(mock_service, data, compute_units)

        expected_result = {
            "compute_unit_1": {"mock_key_1": "mock_value_1"},
            "compute_unit_2": {"mock_key_2": "mock_value_2"},
        }
        self.assertIn("resources", data)
        self.assertEqual(data["resources"], expected_result)
        self.assertEqual(mock_get_resource_inputs.call_count, 2)

    @patch.object(IFService, "get_resource_data")
    @patch.object(IFService, "get_models_info")
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_fill_parser_data(self, mock_get_models_info, mock_get_resource_data):
        """
        Test fill_parser data
        """
        mock_service = IFService()
        mock_data = {}

        mock_get_models_info.side_effect = lambda data, provider="azure": data.update(
            {"hardware_models": {}}
        )
        mock_get_resource_data.side_effect = (
            lambda data, compute_resources: data.update({"resources": {}})
        )
        mock_service.fill_parser_data(mock_data, [])

        self.assertIn("resources", mock_data)
        self.assertIn("hardware_models", mock_data)

    def test_get_measurement_from_output(self):
        """
        Test that get_measurements_from_output correctly extracts and organizes measurements.
        """
        mock_if_output = {
            "vm1": {
                "aggregated": {"carbon": 25, "energy": 10},
                "outputs": [
                    {"carbon": 10, "energy": 3, "timestamp": 1},
                    {"carbon": 15, "energy": 7, "timestamp": 2},
                ],
            }
        }

        mock_compute_resource = ComputeResource(id="vm1")
        result = IFService.get_measurements_from_output(
            mock_if_output, mock_compute_resource.id
        )

        self.assertEqual(result["carbon"]["aggregated"], 25)
        self.assertEqual(result["carbon"]["observations"], [10, 15])
        self.assertEqual(result["energy"]["observations"], [3, 7])
        self.assertEqual(result["energy"]["aggregated"], 10)

    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.IFService.aggregate_app_level"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.read_file"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.logger.info"
    )
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_parse_if_output_success_at_app_level(
        self, mock_logging_info, mock_read_file, mock_aggregate_app_level
    ):
        """
        Test that parse_if_output correctly processes the YAML output and populates compute resources at app level.
        """
        mock_read_file.return_value = {
            "execution": {"status": "success"},
            "tree": {
                "children": {
                    "vm1": {
                        "outputs": [
                            {"carbon": 10, "timestamp": 1},
                            {"carbon": 15, "timestamp": 2},
                        ],
                        "aggregated": {"carbon": 25},
                    }
                }
            },
        }
        mock_service = MagicMock(spec=IFService)
        mock_service.OUTFILE_PATH = "mock_outfile_path"
        mock_compute_resource = [MagicMock(id="vm1", time_points=[1, 2])]
        mock_aggregate_app_level.return_value = [MagicMock(spec=ComputeResource)]

        result = IFService.parse_if_output(
            mock_service, mock_compute_resource, emission_breakdown_at_pod_level=False
        )

        assert isinstance(result, list)
        mock_aggregate_app_level.assert_called_once_with(
            mock_compute_resource,
            {
                "vm1": {
                    "outputs": [
                        {"carbon": 10, "timestamp": 1},
                        {"carbon": 15, "timestamp": 2},
                    ],
                    "aggregated": {"carbon": 25},
                }
            },
            0,
        )
        mock_logging_info.assert_any_call(
            "Output parsing completed in %d seconds for file %d", 0, 0
        )

    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.IFService.aggregate_pod_level"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.read_file"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.logger.info"
    )
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_parse_if_output_success_at_pod_level(
        self, mock_logging_info, mock_read_file, mock_aggregate_pod_level
    ):
        """
        Test that parse_if_output correctly processes the YAML output and populates compute resources at pod level.
        """
        mock_read_file.return_value = {
            "execution": {"status": "success"},
            "tree": {
                "children": {
                    "vm1": {
                        "outputs": [
                            {"carbon": 10, "timestamp": 1},
                            {"carbon": 15, "timestamp": 2},
                        ],
                        "aggregated": {"carbon": 25},
                    }
                }
            },
        }
        mock_service = MagicMock(spec=IFService)
        mock_service.OUTFILE_PATH = "mock_outfile_path"
        mock_compute_resource = [MagicMock(id="vm1", time_points=[1, 2])]
        mock_aggregate_pod_level.return_value = {
            "paas": {"app": {"namespace": [MagicMock(spec=Pod)]}}
        }

        result = IFService.parse_if_output(
            mock_service, mock_compute_resource, emission_breakdown_at_pod_level=True
        )

        assert isinstance(result, dict)
        mock_aggregate_pod_level.assert_called_once_with(
            mock_compute_resource,
            {
                "vm1": {
                    "outputs": [
                        {"carbon": 10, "timestamp": 1},
                        {"carbon": 15, "timestamp": 2},
                    ],
                    "aggregated": {"carbon": 25},
                }
            },
        )
        mock_logging_info.assert_any_call(
            "Output parsing completed in %d seconds for file %d", 0, 0
        )

    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.read_file"
    )
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.logger.error"
    )
    def test_parse_if_output_carmen_exception(self, mock_logging_error, mock_read_file):
        """
        Test for parse_if_output raises CarmenException when the execution status is failed.
        """
        mock_read_file.return_value = {
            "execution": {"status": "failure"},
        }

        mock_service = MagicMock(spec=IFService)
        mock_service.OUTFILE_PATH = "mock_outfile_path"

        mock_compute_resources = [
            MagicMock(
                id="vm1", time_points=[], carbon_emitted=[], total_carbon_emitted=0
            )
        ]
        mock_service.parse_if_output(mock_compute_resources)

        with self.assertRaises(CarmenException):
            IFService.parse_if_output(
                mock_service,
                mock_compute_resources,
                emission_breakdown_at_pod_level=False,
            )

        mock_logging_error.assert_called_once_with(
            "IF has failed to calculate the carbon impact for file ID 0."
        )

    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.logger.info"
    )
    @patch.object(IFService, "get_measurements_from_output")
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_aggregate_app_level(
        self, mock_get_measurements_from_output, mock_logging_info
    ):
        """
        Test that aggregate_app_level correctly aggregates the application metrics.
        """
        mock_get_measurements_from_output.return_value = {
            "timestamp": {"observations": [1, 2]},
            "carbon": {"aggregated": 25, "observations": [10, 15]},
            "energy": {"aggregated": 10, "observations": [3, 7]},
        }
        mock_compute_resource = [MagicMock(id="vm1", time_points=[1, 2])]
        mock_if_output = {
            "vm1": {
                "outputs": [
                    {"carbon": 10, "timestamp": 1},
                    {"carbon": 15, "timestamp": 2},
                ],
                "aggregated": {"carbon": 25},
            }
        }

        result = IFService.aggregate_app_level(mock_compute_resource, mock_if_output, 0)

        mock_get_measurements_from_output.assert_called_once_with(
            {
                "vm1": {
                    "outputs": [
                        {"carbon": 10, "timestamp": 1},
                        {"carbon": 15, "timestamp": 2},
                    ],
                    "aggregated": {"carbon": 25},
                }
            },
            "vm1",
        )
        self.assertEqual(result[0].time_points, [1, 2])
        self.assertEqual(result[0].carbon_emitted, [10, 15])
        self.assertEqual(result[0].total_carbon_emitted, 25)
        self.assertEqual(result[0].energy_consumed, [3, 7])
        self.assertEqual(result[0].total_energy_consumed, 10)
        mock_logging_info.assert_called_once_with(
            "Parsing IF output for file number %s at application level", "0"
        )

    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.logger.info"
    )
    @patch.object(IFService, "get_measurements_from_output")
    @patch(
        "backend.src.services.carbon_service.impact_framework.service.if_service.IFService.initialize_output"
    )
    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_aggregate_pod_level(
        self,
        mock_initialize_output,
        mock_get_measurements_from_output,
        mock_logging_info,
    ):
        """
        Test that aggregate_pod_level correctly aggregates the pod metrics.
        """
        mock_initialize_output.return_value = {"paas1": {"app1": {"namespace1": []}}}
        mock_get_measurements_from_output.return_value = {
            "carbon": {"aggregated": 13.5082, "observations": [2.234, 2.232]},
            "carbon-embodied": {"aggregated": 6.5718, "observations": [1.0953, 1.0953]},
            "carbon-operational": {
                "aggregated": 6.9365,
                "observations": [1.1387, 1.1368],
            },
            "cpu/energy": {"aggregated": 0.006, "observations": [0.0009, 0.0009]},
            "cpu/power": {"aggregated": 0.012, "observations": [0.0019, 0.0018]},
            "energy": {"aggregated": 0.0276, "observations": [0.0045, 0.0045]},
            "timestamp": {"observations": [1, 2]},
        }
        mock_pod1 = Pod(
            id="pod1",
            app="app1",
            paas="paas1",
            namespace="namespace1",
            cpu_util=[0.0231278, 0.0233524],
        )
        mock_compute_resources = [MagicMock(id="vm1", name="app1", pods=[mock_pod1])]
        mock_if_output = {
            "vm1": {
                "children": {
                    "pod1": {
                        "aggregated": {
                            "carbon": 13.508241,
                            "carbon-embodied": 6.571754,
                        },
                        "outputs": [{"carbon": 2.233978, "carbon-embodied": 1.095292}],
                    }
                }
            }
        }

        result = IFService.aggregate_pod_level(mock_compute_resources, mock_if_output)

        mock_initialize_output.assert_called_once_with(mock_compute_resources)
        mock_logging_info.assert_called_once_with("Parsing IF output at pod level")
        mock_get_measurements_from_output.assert_called_once_with(
            {
                "pod1": {
                    "aggregated": {"carbon": 13.508241, "carbon-embodied": 6.571754},
                    "outputs": [{"carbon": 2.233978, "carbon-embodied": 1.095292}],
                }
            },
            "pod1",
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].carbon_emitted, [2.2340, 2.2320]
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].carbon_embodied, [1.0953, 1.0953]
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].carbon_operational,
            [1.1387, 1.1368],
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].cpu_energy, [0.0009, 0.0009]
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].cpu_power, [0.0019, 0.0018]
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].cpu_util, [0.0231, 0.0234]
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].energy_consumed, [0.0045, 0.0045]
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].total_carbon_emitted, 13.5082
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].total_carbon_embodied, 6.5718
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].total_carbon_operational, 6.9365
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].total_cpu_energy, 0.0060
        )
        self.assertEqual(
            result["paas1"]["app1"]["namespace1"][0].total_energy_consumed, 0.0276
        )

    @patch.object(IFService, "__init__", lambda self, *args, **kwargs: None)
    def test_initialize_output(
        self,
    ):
        """
        Test that initialize_output correctly initializes the output dictionary.
        """
        mock_pod1 = Pod(id="pod1", app="app1", paas="paas1", namespace="namespace1")
        mock_pod2 = Pod(id="pod2", app="app1", paas="paas1", namespace="namespace2")
        mock_pod3 = Pod(id="pod3", app="app1", paas="paas2", namespace="namespace3")
        mock_pod4 = Pod(id="pod4", app="app2", paas="paas1", namespace="namespace4")
        mock_compute_resources = [
            Application(id="0", name="app1", pods=[mock_pod1, mock_pod2, mock_pod3]),
            Application(id="1", name="app2", pods=[mock_pod4]),
        ]

        result_output = IFService.initialize_output(mock_compute_resources)

        self.assertEqual(
            result_output,
            {
                "paas1": {
                    "app1": {"namespace1": [], "namespace2": []},
                    "app2": {"namespace4": []},
                },
                "paas2": {"app1": {"namespace3": []}},
            },
        )
