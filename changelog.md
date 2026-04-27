

## Unreleased

### Carmen refined scope

This release clarifies Carmen scope which can now be summarized like this:
- Carmen is computing CO2 impact of your infrastructure thanks to the GSF's Impact Framework.
- It takes in input a CSV file and will output a CSV file both located on local file system (path is configurable).
- It is up to Carmen's DevOps teams to convert their infrastructure data in Carmen's input file.
- It is up to Carmen's DevOps teams to convert the output in a graphical interface.

- This release enables Carmen to be platform/environment agnostic: one can chose to run Carmen to measure bare-metal servers, own-premise data center, Cloud deployed infrastructure, a mix of both, etc.

- To properly compute CO2 impact (and fill the IF Manifest file), Carmen needs to include functional values related to models, machine lifespan, Carbon intensity, etc.
- Some of these settings are generic and provided in Carmen's main configuration file.
- Some are provider specific (especially Cloud Service Provider) and are defined in provider specific configuration file.
- Current supported Cloud Provider: Microsoft Azure.


### Removed

- vX.Y Download from Azure as it was specific to Amadeus' environment.
- vX.Y Upload to Azure as it was specific to Amadeus' environment.
- vX.Y 
- vX.Y 
- vX.Y 
- vX.Y 
- vX.Y 

### Added

#### vX.Y New functional computations
- Storage services impact computed thanks to the IF.
- Miscellaneous services impact computed thanks to the IF.

#### vX.Y New technical architecture
- Carbon Orchestrator handles the overall flow, calling in sequence classes dedicated to a given resource:
    * Reader: reading input file.
    * Runner: calling the IF thanks to models.
    * Writer: writing output file.

#### vX.Y Moving variables to configuration files
- Load functional configuration from conf files.
- Cloud Service Provider specific configuration in dedicated conf file.

## vX.Y - 1


