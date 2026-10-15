# Configuration

This file documents all possible configuration options for running Carmen.

`CARMEN_ROOT` refers to the installation path of Carmen.

The default configuration path is `CARMEN_ROOT/etc/config/config.yaml` when running from `CARMEN_ROOT`. When running the daemon, you can override it with `--carmen-config-filepath PATH` or the `CARMEN_CONFIG_FILEPATH` environment variable. If both are set, the command-line path takes precedence.

## Carmen Daemon configuration

This section explains the configuration structure for the Carmen daemon and details the configuration files content.

TODO: Review this list
### Configuration files directory structure

The daemon reads input files from `carmen_daemon.source.input_path` in the main configuration file.

The configuration files are organized as follows:
```
CARMEN_ROOT/etc/config/
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
- Configuration settings for Carmen API (see [Carmen as a Service](carmen-as-a-service.md) for more information).
- Input folder path.
- Output folder path.
- List of processors to run.
    - Can be selected from the following list of supported processors:
        * Processor_Compute: Virtual Machine, pod, etc.
        * Processor_Storage: Storage services.
        * Processor_Misc_Services: All other services.
    - Defaults to Processor_Compute.

#### CARMEN_ROOT/etc/sample_data/config-test.yaml

This file follows the same structure as `config.yaml` and is used by pytest.
Carbon intensity and PUE defaults are loaded separately from the carbon-values configuration for both files.

### Default Carbon values

This file defines several carbon computation related values.
By default, it is located in `CARMEN_ROOT/etc/config/modelling_constants/carbon_values.yaml` when running from `CARMEN_ROOT`. When running the daemon, you can select another file with `--carmen-carbon-values-filepath PATH` or the `CARMEN_CARBON_VALUES_FILEPATH` environment variable. If both are set, the environment variable takes precedence.
These are common to all providers.

Carmen looks up each CSV `Region` in the `regions` mappings of the loaded provider configurations. The matching entry identifies a location, whose intensity is read from `carbon_intensity_by_location` in `etc/config/modelling_constants/carbon_values.yaml`. For example, `eastus` maps to `United_States`, with an intensity of `384 gCO2e/kWh`. If the region or location is not mapped, Carmen uses `default_carbon_intensity`. To support a new region, configure both its region-to-location mapping and the location's intensity.

It also defines the embodied storage values for the following technologies:
- HDD (Hard Drive Disks)
- SSD (Solid State Disks)
- A default value is provided in case the disk technology is unknown.

#### Providers configuration folder

This folder stores cloud providers specific configurations.
By default, this folder is located in `CARMEN_ROOT/etc/config/modelling_constants/providers/cloud_providers` when running from `CARMEN_ROOT`. When running the daemon, you can select another folder with `--carmen-provider-config-filepath PATH` or the `CARMEN_PROVIDER_CONFIG_FILEPATH` environment variable. If both are set, the environment variable takes precedence.

##### Cloud providers configuration folders

This folder stores subfolders dedicated to implemented cloud providers.
In each implemented subfolder, one will find :
- %provider%.yaml : defines constants related to
  - Power Usage Effectiveness ratio (PUE).
  - Mapping between Azure defined regions and carbon intensity values defined in carbon_values.yaml.
  - Electricity ratios: energy consumption of different resources.
- %provider%_instances.csv : dataset extracted from GSF's if-data containing hardware instances data per virtual machine type.

##### Local configuration folder

Same as above, except it is dedicated to non-CSP configuration.

## Configuration example

The main configuration must contain at least one of `carmen_api` or `carmen_daemon`. You can configure the API, the daemon, or both.

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
    input_path: "etc/sample_data/vm-metrics"

  # Output directory for carbon reports
  output:
    output_path: "./output"
  # TODO document properly below
  orchestrator:
    list_processors:
      - Processor_Compute
```


## Configuration examples path


Configuration examples can be found in CARMEN_ROOT/etc/sample_data or in the [E2E tests](../backend/tests/daemon/end_to_end/test_e2e_multi_resources/success/test_e2e_vm_storage_misc_services_single_provider_azure/test_data/config/config.yaml)
