# Configuration

This file documents all possible configuration options for running Carmen.
The default configuration path is `config/config.yaml`, but can be overriden through the `CARMEN_CONFIG_FILEPATH` environment variable.

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
  infrastructure_providers:
    - azure
```
