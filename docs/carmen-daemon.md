# Carmen Daemon

The Carmen Daemon is a specialized reporting tool designed to help you track and understand the environmental footprint of your cloud infrastructure. It generates comprehensive reports detailing the carbon emissions and energy consumption of your cloud resources, with particular emphasis on compute resources like virtual machines.

## Expected Source File Format

The daemon expects to read a group of csv files containing resource usage data. Below is a description for each column expected in the CSV input.

For all resource rows, input data can include `SampleDurationSeconds` to represent the usage duration for that row.
If `SampleDurationSeconds` is missing or empty, Carmen applies a default value of `86400` seconds.

Internally, Carmen stores per-observation durations as a list (`duration_seconds`) aligned with
resource `time_points`. For convenience when constructing schema objects in code/tests,
`duration_seconds` accepts either a single integer (for example `duration_seconds=86400`) or
an explicit list (for example `duration_seconds=[86400, 3600]`). A scalar value is normalized
to a one-element list.

### Input file structure (=columns)

TODO: review this.


| Field | Description | Example |
|------|-------------|---------|
| SampleTimestamp | Timestamp when the measurement was recorded, typically in ISO 8601 format | 2024-10-15T14:30:00Z |
| ResourceName | Human-readable name assigned to the resource | production-web-01 |
| ResourceId | Unique identifier for the resource | vm-a1b2c3d4e5f6 |
| VmSize | VM instance size used to look up hardware specifications | Standard_D4s_v3 |
| VmNbCpus | Number of vCPUs allocated to the VM, used to estimate CPU power when instance metadata is unavailable | 4 |
| Region | Region code used to determine carbon intensity | eastus |
| Provider | Name of the resource's provider, used to select provider-specific modelling values and instance data when available | azure |
| ResourceType | Resource category used to select the appropriate processor | Compute, Storage, network |
| AverageVmCpuUtilPercent | Average CPU utilization during the measurement period (0-100) | 45.7 |
| VmDiskSizeGb | Total provisioned disk storage in gigabytes | 128 |
| StorageSizeGB | Required for storage rows. Normalized storage capacity in gigabytes. | 512 |
| SampleDurationSeconds | Recommended for all resource rows. Duration represented by the row, in seconds. If missing or empty, Carmen defaults to 86400. | 3600 |
| ReplicationType | Storage replication type | GRS, LRS |

### Storage-specific ingestion contract

For every row where `ResourceType` is `Storage`, the following rules apply:

- `StorageSizeGB` is required and must be numeric and strictly positive.
- `SampleDurationSeconds` is optional but should be provided by the source. If it is missing or empty, Carmen applies the default duration `86400` seconds (1 day).
- If `SampleDurationSeconds` is non-numeric, zero, negative, or fractional, Carmen skips the row.


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
  orchestrator:
    list_processors:
      # Provide the list of processors used to estimate the impact of given resources.
      # Refer to documentation [[docs/methodology.md]] for more information on the models used for each resource.
      # List of supported processors:
      # - Processor_Compute: to estimate impact of Virtual Machines.
      # - Processor_Storage: to estimate impact of storage services.
      # - Processor_Misc_Services: to estimate impact of other services (security, network appliances, etc).
      - Processor_Compute
      - Processor_Storage
      - Processor_Misc_Services

```

To run the example, navigate to the project root and execute the orchestrator module entrypoint:

```bash
uv run python -m backend.src.daemon.carbon_daemon_orchestrator
```


## Carmen Logging


Carmen generates a log file per day stored in CARMEN_HOME/backend/logs.
