# Configuration

This file documents all possible configuration options for running Carmen.

`CARMEN_ROOT` refers to the installation path of Carmen.

The default configuration path is `CARMEN_ROOT/etc/config/config.yaml`, but can be overridden through the `CARMEN_CONFIG_FILEPATH` environment variable.

## Carmen Daemon configuration

This section explains the configuration structure for the Carmen daemon and details the configuration files content.

TODO: Review this list
### Input files directory structure

Carmen daemon reads input files from a directory configured in main config file located in `CARMEN_ROOT/etc/config/config.yaml`.

The configuration directory structure is the following:
```
CARMEN_ROOT/etc/config/
├── config-test.yaml
├── config.yaml
└── modelling_constants
    ├── carbon_values.yaml
    └── providers
        ├── cloud_providers
        │   ├── aws
        │   │   └── aws.yaml
        │   ├── azure
        │   │   ├── azure_instances.csv
        │   │   └── azure.yaml
        │   └── gcp
        │        └── gcp.yaml
        └── local
            └── local.yaml
```

### Carmen main configuration file

This is Carmen's main configuration file.
It is located in CARMEN_ROOT/etc/config/config.yaml.

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

#### CARMEN_ROOT/etc/config/config-test.yaml

This file is following the same structure as config.yaml.
It is used for Unit Tests only.

### Default Carbon values

This file defines several carbon computation related values.
It is located in CARMEN_ROOT/etc/config/modelling_constants/carbon_values.yaml.
These are common to all providers.

Carmen looks up each CSV `Region` in the `regions` mappings of the loaded provider configurations. The matching entry identifies a location, whose intensity is read from `carbon_intensity_by_location` in `etc/config/modelling_constants/carbon_values.yaml`. For example, `eastus` maps to `United_States`, with an intensity of `384 gCO2e/kWh`. If the region or location is not mapped, Carmen uses `default_carbon_intensity`. To support a new region, configure both its region-to-location mapping and the location's intensity.

It also defines the embodied storage values for the following technologies:
- HDD.
- SSD.
- A default value is provided in case the technology is unknown.

#### Providers configuration folder

This folder stores cloud providers specific configurations.
It is located in CARMEN_ROOT/etc/config/modelling_constants/providers/cloud_providers.

##### Azure Cloud Service Provider

This file is dedicated to Microsoft Azure Cloud Service Provider.
It is located in CARMEN_ROOT/etc/config/modelling_constants/providers/cloud_providers/azure/azure.yaml.

It defines constants related to:
- Power Usage Effectiveness ratio (PUE).
- Mapping between Azure defined regions and carbon intensity values defined in carbon_values.yaml.
- Electricity ratios: energy consumption of different resources.


###### Azure Cloud Service Provider - Instances configuration

CARMEN_ROOT/etc/config/modelling_constants/providers/cloud_providers/azure/azure_instances.csv

TODO: Explain what's in this file.

##### AWS Cloud Service Provider

It is located in CARMEN_ROOT/etc/config/modelling_constants/providers/cloud_providers/aws/aws.yaml.

Follows same structure. 
Not implemented yet.

##### GCP Cloud Service Provider

It is located in CARMEN_ROOT/etc/config/modelling_constants/providers/cloud_providers/gcp/gcp.yaml.

Follows same structure.  
Not implemented yet.


## Configuration example

TODO: review this file.
```yaml
# API Configuration (optional)
carmen_api:
  
  # REQUIRED: URL of the Thanos query service
  # Type: string
  thanos_url: "https://thanos.example.com"
  
  # OPTIONAL: Authentication method ("azure" or null)
  # Type: string | null
  # Default: null
  # If set to "azure", credentials must be provided
  authentication: "azure"
  
  # CONDITIONAL: Required when authentication is "azure"
  # Type: object | null
  credentials:
    # All three fields are required when credentials is set
    client_id: "${AZURE_CLIENT_ID}"
    client_secret: "${AZURE_CLIENT_SECRET}"
    tenant_id: "${AZURE_TENANT_ID}"
  
  # OPTIONAL: OAuth scope for authentication
  # Type: string | null
  # Default: null
  scope: "https://management.azure.com/.default"
  
  # REQUIRED: Labels used to filter metrics
  # Type: dict[string, string]
  external_labels:
    cluster: "production"
    environment: "prod"
    region: "us-west-2"
  
  # OPTIONAL: Verify SSL certificates
  # Type: boolean
  # Default: true
  verify_ssl: true
  
  # OPTIONAL: Kubernetes label configuration
  # Type: object
  # All fields have defaults
  labels:
    app_label: "app.kubernetes.io/name"  # Default: "label_app_kubernetes_io/part-of"
    cluster_label: "cluster"              # Default: "stack"
    pod_label: "pod"                      # Default: "pod"
    namespace_label: "namespace"          # Default: "namespace"


# Daemon Configuration (optional)
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


## Configuration examples path


Configuration examples can be found in CARMEN_ROOT/etc/sample_data.
