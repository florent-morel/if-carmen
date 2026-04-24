# Carbon Daemon
The Carbon Daemon is a specialized reporting tool designed to help you track and understand the environmental footprint of your cloud infrastructure **in Azure**. It generates comprehensive reports detailing the carbon emissions and energy consumption of your cloud resources, with particular emphasis on compute resources like virtual machines.

## Expected Source File Format

The daemon expects to read a group of csv files containing resource usage data. Below is a description for each column expected in the CSV input.

| Field | Description | Example |
|------|-------------|---------|
| Time | Timestamp when the measurement was recorded, typically in ISO 8601 format | 2024-10-15T14:30:00Z |
| Id | Unique identifier for the virtual machine resource | vm-a1b2c3d4e5f6 |
| Size | VM instance size or tier (defines CPU, memory, and performance characteristics) | Standard_D4s_v3 |
| Region | Geographic location where the resource is deployed | Canada, California, European_Union |
| Service | Cloud service or product category the VM belongs to | Compute, Azure Virtual Machines, EC2 |
| Component | Logical component or application layer the VM serves | web-server, database, api-gateway |
| Subscription | Cloud subscription or account identifier | prod-subscription-001 |
| Name | Human-readable name assigned to the VM | production-web-01 |
| Instance | Instance identifier or number within a deployment group | instance-01, web-server-03 |
| Environment | Deployment environment designation | production, staging, development |
| Partition | Logical partition, tenant, or organizational division | customer-a, team-finance, partition-1 |
| AverageCpuPercentage | Average CPU utilization during the measurement period (0-100) | 45.7 |
| DiskSizeGb | Total provisioned disk storage in gigabytes | 128 |

## Report File

The Carmen Daemon generates a detailed carbon emissions report in CSV format with the following fields:

| Field | Description | Example |
|------|-------------|---------|
| Date | Date of the reporting period for this record | 2025-10-27 |
| ResourceType | Type of cloud resource being reported | VM |
| Id | Unique Azure resource identifier (full ARM path) | /subscriptions/12345678-abcd-1234-abcd-123456789abc/resourceGroups/DATABASE-PROD-RG/providers/Microsoft.Compute/virtualMachines/prod-db-vm-001 |
| Name | Human-readable name of the virtual machine | prod-db-vm-001 |
| Region | Azure region where the VM is deployed | francecentral |
| Subscription | Cloud subscription or account identifier | production-subscription-01 |
| EnergyKWh | Total energy consumed in kilowatt-hours during the reporting period | 0.1126 |
| OperationalCarbonGramsCO2eq | Carbon emissions from energy consumption during operation (grams of CO2 equivalent) | 4.9551 |
| EmbodiedCarbonGramsCO2eq | Carbon emissions from hardware manufacturing, transport, and disposal (grams of CO2 equivalent) | 6.1248 |
| TotalCarbonGramsCO2eq | Sum of operational and embodied carbon emissions (grams of CO2 equivalent) | 11.08 |
| CarbonIntensity | Carbon intensity of the France Central electricity grid (grams CO2eq per kWh) | 44.0 |
| VMSize | Azure VM instance size/SKU | Standard_E16ads_v5 |
| Service | Application or service name | couchbase |
| Instance | Specific instance identifier within the service | db-instance-001 |
| Environment | Deployment environment | prd |
| Partition | Logical partition or tenant | (empty) |
| Component | Infrastructure component type | db |

## Running The Daemon

The example-data directory includes sample VM usage datasets you can use to explore and test Carbon Engine. The configuration below demonstrates how to run the engine in local-reader mode, processing example VM metrics and generating carbon reports locally.

```yaml
# Example Configuration for Carbon Engine with Sample Data
# This configuration uses the local reader to process the example VM metrics
carmen_daemon:
  # SOURCE: Read VM metrics from local example data
  source:
    type: local

    # Files to process - choose one or more:
    # Option 1: Simple example (2 VMs, 3 hours each)
    file_names:
      - "vm_metrics_simple.csv"

    # Option 2: Full monthly data (6 VMs, January)
    # file_names:
    #   - "vm_metrics_2024_01.csv"

    # Option 3: Multi-month data (January + February)
    # file_names:
    #   - "vm_metrics_2024_01.csv"
    #   - "vm_metrics_2024_02.csv"

    # Local filesystem configuration
    local:
      # Path to the example data directory
      # Using relative path from project root
      source_path: "vm-metrics"

      # Or use absolute path:
      # source_path: "/home/user/carbon-engine/example-data/vm-metrics"

  # UPLOAD: Write carbon reports to local output directory
  upload:
    type: local
    # Local filesystem configuration
    local:
      # Output directory for carbon reports
      upload_path: "./output"
```

To run the example, navigate to the `example-data/` directory and execute the following command:

```bash
cd example-data/
carbon-daemon
```
