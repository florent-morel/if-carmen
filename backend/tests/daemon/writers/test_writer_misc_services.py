"""
Unit tests for Writer_Misc_Services.
"""
import csv
import io
import unittest
from unittest.mock import MagicMock

from backend.src.core.settings import ReportConfig
from backend.src.daemon.writers.writer_misc_services import Writer_Misc_Services
from backend.src.schemas.misc_services_resource import MiscServicesResource
from backend.src.schemas.resource import ResourceType


class TestWriterMiscServices(unittest.TestCase):
    """Unit tests for Writer_Misc_Services.write_content."""

    def setUp(self):
        self.misc_services_resources = [
            MiscServicesResource(
                id="misc_service1",
                name="name1",
                region="eastus",
                subscription="sub1",
                carbon_intensity=100.0,
                misc_services_cost=50.0,
            ),
            MiscServicesResource(
                id="misc_service2",
                name="name2",
                region="westus",
                subscription="sub2",
                carbon_intensity=150.0,
                misc_services_cost=75.0,
            ),
        ]

    def _make_writer(self, resources):
        """Build a Writer_Misc_Services backed by an in-memory CSV buffer."""
        buf = io.StringIO()
        fieldnames = Writer_Misc_Services.get_report_headers()
        dict_writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        dict_writer.writeheader()

        mock_result = MagicMock()
        mock_result.list_processed_resources = resources
        writer = Writer_Misc_Services(
            config=MagicMock(),
            date="2025-06-01",
            writer=dict_writer,
            resource_result=mock_result,
        )
        return writer, buf

    def test_writes_one_row_per_resource(self):
        """write_content emits exactly one CSV row per misc-services resource."""
        writer, buf = self._make_writer(self.misc_services_resources)
        writer.write_content(self.misc_services_resources)

        buf.seek(0)
        rows = list(csv.DictReader(buf))
        self.assertEqual(len(rows), len(self.misc_services_resources))

    def test_row_content(self):
        """write_content writes ResourceType, Id, and ServicesCost correctly."""
        writer, buf = self._make_writer(self.misc_services_resources)
        writer.write_content(self.misc_services_resources)

        buf.seek(0)
        rows = list(csv.DictReader(buf))

        first = rows[0]
        self.assertEqual(first[ReportConfig.COMMON_RESOURCE_TYPE], ResourceType.MISC_SERVICES.value)
        self.assertEqual(first[ReportConfig.COMMON_ID], "misc_service1")
        self.assertEqual(float(first[ReportConfig.MISC_SERVICES_COST]), 50.0)

        second = rows[1]
        self.assertEqual(second[ReportConfig.COMMON_ID], "misc_service2")
        self.assertEqual(float(second[ReportConfig.MISC_SERVICES_COST]), 75.0)
