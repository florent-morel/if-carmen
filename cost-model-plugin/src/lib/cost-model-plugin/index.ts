import {PluginFactory} from '@grnsft/if-core/interfaces';
import {PluginParams, ConfigParams} from '@grnsft/if-core/types';
import { z } from 'zod';

export const CostModelPlugin = PluginFactory({
  configValidation: (config: ConfigParams) => {
    if (!config || !Object.keys(config)?.length) {
      throw new Error('Missing or empty configuration.');
    }

    const configSchema = z.object({
      'input-parameters': z.array(z.string()),
      'output-parameters': z.array(z.string()),
    });

    return validate<z.infer<typeof configSchema>>(configSchema, config);
  },
  inputValidation: (input: PluginParams, config: ConfigParams) => {
    const inputParameters = config['input-parameters'];

    const inputData = inputParameters.reduce(
      (acc: {[x: string]: any}, param: string | number) => {
        acc[param] = input[param];

        return acc;
      },
      {} as Record<string, number>
    );

    const validationSchema = z.record(z.string(), z.number());

    return validate(validationSchema, inputData);
  },
  implementation: async (inputs: PluginParams[], config: ConfigParams) => {
    const { 'input-parameters': _inputParameters } = config;

    return inputs.map(input => {
      // Define input parameters
      const computeEnergy = input['compute-energy'];
      const storageEnergy = input['storage-energy'];
      const computeEmbodied = input['compute-embodied'];
      const storageEmbodied = input['storage-embodied'];
      const computeCost = input['compute-cost'];
      const storageCost = input['storage-cost'];
      const servicesCost = input['services-cost'];
      const carbonIntensity = input['carbon-intensity'];

      // Calculate the outputs
      const servicesEnergyValue = servicesCost * (0.75 * (computeEnergy / computeCost) + 0.25 * (storageEnergy / storageCost));

      const servicesOperationalValue = servicesEnergyValue * carbonIntensity;

      const servicesEmbodiedValue = servicesCost * (0.75 * (computeEmbodied / computeCost) + 0.25 * (storageEmbodied / storageCost));


      return {
        ...input,
        "services-energy": servicesEnergyValue,
        "services-operational": servicesOperationalValue,
        "services-embodied": servicesEmbodiedValue,
      };
    });
  },
});

function validate<T>(schema: z.ZodTypeAny, data: unknown): T {
  const result = schema.safeParse(data);
  if (!result.success) throw new Error(result.error.message);
  return result.data as T;
}
