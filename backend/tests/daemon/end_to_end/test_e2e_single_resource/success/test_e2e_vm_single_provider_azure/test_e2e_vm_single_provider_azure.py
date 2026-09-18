from pathlib import Path

import pytest

from backend.src.schemas.resource import ResourceType
from backend.tests.daemon.end_to_end._e2e_helpers import run_daemon, validate_output


def test_e2e_vm_single_provider_azure():

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

    output_rows = run_daemon(Path(__file__))

    row_by_id = {row["Id"]: row for row in output_rows}

    assert len(output_rows) == 1

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
            }
    }

    validate_output(row_by_id, expected_by_id)
