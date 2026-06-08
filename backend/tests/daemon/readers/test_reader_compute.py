"""
Unit tests for the Compute Reader class in the daemon.readers module.
"""

import unittest
from collections import Counter
from unittest.mock import MagicMock

from backend.src.common.constants import (
    SOURCE_RESOURCE_ID,
    SOURCE_REGION,
    SOURCE_PROVIDER,
    SOURCE_AVG_CPU_PERCENTAGE,
    SOURCE_TIME,
    SOURCE_DISK_SIZE_GB,
    SOURCE_METER_CATEGORY,
    SOURCE_COST,
    SOURCE_PRODUCT_NAME,
    SOURCE_METER_NAME,
    SOURCE_QUANTITY,
    SOURCE_UNIT_OF_MEASURE,
    SOURCE_DATE,
    SOURCE_RESOURCE_GROUP,
    SOURCE_SUBSCRIPTION_ID,
)
from backend.src.daemon.readers.reader_compute import Reader_Compute

import logging

logger = logging.getLogger(__name__)

# Minimal CSV header matching all fields consumed by Reader_Compute
_HEADERS = ",".join([
    SOURCE_DATE,
    SOURCE_TIME,
    SOURCE_RESOURCE_ID,
    SOURCE_AVG_CPU_PERCENTAGE,
    SOURCE_REGION,
    "Subscription",
    SOURCE_SUBSCRIPTION_ID,
    SOURCE_RESOURCE_GROUP,
    "Name",
    "Size",
    "Service",
    "Instance",
    "Component",
    "Environment",
    "Partition",
    SOURCE_PROVIDER,
    SOURCE_DISK_SIZE_GB,
    "NbVCpus",
    SOURCE_COST,
    SOURCE_METER_CATEGORY,
    SOURCE_METER_NAME,
    SOURCE_PRODUCT_NAME,
    SOURCE_QUANTITY,
    SOURCE_UNIT_OF_MEASURE,
    "BillingPeriodStartDate",
    "BillingPeriodEndDate",
    "ConsumedService",
])

def _make_row(resource_id: str, provider: str = "azure", region: str = "eastus") -> str:
    return (
        f"05/01/2024,2024-05-01T00:00:00Z,{resource_id},20,{region},"
        f"sub-test,sub-id,rg-test,vm-name,Standard_A1_v2,compute,inst,comp,test,part,"
        f"{provider},128,2,100.0,Compute,Standard VM,Virtual Machine,1,1/Hour,"
        f"05/01/2024,05/31/2024,compute"
    )


class TestReaderComputeDictLogInfo(unittest.TestCase):
    """Tests verifying dict_log_info counters populated by Reader_Compute."""

    def setUp(self):
        self.mock_config = MagicMock()
        self.reader = Reader_Compute(self.mock_config)
        self.reader.known_regions = {"eastus", "westeurope"}
        self.reader.unknown_regions = Counter()
        self.reader.unknown_providers = Counter()

    def _csv(self, *rows: str) -> str:
        return "\n".join([_HEADERS] + list(rows))

    def test_single_vm_single_row(self):
        """One unique VM, one row — new_vm_rows=1, duplicate_rows=0."""
        csv_data = self._csv(_make_row("vm-1"))
        self.reader.read(csv_data)

        self.assertEqual(self.reader.dict_log_info["total_rows"], 1)
        self.assertEqual(self.reader.dict_log_info["new_vm_rows"], 1)
        self.assertEqual(self.reader.dict_log_info["duplicate_rows"], 0)
        self.assertEqual(self.reader.dict_log_info["skipped_rows"], 0)
        self.assertEqual(self.reader.dict_log_info["excluded_rows"], 0)

    def test_single_vm_multiple_time_series_rows(self):
        """Same VM appearing in 3 rows (time-series) — new_vm_rows=1, duplicate_rows=2."""
        csv_data = self._csv(
            _make_row("vm-1"),
            _make_row("vm-1"),
            _make_row("vm-1"),
        )
        self.reader.read(csv_data)

        self.assertEqual(self.reader.dict_log_info["total_rows"], 3)
        self.assertEqual(self.reader.dict_log_info["new_vm_rows"], 1)
        self.assertEqual(self.reader.dict_log_info["duplicate_rows"], 2)
        self.assertEqual(self.reader.dict_log_info["skipped_rows"], 0)
        self.assertEqual(self.reader.dict_log_info["excluded_rows"], 0)

    def test_multiple_unique_vms(self):
        """Three distinct VMs — new_vm_rows=3, duplicate_rows=0."""
        csv_data = self._csv(
            _make_row("vm-1"),
            _make_row("vm-2"),
            _make_row("vm-3"),
        )
        self.reader.read(csv_data)

        self.assertEqual(self.reader.dict_log_info["total_rows"], 3)
        self.assertEqual(self.reader.dict_log_info["new_vm_rows"], 3)
        self.assertEqual(self.reader.dict_log_info["duplicate_rows"], 0)
        self.assertEqual(self.reader.dict_log_info["skipped_rows"], 0)
        self.assertEqual(self.reader.dict_log_info["excluded_rows"], 0)

    def test_mix_unique_and_duplicate_rows(self):
        """Two VMs, one appears twice — new_vm_rows=2, duplicate_rows=1."""
        csv_data = self._csv(
            _make_row("vm-1"),
            _make_row("vm-2"),
            _make_row("vm-1"),
        )
        self.reader.read(csv_data)

        self.assertEqual(self.reader.dict_log_info["total_rows"], 3)
        self.assertEqual(self.reader.dict_log_info["new_vm_rows"], 2)
        self.assertEqual(self.reader.dict_log_info["duplicate_rows"], 1)
        self.assertEqual(self.reader.dict_log_info["skipped_rows"], 0)
        self.assertEqual(self.reader.dict_log_info["excluded_rows"], 0)

    def test_empty_csv_no_counters_set(self):
        """Header-only CSV — process_csv_data returns early, dict_log_info stays empty."""
        csv_data = _HEADERS  # no data rows
        self.reader.read(csv_data)

        # dict_log_info should not have been populated
        self.assertNotIn("total_rows", self.reader.dict_log_info)


if __name__ == "__main__":
    unittest.main()
