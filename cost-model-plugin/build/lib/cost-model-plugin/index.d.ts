import { PluginParams, ConfigParams } from '@grnsft/if-core/types';
export declare const CostModelPlugin: (config: ConfigParams | undefined, parametersMetadata: import("@grnsft/if-core/types").PluginParametersMetadata, mapping: import("@grnsft/if-core/types").MappingParams) => {
    metadata: {
        inputs: {
            [x: string]: {
                description: string;
                unit: string;
                "aggregation-method": import("@grnsft/if-core/types").AggregationOptions;
            };
        };
        outputs: import("@grnsft/if-core/types").ParameterMetadata;
    };
    execute: (inputs: PluginParams[]) => Promise<{
        [x: string]: any;
    }[]>;
};
