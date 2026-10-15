# Carmen Daemon

The Carmen Daemon is a specialized reporting tool designed to help you track and understand the environmental footprint of your cloud infrastructure. It generates comprehensive reports detailing the carbon emissions and energy consumption of your cloud resources, with particular emphasis on compute resources like virtual machines.

## Expected Source File Format

The daemon expects to read a group of csv files containing resource usage data. Below is a description for each column expected in the CSV input.

For all resource rows, input data can include `SampleDurationSeconds` to represent the usage duration for that row.
If `SampleDurationSeconds` is missing or empty, Carmen applies a default value of `86400` seconds.
When supplied, `SampleDurationSeconds` must be a positive whole number of seconds.

### Input file structure

#### Common fields

| Field | Description | Example |
|------|-------------|---------|
| SampleTimestamp | Timestamp when the measurement was recorded, typically in ISO 8601 format | 2024-10-15T14:30:00Z |
| ResourceName | Human-readable name assigned to the resource | production-web-01 |
| ResourceId | Unique identifier for the resource | vm-a1b2c3d4e5f6 |
| Region | Region code used to determine carbon intensity | eastus |
| Provider | Name of the resource's provider, used to select provider-specific modelling values and instance data when available | azure |
| Cost | Cost attributed to this resource row; required for compute rows (use 0 if unknown) | 120.50 |
| ResourceType | Resource category used to select the appropriate processor | Compute, Storage, network |
| SampleDurationSeconds | Recommended for all resource rows. Duration represented by the row, in seconds. If missing or empty, Carmen defaults to 86400. | 3600 |

#### VM fields

| Field | Description | Example |
|------|-------------|---------|
| VmSize | VM instance size used to look up hardware specifications | Standard_D4s_v3 |
| VmNbCpus | Number of vCPUs allocated to the VM, used to estimate CPU power when instance metadata is unavailable | 4 |
| AverageVmCpuUtilPercent | Average CPU utilization during the measurement period (0-100) | 45.7 |
| VmDiskSizeGb | Total provisioned disk storage in gigabytes | 128 |

#### Storage fields

| Field | Description | Example |
|------|-------------|---------|
| StorageSizeGB | Required for storage rows. Normalized storage capacity in gigabytes. | 512 |
| StorageType | Storage technology used to select the storage power coefficient | SSD |
| StorageReplicationType | Storage replication type | GRS, LRS |

#### Misc-services fields

Misc-services input rows have no additional columns. Their common `Cost` value drives the cost-based energy and embodied estimates. If it is missing, Carmen uses `0`, producing zero estimated impact for that resource. Use the same currency for VM, storage, and misc-services costs.

### VM-specific input and modelling

For rows with `ResourceType` set to `Compute`:

- `AverageVmCpuUtilPercent` and `VmDiskSizeGb` provide CPU utilization and disk capacity for each observation; the VM reader expects both columns.
- `VmSize` selects provider instance metadata. If no matching instance is available, the provider must define `electricity_ratios.cpu_max`. Carmen then uses `VmNbCpus` or, for Azure only, a vCPU count inferred from `VmSize`. Without those fallback inputs, CPU energy computation fails.

### Storage-specific input and modelling

For rows with `ResourceType` set to `Storage`:

- `StorageSizeGB` must be present, numeric, and greater than zero; otherwise the row is skipped.
- `StorageType` selects the storage power coefficient. Missing or unrecognized values use the configured `unknown` coefficient; computation fails if no applicable coefficient exists.
- `StorageReplicationType` selects a factor from the provider's `storage_replication_factors`. A missing or unmapped factor can pass ingestion but prevents computation when a provider configuration is loaded. Without a provider configuration, Carmen uses a factor of `1`.



## Report File

The Carmen Daemon generates one CSV report for all resource types, using the same columns. Each row fills the common fields and the fields for its resource type; other resource-specific fields are empty.

The `Input field` column names a corresponding source CSV column; `-` means there is no direct counterpart. `Date` is assigned by the daemon, and carbon intensity and impact totals are calculated from inputs and configuration. Input `Compute` rows are reported as `VirtualMachine`, while VM `Cost` accumulates across observations. `SampleTimestamp`, `SampleDurationSeconds`, `AverageVmCpuUtilPercent`, `VmNbCpus`, and `VmDiskSizeGb` have no separate report columns.

### Common fields

| Field | Input field | Description | Example |
|------|-------------|-------------|---------|
| Date | - | Daemon execution date (defaults to the current date; can be set with `EXECUTION_DATE`) | 2025-10-27 |
| ResourceType | `ResourceType` | Type of resource being reported (`VirtualMachine`, `Storage`, or `MiscServices`) | VirtualMachine |
| ResourceId | `ResourceId` | Unique resource identifier | /subscriptions/12345678-abcd-1234-abcd-123456789abc/resourceGroups/DATABASE-PROD-RG/providers/Microsoft.Compute/virtualMachines/prod-db-vm-001 |
| ResourceName | `ResourceName` | Human-readable name of the resource | prod-db-vm-001 |
| Provider | `Provider` | Provider of the reported resource | azure |
| Region | `Region` | Region of the reported resource | francecentral |
| EnergyKWH | - | Total energy consumed by the resource across its processed observations (kWh) | 0.1126 |
| OperationalCarbonGramsCO2eq | - | Carbon emissions from energy consumption during operation (grams of CO2 equivalent) | 4.9551 |
| EmbodiedCarbonGramsCO2eq | - | Carbon emissions from hardware manufacturing, transport, and disposal (grams of CO2 equivalent) | 6.1248 |
| TotalCarbonGramsCO2eq | - | Sum of operational and embodied carbon emissions (grams of CO2 equivalent) | 11.08 |
| CarbonIntensity | - | Carbon intensity of the region electricity grid (grams CO2eq per kWh) | 44.0 |
| Cost | `Cost` | Cost of the reported resource | 120.50 |

### VM fields

| Field | Input field | Description | Example |
|------|-------------|-------------|---------|
| VmSize | `VmSize` | Azure VM instance size/SKU | Standard_E16ads_v5 |

### Storage fields

| Field | Input field | Description | Example |
|------|-------------|-------------|---------|
| StorageType | `StorageType` | Storage technology of the resource | SSD |
| StorageReplicationType | `StorageReplicationType` | Storage replication setting | LRS |
| StorageSizeGB | `StorageSizeGB` | Storage size in gigabytes | 32.0 |

### Misc services fields

Misc-services rows have no additional columns.

Energy and carbon values are rounded to four decimal places in the CSV. Total carbon is rounded independently, so its displayed value may differ slightly from the sum of the displayed operational and embodied values. See [Precision and reporting](methodology.md#precision-and-reporting).


> [!IMPORTANT]
> The report file is unique, regardless the number of resource types (compute, storage, misc services) included in the computation.
> A single row is specific to a single entry of a given resource type.
> As a consequence, some fields might be empty if they are not relevant for the given resource type.
> Applications reading Carmen's output files need to be aware of this.


## Running The Daemon

The [VM example configuration](../example-data/config.yaml) reads the [sample VM metrics](../etc/sample_data/vm-metrics/) and writes a CSV report. From the project root, with dependencies installed, run:

```bash
uv run python -m backend.src.daemon.carbon_daemon_orchestrator --carmen-config-filepath example-data/config.yaml
```

The report is written to `output/CO2_YYYY-MM-DD.csv`. Other configurations are available in the [daemon end-to-end tests](../backend/tests/daemon/end_to_end/).

## Carmen Logging


Carmen writes logs to the console. When `TEST_ENV` is enabled, it also writes a log file in the backend package's `logs` directory.
