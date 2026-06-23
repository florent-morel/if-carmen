from pathlib import Path

import pytest
from backend.tests.daemon.end_to_end._e2e_helpers import run_daemon, validate_storage_output


def test_e2e_storage_single_provider_azure():
    
    # -- Storage carbon/energy computation derivation -------------------------
    #
    #   Input data
    #   R1: ProductName="... P4 LRS Disk ...", StorageSizeGB=32, Duration=2678400 s
    #   R2: ProductName="... S20 GRS Disk ...", StorageSizeGB=512, Duration=2678400 s
    #   R3: ProductName="Unknown disk type", StorageSizeGB=128, Duration=3600 s
    #   R4: ProductName="Unknown disk type", StorageSizeGB=128, Duration not specified
    #
    #   Note: replication type is inferred from ProductName.
    #   For "Unknown disk type", no GRS/GZRS/LRS token is present, so replication defaults to LRS.
    #
    # Constants (from test_data modelling constants)
    #   region=westeurope -> Netherlands -> carbon_intensity=253 gCO2e/kWh
    #   storage_electricity_ratio(SSD)=1.200e-6 kWh/(GB*h)
    #   storage_electricity_ratio(Unknown)=9.250e-7 kWh/(GB*h)
    #   storage_embodied_coefficient(SSD)=160 gCO2e/GB
    #   storage_embodied_coefficient(Unknown)=90 gCO2e/GB
    #   replication factors: LRS=3, GRS=6
    #   expected_lifespan_seconds=126230400s (4 years)
    #   duration_hours(R1,R2)=2678400/3600=744 h
    #   duration_hours(R3,R4)=3600/3600=1 h
    #
    # Formula reminders
    #   effective_size_gb = storage_size_gb * replication_factor
    #   energy_kwh = effective_size_gb * storage_electricity_ratio * duration_hours
    #   operational_gco2e = energy_kwh * carbon_intensity
    #   embodied_gco2e = effective_size_gb * storage_embodied_coefficient
    #                    * (duration_seconds / expected_lifespan_seconds)
    #   total_gco2e = operational_gco2e + embodied_gco2e
    #
    # R1: LRS disk (P4) for 1 month
    #   effective_size_gb = 32 * 3 = 96
    #   energy_kwh = 96 * 1.200e-6 * 744 = 8.570e-2
    #   operational_gco2e = 8.570e-2 * 2.530e2 = 2.168e1
    #   embodied_gco2e = 96 * 160 * (2.6784e6 / 126230400)
    #                  = 3.259e2
    #   total_gco2e = 2.168e1 + 3.259e2 = 3.476e2
    #
    # R2: GRS disk (S20) for 1 month
    #   effective_size_gb = 512 * 6 = 3.072e3
    #   energy_kwh = 3.072e3 * 1.200e-6 * 744 = 2.743e0
    #   operational_gco2e = 2.743e0 * 2.530e2 = 6.939e2
    #   embodied_gco2e = 3.072e3 * 160 * (2.6784e6 / 126230400)
    #                  = 1.043e4
    #   total_gco2e = 6.939e2 + 1.043e4 = 1.112e4
    #
    # R3: Unknown-type disks (default to LRS) for 1 hour
    #   effective_size_gb = 128 * 3 = 3.840e2
    #   energy_kwh = 3.840e2 * 9.250e-7 * 1 = 3.552e-4
    #   operational_gco2e = 3.552e-4 * 2.530e2 = 8.986e-2
    #   embodied_gco2e = 3.840e2 * 90 * (3600 / 126230400)
    #                  = 9.856e-1
    #   total_gco2e = 8.986e-2 + 9.856e-1 = 1.075
    #
    # R4: Unknown-type disks (default to LRS) for an unspecified duration (default to 1 day)
    #   effective_size_gb = 128 * 3 = 3.840e2
    #   energy_kwh = 3.840e2 * 9.250e-7 * 24 = 8.525e-3
    #   operational_gco2e = 8.525e-3 * 2.530e2 = 2.157
    #   embodied_gco2e = 3.840e2 * 90 * (86400 / 126230400)
    #                  = 2.365e1
    #   total_gco2e = 2.157 + 23.65 = 25.807
    # ------------------------------------------------------------------------
    
    output_rows = run_daemon(Path(__file__))

    row_by_id = {row["Id"]: row for row in output_rows}
    
    assert len(output_rows) == 4
    expected_by_id = {
        # R1
        "/subscriptions/sub-test/providers/Microsoft.Compute/disks/disk-ssd-lrs": {
            "StorageType": "SSD",
            "ReplicationType": "LRS",
            "SizeGB": 32.0,
            "EnergyKWH": 0.0857,
            "OperationalCarbonGramsCO2eq": 21.6843,
            "EmbodiedCarbonGramsCO2eq": 325.9138,
            "TotalCarbonGramsCO2eq": 347.5981,
        },
        # R2
        "/subscriptions/sub-test/providers/Microsoft.Compute/disks/disk-ssd-grs": {
            "StorageType": "SSD",
            "ReplicationType": "GRS",
            "SizeGB": 512.0,
            "EnergyKWH": 2.7427,
            "OperationalCarbonGramsCO2eq": 693.8984,
            "EmbodiedCarbonGramsCO2eq": 10429.2402,
            "TotalCarbonGramsCO2eq": 11123.1387,
        },
        # R3
        "/subscriptions/sub-test/providers/Microsoft.Compute/disks/disk-ssd-gzrs": {
            "StorageType": "Unknown",
            "ReplicationType": "LRS",
            "SizeGB": 128.0,
            "EnergyKWH": 0.0004,
            "OperationalCarbonGramsCO2eq": 0.0899,
            "EmbodiedCarbonGramsCO2eq": 0.9856,
            "TotalCarbonGramsCO2eq": 1.0755,
        },
        # R4
        "/subscriptions/sub-test/providers/Microsoft.Compute/disks/disk-ssd-ra_gzrs": {
            "StorageType": "Unknown",
            "ReplicationType": "LRS",
            "SizeGB": 128.0,
            "EnergyKWH": 0.0085,
            "OperationalCarbonGramsCO2eq": 2.157,
            "EmbodiedCarbonGramsCO2eq": 23.65,
            "TotalCarbonGramsCO2eq": 25.807,
        },
    }
    
    validate_storage_output(row_by_id, expected_by_id)