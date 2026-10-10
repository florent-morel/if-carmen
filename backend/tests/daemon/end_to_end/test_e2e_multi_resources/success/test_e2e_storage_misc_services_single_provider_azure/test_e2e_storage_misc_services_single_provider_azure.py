from pathlib import Path

import pytest

from backend.src.schemas.resource import ResourceType
from backend.tests.daemon.end_to_end._e2e_helpers import run_daemon, validate_output


def test_e2e_storage_misc_services_single_provider_azure(tmp_path):

    # ── Miscellaneous services computation derivation ─────────────────────────────────
    #
    # Storage computation is validated in test_e2e_storage_single_provider_azure
    # Miscellaneous services computation is validated here, based on the storage computation result.
    #
    #   Input data
    #   R1: ResourceName="... P4 LRS Disk ...", StorageSizeGB=32, Duration=2678400 s
    #   R2: ResourceName="... S20 GRS Disk ...", StorageSizeGB=512, Duration=2678400 s
    #   R3: ResourceName="Unknown disk type", StorageSizeGB=128, Duration=3600 s
    #   R4: ResourceName="Unknown disk type", StorageSizeGB=128, Duration not specified
    #
    #   Note: replication type is inferred from ResourceName.
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
    #   Ratios use full IF storage totals; the CSV writer rounds final metrics
    #   to 4 decimals, including total carbon from unrounded components.
    #   compute_energy = 0.15  # kWh (default value)
    #   storage_energy = 2.922979  # kWh
    #   compute_cost = 1  # $
    #   storage_cost = 500  # $
    #   compute_embodied = 15.0  # gCO2e (default value)
    #   storage_embodied = 11105.708419  # gCO2e
    # Formula reminders
    #   energy_ratio_kwh_per_dollar = 0.75 * (compute_energy / compute_cost)
    #                                  + 0.25 * (storage_energy / storage_cost)
    #                                = 0.113961 kWh/$
    #   embodied_ratio_gco2e_per_dollar = 0.75 * (compute_embodied / compute_cost)
    #                                     + 0.25 * (storage_embodied / storage_cost)
    #                                   = 16.802854 gCO2e/$
    #
    #   operational_gco2e (for a given resource) =  (cost * carbon_intensity_per_region) * energy_ratio_kwh_per_dollar
    #
    #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
    #
    #   total_gco2e = operational_gco2e + embodied_gco2e
    #
    # ------------------------------------------------------------------------

    run = run_daemon(Path(__file__), tmp_path)
    run.validate_if_inputs(
        "storage",
        expected_inputs_by_id={
            "Test_ID_Storage_01": {"storage/requested": 96.0},
            "Test_ID_Storage_02": {"storage/requested": 3072.0},
            "Test_ID_Storage_03": {"storage/embodied-coefficient": 90.0},
            "Test_ID_Storage_04": {"duration/seconds": 86400.0},
            "Test_ID_Storage_05": {"storage/requested": 96.0},
        },
    )
    run.validate_if_inputs(
        "misc_services",
        expected_common_inputs={
            "energy-cost-ratio": 0.113961,
            "embodied-cost-ratio": 16.802854,
        },
        expected_inputs_by_id={
            "Test_ID_Misc_Services_01": {"cost": 120.5},
            "Test_ID_Misc_Services_02": {"cost": 85.0},
            "Test_ID_Misc_Services_03": {"cost": 210.75},
        },
    )

    output_rows = run.rows
    row_by_id = {row["Id"]: row for row in output_rows}

    # 1 VM + 3 Storage resources
    assert len(output_rows) == 8

    expected_by_id = {
        # R1 -- Values are the same as the e2e test for storage single resource
        "Test_ID_Storage_01": {
            "ResourceType": ResourceType.STORAGE.value,
            "Provider": "azure",
            "Region": "westeurope",
            "StorageType": "SSD",
            "ReplicationType": "LRS",
            "SizeGB": 32.0,
            "EnergyKWH": 0.0857,
            "OperationalCarbonGramsCO2eq": 21.6843,
            "EmbodiedCarbonGramsCO2eq": 325.9138,
            "TotalCarbonGramsCO2eq": 347.5981,
            "CarbonIntensity": 253,
        },
        # R2 -- Values are the same as the e2e test for storage single resource
        "Test_ID_Storage_02": {
            "ResourceType": ResourceType.STORAGE.value,
            "Provider": "azure",
            "Region": "westeurope",
            "StorageType": "SSD",
            "ReplicationType": "GRS",
            "SizeGB": 512.0,
            "EnergyKWH": 2.7427,
            "OperationalCarbonGramsCO2eq": 693.8984,
            "EmbodiedCarbonGramsCO2eq": 10429.2402,
            "TotalCarbonGramsCO2eq": 11123.1387,
            "CarbonIntensity": 253,
        },
        # R3 -- Values are the same as the e2e test for storage single resource
        "Test_ID_Storage_03": {
            "ResourceType": ResourceType.STORAGE.value,
            "Provider": "azure",
            "Region": "westeurope",
            "StorageType": "Unknown",
            "ReplicationType": "LRS",
            "SizeGB": 128.0,
            "EnergyKWH": 0.0004,
            "OperationalCarbonGramsCO2eq": 0.0899,
            "EmbodiedCarbonGramsCO2eq": 0.9856,
            "TotalCarbonGramsCO2eq": 1.0755,
            "CarbonIntensity": 253,
        },
        # R4 -- Values are the same as the e2e test for storage single resource
        "Test_ID_Storage_04": {
            "ResourceType": ResourceType.STORAGE.value,
            "Provider": "azure",
            "Region": "westeurope",
            "StorageType": "Unknown",
            "ReplicationType": "LRS",
            "SizeGB": 128.0,
            "EnergyKWH": 0.0085,
            "OperationalCarbonGramsCO2eq": 2.157,
            "EmbodiedCarbonGramsCO2eq": 23.65,
            "TotalCarbonGramsCO2eq": 25.807,
            "CarbonIntensity": 253,
        },
        # R5 -- Values are the same as the e2e test for storage single resource
        "Test_ID_Storage_05": {
            "ResourceType": ResourceType.STORAGE.value,
            "Provider": "azure",
            "Region": "francecentral",
            "StorageType": "SSD",
            "ReplicationType": "LRS",
            "SizeGB": 32.0,
            "EnergyKWH": 0.0857,
            "OperationalCarbonGramsCO2eq": 3.7712,
            "EmbodiedCarbonGramsCO2eq": 325.9138,
            "TotalCarbonGramsCO2eq": 329.685,
            "CarbonIntensity": 44,
        },
        # R6
        #   Energy KWH = cost * energy_ratio_kwh_per_dollar
        #              = 120.5 * energy_ratio = 13.732359
        #
        #   operational_gco2e = energy * 253 = 3474.286953
        #
        #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
        #                  = 120.5 * embodied_ratio = 2024.743932
        #
        #   report: energy=13.7324, operational=3474.2870, embodied=2024.7439
        #           total=5499.0309 (rounded from unrounded component sum)
        "Test_ID_Misc_Services_01": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "westeurope",
            "EnergyKWH": 13.7324,
                "OperationalCarbonGramsCO2eq": 3474.287,
            "EmbodiedCarbonGramsCO2eq": 2024.7439,
                "TotalCarbonGramsCO2eq": 5499.0309,
                "CarbonIntensity": 253,
            },
        # R7
        #   Energy KWH = cost * energy_ratio_kwh_per_dollar
        #              = 85 * energy_ratio = 9.686727
        #
        #   operational_gco2e = energy * 253 = 2450.741834
        #
        #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
        #                  = 85 * embodied_ratio = 1428.242608
        #
        #   report: energy=9.6867, operational=2450.7418, embodied=1428.2426
        #           total=3878.9844 (rounded from unrounded component sum)
        "Test_ID_Misc_Services_02": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "westeurope",
            "EnergyKWH": 9.6867,
                "OperationalCarbonGramsCO2eq": 2450.7418,
            "EmbodiedCarbonGramsCO2eq": 1428.2426,
                "TotalCarbonGramsCO2eq": 3878.9844,
                "CarbonIntensity": 253,
            },
        # R8
        #   Energy KWH = cost * energy_ratio_kwh_per_dollar
        #              = 210.75 * energy_ratio = 24.017384
        #
        #   operational_gco2e = energy * 280 = 6724.867501
        #
        #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
        #                  = 210.75 * embodied_ratio = 3541.201525
        #
        #   report: energy=24.0174, operational=6724.8675, embodied=3541.2015
        #           total=10266.0690 (rounded from unrounded component sum)
        "Test_ID_Misc_Services_03": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "northeurope",
            "EnergyKWH": 24.0174,
                "OperationalCarbonGramsCO2eq": 6724.8675,
            "EmbodiedCarbonGramsCO2eq": 3541.2015,
                "TotalCarbonGramsCO2eq": 10266.069,
                "CarbonIntensity": 280,
            }
    }

    validate_output(row_by_id, expected_by_id)

    for resource_id, expected in expected_by_id.items():
        if expected["ResourceType"] == ResourceType.MISC_SERVICES.value:
            for metric in (
                "EnergyKWH",
                "OperationalCarbonGramsCO2eq",
                "EmbodiedCarbonGramsCO2eq",
                "TotalCarbonGramsCO2eq",
            ):
                assert float(row_by_id[resource_id][metric]) == expected[metric], (
                    resource_id,
                    metric,
                )
