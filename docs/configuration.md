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
  
  # CONDITIONAL: Azure credentials (shared between source and upload)
  # Type: object
  # Required when source.type="azure" OR upload.type="azure"
  credentials:
    # All three fields required when using Azure
    client_id: "${DAEMON_CLIENT_ID}"
    client_secret: "${DAEMON_CLIENT_SECRET}"
    tenant_id: "${AZURE_TENANT_ID}"
  
  # Data source configuration
  source:
    
    # OPTIONAL: Source type ("azure" or "local")
    # Type: string
    # Default: "local"
    type: "azure"
    
    # REQUIRED: List of files to process
    # Type: list[string]
    # Must not be empty
    file_names:
      - "carbon_metrics_2024.csv"
      - "emissions_data.csv"
      - "energy_consumption.csv"
    
    # CONDITIONAL: Required when type="azure"
    azure:
      # REQUIRED: Azure Storage account URL (must start with https://)
      # Type: string | null
      storage_account_url: "https://carbonstorage.blob.core.windows.net"
      
      # REQUIRED: Container name to read from
      # Type: string | null
      container_name_read: "carbon-data-input"
    
    # CONDITIONAL: Required when type="local"
    local:
      # REQUIRED: Directory path for input files
      # Type: string | null
      input_path: "/var/data/carbon-engine/input"
  
  # Upload destination configuration
  upload:
    
    # OPTIONAL: Upload type ("azure" or "local")
    # Type: string
    # Default: "local"
    type: "azure"
    
    # CONDITIONAL: Required when type="azure"
    azure:
      # REQUIRED: Container name for uploads
      # Type: string | null
      container_name_upload: "carbon-reports-output"
      
      # OPTIONAL: Custom blob name pattern
      # Type: string | null
      blob_name: "report_{timestamp}.html"
    
    # CONDITIONAL: Required when type="local"
    local:
      # REQUIRED: Directory path for output reports
      # Type: string | null
      output_path: "/var/data/carbon-engine/output"
```
