# Changelog

## Unreleased - 2026-04-27

### Summary

Carmen refined scope

This release clarifies Carmen scope which can now be summarized like this:
- [Carmen](https://greensoftware.foundation/tools/carmen/) is computing CO2 impact of your infrastructure thanks to the [GSF's Impact Framework](https://if.greensoftware.foundation/)
- It takes in input a CSV file and will output a CSV file both located on local file system (path is configurable).
- It is up to Carmen's administrator to retrieve and convert their infrastructure data into Carmen daemon's input file. TODO: See [[carmen-daemon#Expected Source File Format]] for more information.
- It is up to Carmen's administrator to export and convert the output for further usage (UI...).

- This release enables Carmen to be platform/environment agnostic: one can choose to run Carmen to measure CO2 impact of bare-metal servers, on-premise data center, Cloud deployed infrastructure, a mix of all, etc. TODO: create a local.yaml for on-premise

- To properly compute CO2 impact (and fill the IF Manifest file), Carmen needs to include functional and technical values related to models, machine lifespan, Carbon intensity, etc.
- Some of these settings are generic and provided in Carmen's main configuration file (TODO: provide main conf file path here).
- Some are provider specific and are defined in provider specific configuration file (TODO: provide specific conf file path here).
- Current supported Cloud Provider: Microsoft Azure.

### Added

#### vX.Y Daemon: New functional computations
On top of Compute (VM...) resources, Carmen now supports: 
- Storage services impact thanks to the IF.
- Miscellaneous services impact thanks to the IF. TODO: add link to doc for misc services.

#### vX.Y Daemon: New technical architecture
- Carbon Orchestrator handles the overall flow, calling in sequence classes dedicated to a given resource:
    * Reader: read Carmen input file.
    * Runner: encode IF input file and call the IF thanks to models.
    * Writer: write Carmen output file.

#### vX.Y Daemon: Multi-Cloud Provider Support
- Carmen architecture now supports Multi-Cloud Provider variables such as regions, energy ratios, PUE, etc.
- A "Provider" column is present in Carmen input file. This means that each resource can come from a distinct provider.
- Current implementation supports "local" infrastructure (aka on-premise) and Microsoft Azure.
- To add a new CSP, one needs to fill dedicated configuration in (TODO: provide specific conf file path here).

#### vX.Y Moving variables to configuration files
- Load functional configuration from conf files.
- Cloud Service Provider specific configuration in dedicated conf file.

### Changed
- "Provider" column in Carmen input file.

### Deprecated

### Removed

- vX.Y Download input file from an Azure blob storage as it was specific to Amadeus' environment. See Summary section.
- vX.Y Upload output file to an Azure blob storage as it was specific to Amadeus' environment. See Summary section.

### Fixed

### Security

Note: changelog file written following [https://common-changelog.org/] guidelines.
