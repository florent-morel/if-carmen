from pathlib import Path

import pytest

from backend.src.schemas.resource import ResourceType
from backend.tests.daemon.end_to_end._e2e_helpers import run_daemon, validate_output


def test_e2e_misc_services_single_provider_azure():
    # -- Misc services carbon/energy computation derivation ------------------
    #
    # No VM or storage processors are configured for this fixture. The misc
    # services model therefore uses default_misc_services_constants.
    #
    # Input data
    #   R1: cost=120.50, region=westeurope
    #   R2: cost=85.00,  region=westeurope
    #   R3: cost=210.75, region=northeurope
    #
    # Constants (from test_data modelling constants)
    #   compute_cost=1.0 $, compute_energy=0.15 kWh
    #   storage_cost=1.0 $, storage_energy=0.02 kWh
    #   compute_embodied=15.0 gCO2e, storage_embodied=65.0 gCO2e
    #   weights: compute=0.75, storage=0.25
    #   westeurope -> Netherlands -> carbon_intensity=253 gCO2e/kWh
    #   northeurope -> Ireland -> carbon_intensity=280 gCO2e/kWh
    #
    # Formula reminders
    #   energy_ratio_kwh_per_dollar = 0.75 * (compute_energy / compute_cost)
    #                                  + 0.25 * (storage_energy / storage_cost)
    #                                = 0.75 * (0.15 / 1.0) + 0.25 * (0.02 / 1.0)
    #                                = 0.1175 kWh/$
    #   embodied_ratio_gco2e_per_dollar = 0.75 * (compute_embodied / compute_cost)
    #                                     + 0.25 * (storage_embodied / storage_cost)
    #                                   = 0.75 * (15.0 / 1.0) + 0.25 * (65.0 / 1.0)
    #                                   = 27.5 gCO2e/$
    #   energy_kwh = cost * energy_ratio_kwh_per_dollar
    #   operational_gco2e = energy_kwh * carbon_intensity
    #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
    #   total_gco2e = operational_gco2e + embodied_gco2e
    #
    # R1: Azure Firewall - Standard - EU West
    #   energy_kwh = 120.50 * 0.1175 = 14.15875
    #   operational_gco2e = 14.15875 * 253 = 3582.16375
    #   embodied_gco2e = 120.50 * 27.5 = 3313.75
    #   total_gco2e = 3582.16375 + 3313.75 = 6895.91375
    #
    # R2: Azure DDoS Protection - Standard - EU West
    #   energy_kwh = 85.00 * 0.1175 = 9.9875
    #   operational_gco2e = 9.9875 * 253 = 2526.8375
    #   embodied_gco2e = 85.00 * 27.5 = 2337.5
    #   total_gco2e = 2526.8375 + 2337.5 = 4864.3375
    #
    # R3: Azure Application Gateway - Standard V2 - EU North
    #   energy_kwh = 210.75 * 0.1175 = 24.763125
    #   operational_gco2e = 24.763125 * 280 = 6933.675
    #   embodied_gco2e = 210.75 * 27.5 = 5795.625
    #   total_gco2e = 6933.675 + 5795.625 = 12729.3
    # -------------------------------------------------------------------------
    output_rows = run_daemon(Path(__file__))
    row_by_id = {row["Id"]: row for row in output_rows}

    assert len(output_rows) == 3

    expected_by_id = {
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
        }
    }

    validate_output(row_by_id, expected_by_id)
