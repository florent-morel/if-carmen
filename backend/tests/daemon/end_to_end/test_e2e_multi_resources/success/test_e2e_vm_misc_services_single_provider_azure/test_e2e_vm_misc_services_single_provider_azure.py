from pathlib import Path

from backend.src.schemas.resource import ResourceType
from backend.tests.daemon.end_to_end._e2e_helpers import run_daemon, validate_output


def test_e2e_vm_misc_services_single_provider_azure(tmp_path):

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
    #       IF energy=0.011967 kWh, embodied=4.276311 gCO2e
    #       CSV energy=0.0120 kWh, embodied=4.2763 gCO2e
    #
    #
    # Ratio inputs
    #   compute_energy = 0.011967  # kWh
    #   storage_energy = 0.02  # kWh (default value)
    #   compute_cost = 4  # $
    #   storage_cost = 1  # $
    #   compute_embodied = 4.276311  # gCO2e
    #   storage_embodied = 65.0  # gCO2e (default value)
    #   weights: compute=0.75, storage=0.25
    #   westeurope -> Netherlands -> carbon_intensity=253 gCO2e/kWh
    #   northeurope -> Ireland -> carbon_intensity=280 gCO2e/kWh
    #
    # Formula reminders
    #   Ratios use unrounded IF totals. The CSV writer rounds final metrics to
    #   4 decimals, including total carbon calculated from unrounded components.
    #   energy_ratio_kwh_per_dollar = 0.75 * (compute_energy / compute_cost)
    #                                  + 0.25 * (storage_energy / storage_cost)
    #                                = 0.007244 kWh/$
    #   embodied_ratio_gco2e_per_dollar = 0.75 * (compute_embodied / compute_cost)
    #                                     + 0.25 * (storage_embodied / storage_cost)
    #                                   = 17.051808 gCO2e/$
    #   energy_kwh = cost * energy_ratio_kwh_per_dollar
    #   operational_gco2e = energy_kwh * carbon_intensity
    #   embodied_gco2e = cost * embodied_ratio_gco2e_per_dollar
    #   total_gco2e = operational_gco2e + embodied_gco2e
    #
    # R1: Azure Firewall - Standard - EU West
    #   energy_kwh = 120.5 * energy_ratio = 0.872887
    #   operational_gco2e = energy_kwh * 253 = 220.840473
    #   embodied_gco2e = 120.5 * embodied_ratio = 2054.742894
    #   report: energy=0.8729, operational=220.8405, embodied=2054.7429
    #           total=2275.5834 (rounded from unrounded component sum)
    #
    # R2: Azure DDoS Protection - Standard - EU West
    #   energy_kwh = 85.0 * energy_ratio = 0.615730
    #   operational_gco2e = energy_kwh * 253 = 155.779587
    #   embodied_gco2e = 85.0 * embodied_ratio = 1449.403701
    #   report: energy=0.6157, operational=155.7796, embodied=1449.4037
    #           total=1605.1833 (rounded from unrounded component sum)
    #
    # R3: Azure Application Gateway - Standard V2 - EU North
    #   energy_kwh = 210.75 * energy_ratio = 1.526647
    #   operational_gco2e = energy_kwh * 280 = 427.461214
    #   embodied_gco2e = 210.75 * embodied_ratio = 3593.668589
    #   report: energy=1.5266, operational=427.4612, embodied=3593.6686
    #           total=4021.1298 (rounded from unrounded component sum)

    # -------------------------------------------------------------------------

    run = run_daemon(Path(__file__), tmp_path)
    output_rows = run.rows

    row_by_id = {row["Id"]: row for row in output_rows}

    # 1 VM + 3 Misc Services resources
    assert len(output_rows) == 4
    run.validate_if_inputs(
        stage="vm",
        expected_inputs_by_id={"Test_ID_VM_01": {"vcpus-total": 52.0, "vcpus-allocated": 1.0}},
    )
    run.validate_if_inputs(
        stage="misc_services",
        expected_common_inputs={
            "energy-cost-ratio": 0.007244,
            "embodied-cost-ratio": 17.051808,
        },
        expected_inputs_by_id={
            "Test_ID_Misc_Services_01": {"cost": 120.5},
            "Test_ID_Misc_Services_02": {"cost": 85.0},
            "Test_ID_Misc_Services_03": {"cost": 210.75},
        },
    )

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
                "Provider": "azure",
                "Region": "westeurope",
                "EnergyKWH": 0.8729,
                "OperationalCarbonGramsCO2eq": 220.8405,
                "EmbodiedCarbonGramsCO2eq": 2054.7429,
                "TotalCarbonGramsCO2eq": 2275.5834,
                "CarbonIntensity": 253,
            },
        "Test_ID_Misc_Services_02": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "Provider": "azure",
                "Region": "westeurope",
                "EnergyKWH": 0.6157,
                "OperationalCarbonGramsCO2eq": 155.7796,
                "EmbodiedCarbonGramsCO2eq": 1449.4037,
                "TotalCarbonGramsCO2eq": 1605.1833,
                "CarbonIntensity": 253,
            },
        "Test_ID_Misc_Services_03": {
                "ResourceType": ResourceType.MISC_SERVICES.value,
                "Provider": "azure",
                "Region": "northeurope",
                "EnergyKWH": 1.5266,
                "OperationalCarbonGramsCO2eq": 427.4612,
                "EmbodiedCarbonGramsCO2eq": 3593.6686,
                "TotalCarbonGramsCO2eq": 4021.1298,
                "CarbonIntensity": 280,
            }
    }

    validate_output(row_by_id, expected_by_id)
