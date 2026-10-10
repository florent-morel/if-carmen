from pathlib import Path

from backend.src.schemas.resource import ResourceType
from backend.tests.daemon.end_to_end._e2e_helpers import run_daemon, validate_output


def test_e2e_misc_services_single_provider_azure(tmp_path):
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
    # Ratio inputs (default values from test_data modelling constants)
    #   compute_energy = 0.15  # kWh
    #   storage_energy = 0.02  # kWh
    #   compute_cost = 1  # $
    #   storage_cost = 1  # $
    #   compute_embodied = 15.0  # gCO2e
    #   storage_embodied = 65.0  # gCO2e
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
    #   IF products and derived total carbon keep full precision. The CSV
    #   writer rounds each final energy/carbon value to 4 decimals.
    #
    # R1: Azure Firewall - Standard - EU West
    #   energy_kwh = 120.50 * 0.1175 = 14.15875
    #   operational_gco2e = 14.15875 * 253 = 3582.16375
    #   embodied_gco2e = 120.50 * 27.5 = 3313.75
    #   total_gco2e = 3582.16375 + 3313.75 = 6895.91375
    #   report: energy=14.1587, operational=3582.1637, embodied=3313.7500
    #           total=3582.1637 + 3313.7500 = 6895.9137
    #
    # R2: Azure DDoS Protection - Standard - EU West
    #   energy_kwh = 85.00 * 0.1175 = 9.9875
    #   operational_gco2e = 9.9875 * 253 = 2526.8375
    #   embodied_gco2e = 85.00 * 27.5 = 2337.5
    #   total_gco2e = 2526.8375 + 2337.5 = 4864.3375
    #   report: energy=9.9875, operational=2526.8375, embodied=2337.5000
    #           total=2526.8375 + 2337.5000 = 4864.3375
    #
    # R3: Azure Application Gateway - Standard V2 - EU North
    #   energy_kwh = 210.75 * 0.1175 = 24.763125
    #   operational_gco2e = 24.763125 * 280 = 6933.675
    #   embodied_gco2e = 210.75 * 27.5 = 5795.625
    #   total_gco2e = 6933.675 + 5795.625 = 12729.3
    #   report: energy=24.7631, operational=6933.6750, embodied=5795.6250
    #           total=6933.6750 + 5795.6250 = 12729.3000
    # -------------------------------------------------------------------------
    run = run_daemon(Path(__file__), tmp_path)
    run.validate_if_inputs(
        "misc_services",
        expected_common_inputs={
            "energy-cost-ratio": 0.1175,
            "embodied-cost-ratio": 27.5,
        },
        expected_inputs_by_id={
            "Test_ID_Misc_Services_01": {"cost": 120.5},
            "Test_ID_Misc_Services_02": {"cost": 85.0},
            "Test_ID_Misc_Services_03": {"cost": 210.75},
        },
    )
    output_rows = run.rows
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
