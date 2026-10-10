from pathlib import Path

import pytest

from backend.src.schemas.resource import ResourceType
from backend.tests.daemon.end_to_end._e2e_helpers import run_daemon, validate_output


def test_e2e_vm_storage_misc_services_single_provider_azure(tmp_path):

    # ── Carbon/energy computation derivation ─────────────────────────────────
    #
    # Input data  (3 hourly time points for vm-01, all merged into one resource)
    #   T00: cpu_util=20%, T01: cpu_util=20%, T02: cpu_util=100%
    #   VmDiskSizeGb=128 GB  (all 3 rows)
    #
    # Instance hardware  (azure_instances.csv – Standard_A1_v2)
    #   cpu-cores-available=52, cpu-cores-utilized=1, cpu-tdp=205 W, memory=2 GB
    #   vm_tdp = 205 × (1/52) = 3.9423 W   ← TDP scaled to the allocated core share
    #
    # duration = SampleDurationSeconds = 3600 s per observation
    #
    # ── Energy per observation (SCI-E pipeline) ──────────────────────────────
    #
    # 1. TeadsCurve – linear interpolation [0,10,50,100]% → [0.12,0.32,0.75,1.02]
    #    tdp_ratio(20%)  = 0.32 + (20-10)/(50-10) × (0.75-0.32) = 0.4275
    #    tdp_ratio(100%) = 1.02   (exact control point)
    #
    # 2. cpu/power (kW) = tdp_ratio × vm_tdp / 1000
    #    T00,T01: 0.4275 × 3.942 / 1000 = 1.685e-3 kW
    #    T02:     1.020  × 3.942 / 1000 = 4.021e-3 kW
    #
    # 3. cpu/energy (kWh) = cpu/power × 3600 s / 3600 = cpu/power (1-hour window)
    #    T00,T01: 1.685e-3 kWh   T02: 4.021e-3 kWh
    #
    # 4. memory/power  = 2.0 GB × 3.920e-4 kW/GB = 7.840e-4 kW   (PMem, CCF)
    #    memory/energy = 7.840e-4 × 3600/3600         = 7.840e-4 kWh  (all obs.)
    #
    # 5. storage/power  = 128 GB × 9.250e-7 kW/GB = 1.184e-4 kW   (PVmStorage)
    #    storage/energy  = 1.184e-4 × 3600/3600    = 1.184e-4 kWh  (all obs.)
    #
    # 6. energy_raw = cpu/energy + memory/energy + storage/energy  (SciE sum)
    #    T00,T01: 1.685e-3 + 7.840e-4 + 1.184e-4 = 2.588e-3 kWh
    #    T02:     4.021e-3 + 7.840e-4 + 1.184e-4 = 4.924e-3 kWh
    #
    # 7. energy (kWh) = energy_raw × PUE  (SciEPue, azure PUE=1.185e0)
    #    T00,T01: 2.588e-3 × 1.185 = 3.066e-3 kWh
    #    T02:     4.924e-3 × 1.185 = 5.834e-3 kWh
    #    ─────────────────────────────────────────
    #    TOTAL EnergyKWH = 3.066e-3 + 3.066e-3 + 5.834e-3 = 1.200e-2 kWh
    #
    # ── Operational carbon (SciO) ────────────────────────────────────────────
    #
    #    carbon-operational = energy × carbon_intensity
    #    carbon_intensity(eastus) = 384 gCO2/kWh  (United_States, carbon_values.yaml)
    #    T00,T01: 3.066e-3 × 384 = 1.178 gCO2e
    #    T02:     5.834e-3 × 384 = 2.240 gCO2e
    #    ─────────────────────────────────────────
    #    TOTAL OperationalCarbonGramsCO2eq = 1.178 + 1.178 + 2.240 = 4.596 gCO2e
    #
    # ── Embodied carbon (SciM pipeline) ─────────────────────────────────────
    #
    #    CPU embodied (sci-m-cpu / @grnsft/if-plugins SciM):
    #      = device_embodied × (duration / expected_lifespan) × (vcpus_allocated / vcpus_total)
    #      = 1999999 × (3600 / 126230400) × (1 / 52) = 1.097 gCO2e per obs.
    #      (device/emissions-embodied=1999999 treated as gCO2e by the SciM plugin,
    #       device/expected-lifespan=126230400 s = 4 years)
    #
    #    Storage embodied (m-vm-storage):
    #      = storage/requested × storage/embodied-coefficient × duration / expected_lifespan
    #      = 128 × 90 × 3600 / 126230400 = 3.285e-1 gCO2e per obs.
    #      (storage/embodied-coefficient=90 gCO2e/GB, unknown/default)
    #
    #    Total per obs.: 1.097 + 3.285e-1 = 1.425 gCO2e  (same for all 3, embodied is time-independent)
    #    ─────────────────────────────────────────
    #    TOTAL EmbodiedCarbonGramsCO2eq = 3 × 1.425 = 4.276 gCO2e
    #
    # ── Total carbon ─────────────────────────────────────────────────────────
    #    TOTAL TotalCarbonGramsCO2eq = 4.596 + 4.276 = 8.872 gCO2e
    # ─────────────────────────────────────────────────────────────────────────
    # Formula reminders
    #   Ratios use full IF VM/storage totals. The CSV writer rounds final
    #   energy and carbon metrics to 4 decimals after calculating total carbon.
    #   compute_energy = 0.011967  # kWh
    #   storage_energy = 2.922979  # kWh
    #   compute_cost = 400  # $
    #   storage_cost = 500  # $
    #   compute_embodied = 4.276311  # gCO2e
    #   storage_embodied = 11105.708419  # gCO2e
    #
    #   energy_ratio_kwh_per_dollar = 0.75 * (compute_energy / compute_cost)
    #                                  + 0.25 * (storage_energy / storage_cost)
    #                                = 0.001484 kWh/$
    #   embodied_ratio_gco2e_per_dollar = 0.75 * (compute_embodied / compute_cost)
    #                                     + 0.25 * (storage_embodied / storage_cost)
    #                                   = 5.560872 gCO2e/$
    #
    #   operational_gco2e (for a given resource) =  (cost * carbon_intensity_per_region) * energy_ratio_kwh_per_dollar
    #
    #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
    #
    #   total_gco2e = operational_gco2e + embodied_gco2e
    #

    run = run_daemon(Path(__file__), tmp_path)
    run.validate_if_inputs(
        "vm",
        expected_inputs_by_id={"Test_ID_VM_01": {"vcpus-total": 52.0}},
    )
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
            "energy-cost-ratio": 0.001484,
            "embodied-cost-ratio": 5.560872,
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
    assert len(output_rows) == 9

    expected_by_id = {
        # R1 -- Values are the same as the e2e test for storage single resource
        "Test_ID_VM_01":
            {
                "ResourceType": ResourceType.VIRTUAL_MACHINE.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "eastus",
                "EnergyKWH": 0.012,
                "OperationalCarbonGramsCO2eq": 4.5955,
                "EmbodiedCarbonGramsCO2eq": 4.2763,
                "TotalCarbonGramsCO2eq": 8.8718,
                "CarbonIntensity": 384,
            },
            # R2 -- Values are the same as the e2e test for storage single resource
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
            # R3 -- Values are the same as the e2e test for storage single resource
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
            # R4 -- Values are the same as the e2e test for storage single resource
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
            # R5 -- Values are the same as the e2e test for storage single resource
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
            # R6 -- Values are the same as the e2e test for storage single resource
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
            # R7
            #   Energy KWH = cost * energy_ratio_kwh_per_dollar
            #              = 120.5 * energy_ratio = 0.178813
            #
            #   operational_gco2e = energy * 253 = 45.239782
            #
            #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
            #                  = 120.5 * embodied_ratio = 670.085111
            #
            #   report: energy=0.1788, operational=45.2398, embodied=670.0851
            #           total=715.3249 (rounded from unrounded component sum)
        "Test_ID_Misc_Services_01": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "westeurope",
                "EnergyKWH": 0.1788,
                "OperationalCarbonGramsCO2eq": 45.2398,
            "EmbodiedCarbonGramsCO2eq": 670.0851,
                "TotalCarbonGramsCO2eq": 715.3249,
                "CarbonIntensity": 253,
            },
            # R8
            #   Energy KWH = cost * energy_ratio_kwh_per_dollar
            #              = 85 * energy_ratio = 0.126134
            #
            #   operational_gco2e = energy * 253 = 31.911880
            #
            #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
            #                  = 85 * embodied_ratio = 472.674145
            #
            #   report: energy=0.1261, operational=31.9119, embodied=472.6741
            #           total=504.5860 (rounded from unrounded component sum)
        "Test_ID_Misc_Services_02": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "westeurope",
                "EnergyKWH": 0.1261,
                "OperationalCarbonGramsCO2eq": 31.9119,
            "EmbodiedCarbonGramsCO2eq": 472.6741,
                "TotalCarbonGramsCO2eq": 504.586,
                "CarbonIntensity": 253,
            },
            # R9
            #   Energy KWH = cost * energy_ratio_kwh_per_dollar
            #              = 210.75 * energy_ratio = 0.312738
            #
            #   operational_gco2e = energy * 280 = 87.566613
            #
            #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
            #                  = 210.75 * embodied_ratio = 1171.953836
            #
            #   report: energy=0.3127, operational=87.5666, embodied=1171.9538
            #           total=1259.5204 (rounded from unrounded component sum)
        "Test_ID_Misc_Services_03": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "northeurope",
                "EnergyKWH": 0.3127,
                "OperationalCarbonGramsCO2eq": 87.5666,
            "EmbodiedCarbonGramsCO2eq": 1171.9538,
                "TotalCarbonGramsCO2eq": 1259.5204,
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
