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
    #   Ratios and intermediate products use full precision; displayed results are rounded to 4 decimals.
    # Formula reminders
    #   energy_ratio_kwh_per_dollar = 0.75 * (compute_energy / compute_cost)
    #                                  + 0.25 * (storage_energy / storage_cost)
    #                                = 0.75 * (0.15 / 1) -- default value cf (config/modelling_constants/carbon_values.yaml)
    #                                + 0.25 * ((0.0857+2.7427+0.0004+0.0085+0.0857) / 500.0)
    #                                = 0.1125
    #                                + 0.25 * (2.923 / 500.0)
    #                                = 0.1125 + 0.0014615
    #                                = 0.1139615
    #                                ≈ 0.114 kWh/$
    #   embodied_ratio_gco2e_per_dollar = 0.75 * (compute_embodied / compute_cost)
    #                                     + 0.25 * (storage_embodied / storage_cost)
    #                                   = 0.75 * (15.0 / 1) -- default value cf (config/modelling_constants/carbon_values.yaml)
    #                                   + 0.25 * ((325.9138+10429.2402+0.9856+23.655+325.9138) / 500.0)
    #                                   = 11.25
    #                                   + 0.25 * (11105.7084 / 500.0)
    #                                   = 11.25 + 5.5529
    #                                   ≈ 16.8029 gCO2e/$
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
        expected_common_inputs={"compute-cost": 1.0, "storage-cost": 500.0},
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
        #              = 120.5 * 0.114
        #              = 13.737
        #
        #   operational_gco2e = SUM_per_region(cost * carbon_intensity) * energy_ratio_kwh_per_dollar
        #                     = 120.5 * 253 * 0.114
        #                     = 3475.461 gCO2e
        #
        #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
        #                  = 120.5 * 16.8029
        #                  = 2024.7495 gCO2e
        #
        #   total_gco2e = operational_gco2e + embodied_gco2e
        #               = 3475.461 + 2024.7495
        #               = 5500.2105 gCO2e
        "Test_ID_Misc_Services_01": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "westeurope",
                "EnergyKWH": 13.737,
                "OperationalCarbonGramsCO2eq": 3475.461,
                "EmbodiedCarbonGramsCO2eq": 2024.7495,
                "TotalCarbonGramsCO2eq": 5500.2105,
                "CarbonIntensity": 253,
            },
        # R7
        #   Energy KWH = cost * energy_ratio_kwh_per_dollar
        #              = 85 * 0.114
        #              = 9.69
        #
        #   operational_gco2e = SUM_per_region(cost * carbon_intensity) * energy_ratio_kwh_per_dollar
        #                     = 85 * 253 * 0.114
        #                     = 2451.57 gCO2e
        #
        #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
        #                  = 85 * 16.8029
        #                  = 1428.2465 gCO2e
        #
        #   total_gco2e = operational_gco2e + embodied_gco2e
        #               = 2451.57 + 1428.2465
        #               = 3879.8165 gCO2e
        "Test_ID_Misc_Services_02": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "westeurope",
                "EnergyKWH": 9.69,
                "OperationalCarbonGramsCO2eq": 2451.57,
                "EmbodiedCarbonGramsCO2eq": 1428.2465,
                "TotalCarbonGramsCO2eq": 3879.8165,
                "CarbonIntensity": 253,
            },
        # R8
        #   Energy KWH = cost * energy_ratio_kwh_per_dollar
        #              = 210.75 * 0.114
        #              = 24.0255
        #
        #   operational_gco2e = SUM_per_region(cost * carbon_intensity) * energy_ratio_kwh_per_dollar
        #                     = 210.75 * 280 * 0.114
        #                     = 6727.14 gCO2e
        #
        #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
        #                  = 210.75 * 16.8029
        #                  = 3541.2112 gCO2e
        #
        #   total_gco2e = operational_gco2e + embodied_gco2e
        #               = 6727.14 + 3541.2112
        #               = 10268.3512 gCO2e
        "Test_ID_Misc_Services_03": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "northeurope",
                "EnergyKWH": 24.0255,
                "OperationalCarbonGramsCO2eq": 6727.14,
                "EmbodiedCarbonGramsCO2eq": 3541.2112,
                "TotalCarbonGramsCO2eq": 10268.3512,
                "CarbonIntensity": 280,
            }
    }

    validate_output(row_by_id, expected_by_id)
