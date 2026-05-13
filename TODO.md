## Code implem

### Config

V1: Configure and propagate output/generated folders for IF files, CSV reports...

### Orchestrator

V1: Make E2E test with sample data
-- Includes VM, storage, services

### UTs

100% fix

### Features

V1: 
- Implement missing regions/providers for storage and services
- Validate storage and services computation
- Implement default storage & VMs energy & carbon cost ratios. (should be configurable).
 
Vnext: 
- Implement embodied emissions TE retrieved from config file per instance_type

## Documentation

### Changelog

### Review documentation, examples

``` sh
if-carmen/
├── backend
├── docs
├── etc
│   ├── config
│   │   ├── config.yaml
│   │   └── modelling_constants
│   │       ├── carbon_values.yaml
│   │       └── cloud_providers
│   ├── impact_framework
│   │   ├── generated
│   │   └── templates
│   ├── report
│   └── sample_data
│       └── config-test.yaml

```
