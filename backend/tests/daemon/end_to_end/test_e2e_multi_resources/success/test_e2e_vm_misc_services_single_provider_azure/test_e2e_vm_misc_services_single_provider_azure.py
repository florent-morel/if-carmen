from pathlib import Path

import pytest

from backend.src.schemas.resource import ResourceType
from backend.tests.daemon.end_to_end._e2e_helpers import run_daemon, validate_output


def test_e2e_vm_misc_services_single_provider_azure():

    # ── Miscellaneous services computation derivation ─────────────────────────────────
    # 
    # Virtual machine computation is validated in test_e2e_vm_single_provider_azure
    # Miscellaneous services computation is validated here, based on the Virtual Machines computation result.
    #
    # Input data
    #   R1: cost=120.50, region=westeurope
    #   R2: cost=85.00,  region=westeurope
    #   R3: cost=210.75, region=northeurope
    #   VM1: 
    #       cost=4 (1 + 1 + 2), region=eastus
    #       EnergyKWH = 1.200e-2 kWh
    #       EmbodiedCarbonGramsCO2eq = 4.2763 gCO2e
    #   
    #
    # Constants (from test_data modelling constants)
    #   storage_cost=1.0 $, storage_energy=0.02 kWh
    #   storage_embodied=65.0 gCO2e
    #   weights: compute=0.75, storage=0.25
    #   westeurope -> Netherlands -> carbon_intensity=253 gCO2e/kWh
    #   northeurope -> Ireland -> carbon_intensity=280 gCO2e/kWh
    #
    # Formula reminders
    #   energy_ratio_kwh_per_dollar = 0.75 * (compute_energy / compute_cost)
    #                                  + 0.25 * (storage_energy / storage_cost)
    #                                = 0.75 * (0.012 / 4.0) + 0.25 * (0.02 / 1.0)
    #                                = 0.00725 kWh/$
    #   embodied_ratio_gco2e_per_dollar = 0.75 * (compute_embodied / compute_cost)
    #                                     + 0.25 * (storage_embodied / storage_cost)
    #                                   = 0.75 * (4.2763 / 4.0) + 0.25 * (65.0 / 1.0)
    #                                   = 21.45633 gCO2e/$
    #   energy_kwh = cost * energy_ratio_kwh_per_dollar
    #   operational_gco2e = energy_kwh * carbon_intensity
    #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
    #   total_gco2e = operational_gco2e + embodied_gco2e
    #
    # R1: Azure Firewall - Standard - EU West
    #   energy_kwh = 120.50 * 0.00725 = 0.873625
    #   operational_gco2e = 0.873625 * 253 = 220.830625
    #   embodied_gco2e = 120.50 * 21.45633 = 2585.064165
    #   total_gco2e = 220.830625 + 2585.064165 = 2805.89479
    #
    # R2: Azure DDoS Protection - Standard - EU West
    #   energy_kwh = 85.00 * 0.00725 = 0.61625
    #   operational_gco2e = 0.61625 * 253 = 155.71125
    #   embodied_gco2e = 85.00 * 21.45633 = 1823.28805
    #   total_gco2e = 155.71125 + 1823.28805 = 1978.9993
    #
    # R3: Azure Application Gateway - Standard V2 - EU North
    #   energy_kwh = 210.75 * 0.00725 = 1.5279375
    #   operational_gco2e = 1.5279375 * 280 = 427.2225
    #   embodied_gco2e = 210.75 * 21.45633 = 4518.9998475
    #   total_gco2e = 427.2225 + 4518.9998475 = 4946.2223475
    
    # Test finds WRONG values since the cost of the VM is 1, instead of 4, in the output CSV => there is a bug in the accumulation of the cost of the resource.
    # -------------------------------------------------------------------------

    output_rows = run_daemon(Path(__file__))

    row_by_id = {row["Id"]: row for row in output_rows}

    # 1 VM + 3 Storage resources
    assert len(output_rows) == 4

    expected_by_id = {
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
        "Test_ID_Misc_Services_01": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "westeurope",
                "EnergyKWH": 14.1587,
                "OperationalCarbonGramsCO2eq": 3582.1637,
                "EmbodiedCarbonGramsCO2eq": 3313.75,
                "TotalCarbonGramsCO2eq": 6895.9137,
                "CarbonIntensity": 253,
            },
        "Test_ID_Misc_Services_02": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "westeurope",
                "EnergyKWH": 9.9875,
                "OperationalCarbonGramsCO2eq": 2526.8375,
                "EmbodiedCarbonGramsCO2eq": 2337.5,
                "TotalCarbonGramsCO2eq": 4864.3375,
                "CarbonIntensity": 253,
            },
        "Test_ID_Misc_Services_03": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "VMSize": "Standard_A1_v2",
                "Provider": "azure",
                "Region": "northeurope",
                "EnergyKWH": 24.7631,
                "OperationalCarbonGramsCO2eq": 6933.675,
                "EmbodiedCarbonGramsCO2eq": 5795.625,
                "TotalCarbonGramsCO2eq": 12729.3,
                "CarbonIntensity": 280,
            }
    }

    validate_output(row_by_id, expected_by_id)
