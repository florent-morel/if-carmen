# Changelog

## Latest Release - yyyy-mm-dd

## Unreleased - 2026-10-14

TODO: To be moved in [[#Latest Release - yyyy-mm-dd]] once ready to release.

### Summary

#### Carmen refined scope

This release clarifies Carmen scope which can now be summarized like this:
- [Carmen](https://greensoftware.foundation/tools/carmen/) is computing CO2 impact of your infrastructure thanks to the [GSF's Impact Framework](https://if.greensoftware.foundation/).
- It takes in input one or more CSV files and will output a CSV file both located on local file system (path is configurable, see [[configuration]] for more information).
- It is up to Carmen's administrator to retrieve and convert their infrastructure data into Carmen daemon's input file format.
    - See [[carmen-daemon#Expected Source File Format]] for more information.
- It is up to Carmen's administrator to export and convert the output for further usage (UI, dashboards...).

- This release enables Carmen to be platform/environment agnostic: one can choose to run Carmen to measure CO2 impact of bare-metal servers, on-premise data center, Cloud deployed infrastructure, a mix of all, etc.

To properly compute CO2 impact (and fill the IF Manifest file), Carmen needs to include functional and technical values related to models, machine lifespan, Carbon intensity, etc.
- Some of these settings are generic and provided in Carmen's main configuration file (see [[configuration#Carmen main configuration file]] for more information).
- Some are provider specific and are defined in provider specific configuration file (see [[configuration#Providers configuration folder]] for more information).
- Current supported Cloud Provider: Microsoft Azure.

### Added

#### v1.0 Daemon: New functional computations

On top of Compute (VM...) resources, Carmen now supports: 
- Storage services impact thanks to the IF.
- Miscellaneous services impact thanks to the IF. See [[methodology#Miscellaneous Services Pipeline]] for more information on how the impact of these services is computed.

#### v1.0 Daemon: New technical architecture

The Carbon Orchestrator class handles the overall flow, calling in sequence a Processor class dedicated to a given resource.

The Processor wraps the sequencing of the following classes:
- Reader: read Carmen input file.
- Runner: encode IF input file and call the IF thanks to models.
- Writer: write Carmen output file.

Each of these classes are implementation of their respective Abstract class.


#### v1.0 Daemon: Multi-Cloud Provider Support

Carmen architecture now supports Multi-Cloud Provider variables such as regions, energy ratios, PUE, etc.
- A "Provider" column is present in Carmen input file. This means that each resource can come from a distinct provider.
- Current implementation supports "local" infrastructure (aka on-premise) and Microsoft Azure.
- To add a new CSP, one needs to fill dedicated configuration in (see [[configuration#Providers configuration folder]]).

#### v1.0 Moving variables to configuration files

- Load functional configuration to configuration files.
- Cloud Service Provider specific configuration in dedicated configuration file.

### Changed
- "Provider" column in Carmen input file.

### Deprecated

### Removed

- v1.0 Download input file from an Azure blob storage as it was specific to Amadeus' environment. See Summary section.
- v1.0 Upload output file to an Azure blob storage as it was specific to Amadeus' environment. See Summary section.
- TODO: removed useless columns in azure_instances.csv

### Fixed

### Security


## Unreleased



## Future features




Note: changelog file written following [https://common-changelog.org/] guidelines.
