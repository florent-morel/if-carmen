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

- Implement embodied emissions TE retrieved from config file per instance_type
- Configure and propagate output/generated folders for IF files dir (hardcoded as IF_FILES_DIR in Constants).

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
