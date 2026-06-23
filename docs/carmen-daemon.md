# Carmen Daemon

The Carmen Daemon is a specialized reporting tool designed to help you track and understand the environmental footprint of your cloud infrastructure. It generates comprehensive reports detailing the carbon emissions and energy consumption of your cloud resources, with particular emphasis on compute resources like virtual machines.

## Carmen Daemon configuration

This section explains the configuration structure for the Carmen daemon and details the configuration files content.

TODO: Review this list
### Input files directory structure

Carmen daemon reads input files from a directory configured in main config file located in `etc/config/config.yaml`.

The configuration directory structure is the following:
``` sh
if-carmen/etc/config/
├── config-test.yaml
├── config.yaml
└── modelling_constants
    ├── carbon_intensity.yaml
    └── cloud_providers
        ├── aws
        │   └── aws.yaml
        ├── azure
        │   ├── azure_instances.csv
        │   └── azure.yaml
        └── gcp
            └── gcp.yaml
```

#### ~/etc/config/config.yaml

This is Carmen's main configuration file.

It contains: 
- Carbon intensity & PUE default values.
- Configuration settings for Carmen API (see [[carmen-as-a-service]] for more information).
- Input folder path.
- Output folder path.
- List of supported processors.
    - This corresponds to the implemented resources CO2 computation: TODO: properly define resources.
        * Compute: VM, pod, etc.
        * Storage: storage services.
        * Misc_Services: all other services required.

#### ~/etc/config/config-test.yaml

This file is following the same structure as config.yaml.
It is used for Unit Tests only.

#### ~/etc/config/modelling_constants/carbon-values.yaml

This file defines several carbon computation related values.
These are common to all providers.

This file defines the carbon intensity mapping per location.
A location can be: 
- A country (e.g. Sweden).
- A state (e.g. California).
- A city (e.g. Mumbai).
- Anything as long as it is provided in the input file dedicated column.

To support a new location in one's computation, a new entry should be added.

It also defines the embodied storage values for the following technologies:
- HDD.
- SSD.
- A default value is provided in case the technology is unknown.

#### ~/etc/config/modelling_constants/cloud_providers folder

This folder stores cloud providers specific configurations.

##### ~/etc/config/modelling_constants/azure/azure.yaml

This file is dedicated to Microsoft Azure Cloud Service Provider.
It defines constants related to:
- Power Usage Effectiveness ratio (PUE).
- Mapping between Azure defined regions and carbon intensity values defined in carbon-values.yaml.
- Electricity ratios: energy consumption of different resources.


##### ~/etc/config/modelling_constants/azure/azure_instances.csv

TODO: Explain what's in this file.

##### ~/etc/config/modelling_constants/aws/aws.yaml

Follows same structure. 
Not implemented yet.

##### ~/etc/config/modelling_constants/gcp/gcp.yaml

Follows same structure.  
Not implemented yet.

## Expected Source File Format

The daemon expects to read a group of csv files containing resource usage data. Below is a description for each column expected in the CSV input.

For all resource rows, input data can include `DurationSeconds` to represent the usage duration for that row.
If `DurationSeconds` is missing or empty, Carmen applies a default value of `86400` seconds.

Internally, Carmen stores per-observation durations as a list (`duration_seconds`) aligned with
resource `time_points`. For convenience when constructing schema objects in code/tests,
`duration_seconds` accepts either a single integer (for example `duration_seconds=86400`) or
an explicit list (for example `duration_seconds=[86400, 3600]`). A scalar value is normalized
to a one-element list.

### Input file structure (=columns)

TODO: review this.


| Field | Description | Example |
|------|-------------|---------|
| Time | Timestamp when the measurement was recorded, typically in ISO 8601 format | 2024-10-15T14:30:00Z |
| Name | Human-readable name assigned to the resource | production-web-01 |
| Id | Unique identifier for the virtual machine resource | vm-a1b2c3d4e5f6 |
| Size | VM instance size or tier (defines CPU, memory, and performance characteristics) | Standard_D4s_v3 |
| Region | Geographic location where the resource is deployed | Canada, California, European_Union |
| Service | Cloud service or product category the VM belongs to | Compute, Azure Virtual Machines, EC2 |
| AverageVmCpuUtilPercent | Average CPU utilization during the measurement period (0-100) | 45.7 |
| VmDiskSizeGb | Total provisioned disk storage in gigabytes | 128 |
| StorageSizeGB | Required for storage rows. Normalized storage capacity in gigabytes. | 512 |
| DurationSeconds | Recommended for all resource rows. Duration represented by the row, in seconds. If missing or empty, Carmen defaults to 86400. | 3600 |
| ReplicationType | Storage replication type | GRS, LRS |

### Storage-specific ingestion contract

Storage input files must include the following columns for every row where `MeterCategory` is `Storage`:

- `StorageSizeGB`
- `DurationSeconds`

These values are part of the source contract.

- `StorageSizeGB` is required and must be numeric and strictly positive.
- `DurationSeconds` should be provided by the source. If it is missing or empty, Carmen applies the default duration `86400` seconds (1 day).
- If `DurationSeconds` is non-numeric, zero, negative, or fractional, Carmen skips the row.


### Technical required data


## Report File

TODO: review this.
TODO: Add the expected unit when applicable.

The Carmen Daemon generates a detailed carbon emissions report in CSV format with the following fields:

| Field | Description | Example |
|------|-------------|---------|
| Date | Date of the reporting period for this record | 2025-10-27 |
| ResourceType | Type of cloud resource being reported | VM |
| Id | Unique Azure resource identifier (full ARM path) | /subscriptions/12345678-abcd-1234-abcd-123456789abc/resourceGroups/DATABASE-PROD-RG/providers/Microsoft.Compute/virtualMachines/prod-db-vm-001 |
| Name | Human-readable name of the virtual machine | prod-db-vm-001 |
| Region | Azure region where the VM is deployed | francecentral |
| EnergyKWh | Total energy consumed in kilowatt-hours during the reporting period | 0.1126 |
| OperationalCarbonGramsCO2eq | Carbon emissions from energy consumption during operation (grams of CO2 equivalent) | 4.9551 |
| EmbodiedCarbonGramsCO2eq | Carbon emissions from hardware manufacturing, transport, and disposal (grams of CO2 equivalent) | 6.1248 |
| TotalCarbonGramsCO2eq | Sum of operational and embodied carbon emissions (grams of CO2 equivalent) | 11.08 |
| CarbonIntensity | Carbon intensity of the France Central electricity grid (grams CO2eq per kWh) | 44.0 |
| VMSize | Azure VM instance size/SKU | Standard_E16ads_v5 |


> [!IMPORTANT]
> The report file is unique, regardless the number of resource types (compute, storage, misc services) included in the computation.
> A single row is specific to a single entry of a given resource type.
> As a consequence, some fields might be empty if they are not relevant for the given resource type.
> Applications reading Carmen's output files need to be aware of this.


## Running The Daemon

The example-data directory includes sample VM usage datasets you can use to explore and test Carmen Engine. The configuration below demonstrates how to run the engine in local-reader mode, processing example VM metrics and generating carbon reports locally.

```yaml
# Example Configuration for Carbon Engine with Sample Data
carmen_daemon:
  # SOURCE: Read VM metrics from local example data
  source:
    # Path to the example data directory
    # Using relative path from project root
    input_path: "vm-metrics"
    # Or use absolute path:
    # input_path: "/home/user/carbon-engine/example-data/vm-metrics"

  # Output directory for carbon reports
  output_path: "./output"
  # TODO document properly below
  orchestrator:
    list_processors:
      - Processor_Compute
      - Processor_Storage
      - Processor_Misc_Services

```

To run the example, navigate to the project root and execute the orchestrator module entrypoint:

```bash
uv run python -m backend.src.daemon.carbon_daemon_orchestrator
```
