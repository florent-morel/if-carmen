# TODO


## 2026-09-11 14:15:08

- [ ] 100% success UT.
- [ ] E2E UT covering aggregated:
    - [ ] 3 resources success.
    - [ ] failures cases.
- [ ] Review all TODOs.
- [ ] Review & remove if possible commented code (or put it in vNext/v1).
- [ ] Review all documentation.
- [ ] Documentation: explain sample data in tests folders.
- [ ] Review changelog.
- [ ] Review & centralize vNext in [[changelog.md]].
- [ ] Fix gitignore of tests output.
- [ ] Review log level in log files.

- [ ] Build next steps -> Project with GSF.


## Code implem

### Features

vNext:

TODO|1 - Implement embodied emissions TE retrieved from config file per instance_type
TODO|2 - Configure and propagate output/generated folders for IF files dir (hardcoded as IF_FILES_DIR in Constants).
TODO|3 - Resolve carbon intensity using the resource's Provider-specific region mapping, not the first matching region across all providers.
    Today, the readers record Provider, but call PaasCiMapper.calculate_ci with Region only... The mapper scans every provider’s region map and takes the FIRST match.

    For example, suppose both Azure and AWS configure the same code for a different region: Azure maps it to the Netherlands (253 gCO₂/kWh), while AWS maps it to France (44 gCO₂/kWh). An AWS resource in that region using 10 kWh should produce 440 gCO₂. If Azure’s mapping is encountered first, the current lookup would use 2,530 gCO₂ instead.

    Low risk, but conflict may arise in the future.
TODO|4 - Fail storage computation explicitly when a configured provider has no mapping for a resource's StorageReplicationType.
TODO|5 - Misc-services computation: Set weights used in ratio calculation as configurable input with a default value.
TODO|6 - Misc-services computation: Move ratio calculation into IF. Include the raw compute/storage totals in the manifest and expose intermediate ratios, so the manifest explains the impact without Python logs.

## Documentation

> [!IMPORTANT]
> Add the fact that input files should be mono currency.

### Changelog

### Review documentation, examples


Configuration architecture: 

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
