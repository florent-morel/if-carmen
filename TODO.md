

## Finalize workflow

- Orchestrator.
- Reader.
- Runner.
- Writer.

### Orchestrator

- main: Read list of processors & DaemonConfig from settings.

### Reader

### Runner

### Writer

- Build CSV columns and data depending on listed processors.

Output CSV example:
| Resource | VM Energy| Total Energy | Total CO2 |
| --- | --- | --- | ---|
| abc | 560 | 560 | 2500 |

| Resource | VM Energy | Storage energy | Total Energy | Total CO2 |
| --- | --- | --- | --- | ---|
| abc | 560 | 100 | 660 | 2500 |
Algo:
- writer-0: based on CarbonDaemonResult.
    - Csv file structure (=add columns to be output regardless number of processors - aka total columns).
    - "pre-processors columns".
    - "post-processors columns".
- writer-i: based on ResourceTypeResult.
    - columns dedicated to this resource.

### Fixing UTs

## Implement Cost use case.

- Dedicated Reader, Runner.
- Adapt Writer.
- From Berkay's PR.

## Fixes


- calculate_vm_count_for_missing_regions -> it applies to any resource.
- remove THANOS: ThanosConfig
