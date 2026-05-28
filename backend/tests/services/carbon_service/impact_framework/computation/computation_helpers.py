"""
This module contains the test computation helpers. It is used to replicate what the IF
pipeline does when it computes carbon emissions.
"""

import numpy as np

# European Average for 2024 (Source: https://ourworldindata.org/grapher/carbon-intensity-electricity)
CARBON_INTENSITY_EUROPE = 281  # gCO2 per kWh

STORAGE_POWER_COEFFICIENT_MAPPING = (
    {  # in kWh/GBh from https://www.cloudcarbonfootprint.org/docs/methodology/#storage
        "SSD": 0.0000012,
        "HDD": 0.00000065,
        "UNKNOWN": 0.000000925,  # Average
    }
)

STORAGE_EMBODIED_COEFFICIENT_MAPPING = (
    {  # in gCO2e/GB from https://hotcarbon.org/assets/2022/pdf/hotcarbon22-tannu.pdf
        "SSD": 160,
        "HDD": 20,
        "UNKNOWN": 90,  # Average
    }
)

# Replication factors for different Azure storage types
# https://docs.google.com/spreadsheets/d/1D7mIGKkdO1djPoMVmlXRmzA7_4tTiGZLYdVbfe85xQM/edit?gid=2008238628#gid=2008238628
STORAGE_REPLICATION_FACTORS = {
    "LRS": 3,  # Locally redundant storage - 3 copies in single physical location
    "ZRS": 3,  # Zone redundant storage - 3 copies across availability zones
    "GRS": 6,  # Geo redundant storage - 3 primary + 3 secondary copies
    "RA_GRS": 6,  # Read-access geo redundant - same as GRS
    "GZRS": 6,  # Geo-zone redundant - 3 copies across zones + 3 secondary
    "RA_GZRS": 6,  # Read-access geo-zone - same as GZRS
}

# TODO: -> Config
MEMORY_COEFFICIENT = 0.000392
DEVICE_EMISSIONS = 1672000
EXPECTED_LIFESPAN = 126230400  # 4 years in seconds


def compute_tdp_ratio(cpu_util: float) -> float:
    """
    Compute the TDP ratio based on CPU utilization.
    """
    return np.interp(cpu_util * 100, [0, 10, 50, 100], [0.12, 0.32, 0.75, 1.02])


def compute_cpu_energy(tdp: float, tdp_ratio: float, duration: float) -> float:
    """
    Compute the CPU energy consumption.
    """
    return tdp * tdp_ratio * duration / 1000


def compute_memory_energy(memory_requested: float, duration: float) -> float:
    """
    Compute the memory energy consumption.
    """
    memory_energy = MEMORY_COEFFICIENT * memory_requested * duration
    return memory_energy


def compute_storage_energy(storage_size: float, duration: float) -> float:
    """
    Compute the storage energy consumption.
    Args:
        storage_size (float): storage size in GB
        duration (float): duration in hours
    Returns:
        float: energy consumption in kWh
    """
    return storage_size * STORAGE_POWER_COEFFICIENT_MAPPING["UNKNOWN"] * duration


def compute_operational_carbon(energy: float) -> float:
    """
    Compute the operational carbon emissions.
    """
    return energy * CARBON_INTENSITY_EUROPE


def compute_embodied_carbon(
    vcpu_allocated: float, vcpu_total: float, storage_size: float, duration: float
) -> float:
    """
    Compute the embodied carbon emissions.
    duration in hours
    """
    cpu_embodied = (
        DEVICE_EMISSIONS
        * duration
        * 3600
        / EXPECTED_LIFESPAN
        * vcpu_allocated
        / vcpu_total
    )
    storage_embodied = (
        storage_size
        * STORAGE_EMBODIED_COEFFICIENT_MAPPING["UNKNOWN"]
        * duration
        * 3600
        / EXPECTED_LIFESPAN
    )
    return cpu_embodied + storage_embodied


def compute_storage_energy_helper(
    size_gb: float, storage_type: str, replication_type: str, duration_seconds: float
) -> float:
    """
    Compute storage energy consumption to validate IF pipeline results.

    Args:
        size_gb (float): Storage size in GB
        storage_type (str): Storage type as stored in StorageResource (SSD, HDD, Unknown)
        replication_type (str): Replication type (LRS, GRS, ZRS, etc.)
        duration_seconds (float): Duration in seconds

    Returns:
        float: Energy consumption in kWh
    """
    # 1. Get power coefficient
    power_coefficient = STORAGE_POWER_COEFFICIENT_MAPPING.get(
        storage_type.upper(), STORAGE_POWER_COEFFICIENT_MAPPING["UNKNOWN"]
    )

    # 2. Apply replication factor
    replication_factor = STORAGE_REPLICATION_FACTORS.get(replication_type.upper(), 1)
    effective_size = size_gb * replication_factor

    # 3. Calculate power
    power_kw = effective_size * power_coefficient

    # 4. Calculate energy
    duration_hours = duration_seconds / 3600
    energy_kwh = power_kw * duration_hours

    return energy_kwh


def compute_storage_operational_helper(
    energy_kwh: float, carbon_intensity: float
) -> float:
    """
    Compute storage operational carbon emissions.

    Args:
        energy_kwh (float): Energy consumption in kWh
        carbon_intensity (float): Carbon intensity in gCO2/kWh

    Returns:
        float: Operational carbon emissions in gCO2e
    """
    return energy_kwh * carbon_intensity


def compute_storage_embodied_helper(
    size_gb: float, storage_type: str, replication_type: str, duration_seconds: float
) -> float:
    """
    Compute storage embodied carbon emissions to validate IF pipeline results.

    Args:
        size_gb (float): Storage size in GB
        storage_type (str): Storage type (SSD, HDD, Unknown)
        replication_type (str): Replication type (LRS, GRS, ZRS, etc.)
        duration_seconds (float): Duration in seconds

    Returns:
        float: Embodied carbon emissions in gCO2e
    """
    # 1. Get embodied coefficient
    embodied_coefficient = STORAGE_EMBODIED_COEFFICIENT_MAPPING.get(
        storage_type.upper(), STORAGE_EMBODIED_COEFFICIENT_MAPPING["UNKNOWN"]
    )

    # 2. Apply replication factor
    replication_factor = STORAGE_REPLICATION_FACTORS.get(replication_type.upper(), 1)
    effective_size = size_gb * replication_factor

    # 3. Calculate embodied emissions
    embodied_gco2 = (
        effective_size * embodied_coefficient * duration_seconds / EXPECTED_LIFESPAN
    )

    return embodied_gco2


def compute_services_energy_helper(
    compute_energy: float,
    storage_energy: float,
    compute_cost: float,
    storage_cost: float,
    misc_services_cost: float,
) -> float:
    """
    Compute services energy consumption based on cost allocation.

    Args:
        compute_energy (float): Compute energy in kWh
        storage_energy (float): Storage energy in kWh
        compute_cost (float): Compute cost
        storage_cost (float): Storage cost
        misc_services_cost (float): Total services cost

    Returns:
        float: Services energy consumption in kWh
    """
    return misc_services_cost * (
        0.75 * (compute_energy / compute_cost) + 0.25 * (storage_energy / storage_cost)
    )


def compute_services_operational_helper(
    compute_energy: float,
    storage_energy: float,
    compute_cost: float,
    storage_cost: float,
    misc_services_cost: float,
    carbon_intensity: float,
) -> float:
    """
    Compute services operational carbon emissions.

    Args:
        compute_energy (float): Compute energy in kWh
        storage_energy (float): Storage energy in kWh
        compute_cost (float): Compute cost
        storage_cost (float): Storage cost
        misc_services_cost (float): Total services cost
        carbon_intensity (float): Carbon intensity in gCO2/kWh

    Returns:
        float: Services operational carbon emissions in gCO2e
    """
    return (
        misc_services_cost
        * (
            0.75 * (compute_energy / compute_cost)
            + 0.25 * (storage_energy / storage_cost)
        )
        * carbon_intensity
    )


def compute_services_embodied_helper(
    compute_embodied: float,
    storage_embodied: float,
    compute_cost: float,
    storage_cost: float,
    misc_services_cost: float,
) -> float:
    """
    Compute services embodied carbon emissions based on service cost.

    Args:
        compute_embodied (float): Compute embodied carbon in gCO2e
        storage_embodied (float): Storage embodied carbon in gCO2e
        compute_cost (float): Compute cost
        storage_cost (float): Storage cost
        misc_services_cost (float): Total services cost

    Returns:
        float: Services embodied carbon emissions in gCO2e
    """
    return misc_services_cost * (
        0.75 * (compute_embodied / compute_cost)
        + 0.25 * (storage_embodied / storage_cost)
    )
