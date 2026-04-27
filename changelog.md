# Changelog

## Unreleased - 2026-04-27

### Carmen refined scope

This release clarifies Carmen scope which can now be summarized like this:
- Carmen is computing CO2 impact of your infrastructure thanks to the GSF's Impact Framework.
- It takes in input a CSV file and will output a CSV file both located on local file system (path is configurable).
- It is up to Carmen's DevOps teams to convert their infrastructure data in Carmen's input file.
- It is up to Carmen's DevOps teams to convert the output in a graphical interface.

- This release enables Carmen to be platform/environment agnostic: one can chose to run Carmen to measure bare-metal servers, own-premise data center, Cloud deployed infrastructure, a mix of both, etc.

- To properly compute CO2 impact (and fill the IF Manifest file), Carmen needs to include functional values related to models, machine lifespan, Carbon intensity, etc.
- Some of these settings are generic and provided in Carmen's main configuration file (TODO: provide main conf file path here).
- Some are provider specific (especially Cloud Service Provider) and are defined in provider specific configuration file (TODO: provide specific conf file path here).
- Current supported Cloud Provider: Microsoft Azure.

### Added

#### vX.Y New functional computations
- Compute storage services impact thanks to the IF.
- Compute miscellaneous services impact thanks to the IF.

#### vX.Y New technical architecture
- Carbon Orchestrator handles the overall flow, calling in sequence classes dedicated to a given resource:
    * Reader: reading Carmen input file.
    * Runner: calling the IF thanks to models.
    * Writer: writing output file.

#### Multi-Cloud Provider Support
- Carmen architecture now supports Multi-Cloud Provider variables such as regions, energy ratios, pue, etc.
- A "Provider" column is present in Carmen input file. This means that each provided resource can come from a distinct infrastructure.
- Current implementation only supports Microsoft Azure.
- To add a new CSP, one needs to fill dedicated configuration in (TODO: provide specific conf file path here).

#### vX.Y Moving variables to configuration files
- Load functional configuration from conf files.
- Cloud Service Provider specific configuration in dedicated conf file.

### Changed

### Deprecated

### Removed

- vX.Y Download from Azure as it was specific to Amadeus' environment.
- vX.Y Upload to Azure as it was specific to Amadeus' environment.
- vX.Y 
- vX.Y 
- vX.Y 
- vX.Y 
- vX.Y 

### Fixed

### Security


## vX.Y - 1

Note: changelog file written following [https://common-changelog.org/] guidelines.
