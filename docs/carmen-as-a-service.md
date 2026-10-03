# Carmen as a Service

Carmen can be deployed as a containerized application which is tightly coupled with a prometheus instance in your kubernetes cluster.

It provides an API which allows you to query for different carbon emissions and energy consumption metrics per application/service.

Before setting up Carmen, ensure that your monitoring environment meets its requirements. Carmen relies on Kubernetes labels to identify resources and map their relationships within the cluster.

Each pod in your Kubernetes setup should include the following labels:

- A label that uniquely identifies the pod.
- A label that identifies the application or service the pod belongs to.
- A label that identifies the cluster the pod is part of.
- A label that identifies the namespace the pod belongs to.

Additionally, you must define a Prometheus rule named `pod:container_cpu_usage:sum` to monitor CPU usage across containers in the cluster.

In most production environments, these configurations are typically available. The following section demonstrates how to configure them manually in a local environment for testing purposes.

### Deploying Kube Prometheus Stack

Make sure you have Helm installed, and that you have access to a Kubernetes cluster.

1. Define a `values.yaml` file:

```yaml
   kube-state-metrics:
     metricLabelsAllowlist:
       - "pods=[*]"
       - "namespaces=[*]"
     prometheus:
       monitor:
         relabelings:
           - sourceLabels: [__meta_kubernetes_node_label_cluster_name]
             targetLabel: cluster
             action: replace
           - targetLabel: cluster
             replacement: "production"
             action: replace

   kubelet:
     enabled: true
     serviceMonitor:
       cAdvisor: true
       cAdvisorMetricRelabelings:
         - targetLabel: cluster
           replacement: "production"
           action: replace

   additionalPrometheusRulesMap:
     recording-rules.yaml:
       groups:
         - name: pod_cpu_aggregation
           interval: 30s
           rules:
             - record: pod:container_cpu_usage:sum
               expr: |
                 sum by (cluster, namespace, pod) (
                   rate(container_cpu_usage_seconds_total{container!="",container!="POD"}[5m])
                 )
```

2. Deploy the Kube Prometheus Stack using Helm with your `values.yaml`:

   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   helm install kube-prometheus-stack --create-namespace --namespace kube-prometheus-stack prometheus-community/kube-prometheus-stack -f values.yaml
   ```

3. Verify the deployment:

   ```bash
   kubectl get pods -n kube-prometheus-stack
   ```

### Running Carmen's Service
1. Write your carmen configuration file under the name `config.yaml`, where you define the querier endpoint and your label names:
```yaml
carmen_api:
  # The URL of the querier endpoint where Prometheus queries will be sent.
  thanos_url: http://localhost:9090
  provider: azure

  # The authentication method used to access the Prometheus/Thanos API.
  # Supported values can include: 'azure', 'none'.

  labels:
    app_label: "service" # Label representing the application name.
    cluster_label: "cluster" # Label representing the cluster or environment.
    pod_label: "pod" # Label representing the pod name.
    namespace_label: "namespace" # Label representing the Kubernetes namespace.`
```
You can refer to the configuration section of the documentation for more details.

2. Run the carmen service:
```
carbon-engine

[2025-10-28 23:22:46] INFO:backend.src.core.settings:Settings validated.
[2025-10-28 23:22:46] INFO:backend.src.core.yaml_config_loader:configuration loaded successfully from: config.yaml
[2025-10-28 23:22:46] INFO:backend.src.common.exception_handler:Exception handlers registered successfully
[2025-10-28 23:22:46] INFO:backend.src.main:Running Fast API application.
INFO:     Started server process [791793]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

You can access the swagger UI at http://localhost:8000/api/docs.

### How it works ?

As soon as Carmen receives a request, it queries the configured Prometheus instance to retrieve relevant telemetry data, mainly CPU and memory usage. For this reason, your monitoring stack must include both kube state metrics and cAdvisor to ensure these metrics are available. After retrieving the data, Carmen generates the required manifest files, runs the Impact Framework, parses the resulting files, and returns the processed response.
You can refer to the methodology section of the documentation for more details on the calculation models used.
The figure below summarizes the flow:

<p align="center">
  <img src="./static/carmen-as-a-service.drawio.svg" alt="Carmen as a Service local demo" width="1920">
</p>

### Apps Endpoint 

The `/apps` endpoint allows you to retrieve the names of resources associated with a specific cluster.

```bash 
curl -X 'GET' \
  'http://localhost:8000/api/apps/?paas=production' \
  -H 'accept: application/json'
```

Response: 
```json
{
  "namespaces": [
    "kube-system",
    "kube-node-lease",
    "kube-public",
    "kube-prometheus-stack",
    "default"
  ]
}
```

### Run-Engine Endpoint
Access the run-engine endpoint to collect granular metrics on your cluster’s carbon footprint and energy consumption.

```bash
curl -X 'GET' \
  'http://localhost:8000/api/apps/run-engine/?sampling=1h&paas=production&emission_breakdown=false' \
  -H 'accept: application/json'
```

The default query window is the last three hours. Set emission_breakdown=true to return metrics for each pod instead of aggregated cluster totals.

Response: 
```json
[
  {
    "id": "0",
    "name": "production",
    "energy_consumed": [
      0.0015,
      0.0015,
      0.0015,
      0.0015
    ],
    "carbon_operational": [
      0.4277,
      0.433,
      0.4326,
      0.4316
    ],
    "carbon_embodied": [
      0.9031,
      0.9031,
      0.9031,
      0.9031
    ],
    "carbon_emitted": [
      1.3308,
      1.3361,
      1.3357,
      1.3347
    ],
    "time_points": [
      "2025-10-29T18:40:43",
      "2025-10-29T19:40:43",
      "2025-10-29T20:40:43",
      "2025-10-29T21:40:43"
    ],
    "total_energy_consumed": 0.0061,
    "total_carbon_operational": 1.7249,
    "total_carbon_embodied": 3.6124,
    "total_carbon_emitted": 5.3373,
    "cpu_energy": [
      0.0009,
      0.0009,
      0.0009,
      0.0009
    ],
    "memory_energy": [
      0.0004,
      0.0004,
      0.0004,
      0.0004
    ],
    "cpu_power": [
      0.0009,
      0.0009,
      0.0009,
      0.0009
    ],
    "requested_cpu": [
      1.25,
      1.25,
      1.25,
      1.25
    ],
    "cpu_util": [
      0.0589160886868118,
      0.06278529203378494,
      0.06187297998171409,
      0.060484402949900096
    ],
    "storage_capacity": [],
    "network_io": [],
    "requested_memory": [
      1008730112,
      1008730112,
      1008730112,
      1008730112
    ],
    "total_cpu_energy": 0.0036,
    "total_memory_energy": 0.0016,
  }
]
```

You can also query specific applications within the cluster. In this case, the query retrieves metrics for the pods deployed for that application, ideal for development teams who want visibility into their application’s emissions: 

```bash
curl -X 'GET' \
  'http://localhost:8000/api/apps/run-engine/?sampling=1h&app=kube-prometheus-stack-kube-state-metrics&paas=production&emission_breakdown=false' \
  -H 'accept: application/json'
```

### Run-Hardware Endpoint
The run-hardware endpoint returns metrics for a hardware resource operating over a specified duration.   
This endpoint is particularly useful for testing and benchmarking virtual machines, physical servers, or cloud resources before deploying workloads in production.   
The endpoint supports a variety of query parameters, such as virtual_machine-type, cpu-load, storage-size, and duration. The following curl command runs a simulation on a Standard_E16as_v4 virtual machine with 30% CPU load, 4 GB storage, for 60 seconds
```bash
curl -X 'GET' \
  'http://localhost:8000/api/hardware/run-engine-hardware/?virtual_machine-type=Standard_E16as_v4&cpu-load=30&storage-size=4&duration=60' \
  -H 'accept: application/json'
```

