"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MiscServicesModelPlugin = void 0;
const interfaces_1 = require("@grnsft/if-core/interfaces");
const zod_1 = require("zod");
exports.MiscServicesModelPlugin = (0, interfaces_1.PluginFactory)({
    configValidation: (config) => {
        if (!config || !Object.keys(config)?.length) {
            throw new Error('Missing or empty configuration.');
        }
        const configSchema = zod_1.z.object({
            'input-parameters': zod_1.z.array(zod_1.z.string()),
            'output-parameters': zod_1.z.array(zod_1.z.string()),
        });
        return validate(configSchema, config);
    },
    inputValidation: (input, config) => {
        const inputParameters = config['input-parameters'];
        const inputData = inputParameters.reduce((acc, param) => {
            acc[param] = input[param];
            return acc;
        }, {});
        const validationSchema = zod_1.z.record(zod_1.z.string(), zod_1.z.number());
        return validate(validationSchema, inputData);
    },
    implementation: async (inputs, config) => {
        const { 'input-parameters': _inputParameters } = config;
        return inputs.map(input => {
            const cost = input['cost'];
            const carbonIntensity = input['carbon-intensity'];
            const energyCostRatio = input['energy-cost-ratio'];
            const embodiedCostRatio = input['embodied-cost-ratio'];
            const miscServicesEnergyValue = cost * energyCostRatio;
            const miscServicesOperationalValue = miscServicesEnergyValue * carbonIntensity;
            const miscServicesEmbodiedValue = cost * embodiedCostRatio;
            return {
                ...input,
                "misc-services-energy": miscServicesEnergyValue,
                "misc-services-operational": miscServicesOperationalValue,
                "misc-services-embodied": miscServicesEmbodiedValue,
            };
        });
    },
});
function validate(schema, data) {
    const result = schema.safeParse(data);
    if (!result.success)
        throw new Error(result.error.message);
    return result.data;
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW5kZXguanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvbGliL21pc2Mtc2VydmljZXMtbW9kZWwtcGx1Z2luL2luZGV4LnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7OztBQUFBLDJEQUF5RDtBQUV6RCw2QkFBd0I7QUFFWCxRQUFBLHVCQUF1QixHQUFHLElBQUEsMEJBQWEsRUFBQztJQUNuRCxnQkFBZ0IsRUFBRSxDQUFDLE1BQW9CLEVBQUUsRUFBRTtRQUN6QyxJQUFJLENBQUMsTUFBTSxJQUFJLENBQUMsTUFBTSxDQUFDLElBQUksQ0FBQyxNQUFNLENBQUMsRUFBRSxNQUFNLEVBQUUsQ0FBQztZQUM1QyxNQUFNLElBQUksS0FBSyxDQUFDLGlDQUFpQyxDQUFDLENBQUM7UUFDckQsQ0FBQztRQUVELE1BQU0sWUFBWSxHQUFHLE9BQUMsQ0FBQyxNQUFNLENBQUM7WUFDNUIsa0JBQWtCLEVBQUUsT0FBQyxDQUFDLEtBQUssQ0FBQyxPQUFDLENBQUMsTUFBTSxFQUFFLENBQUM7WUFDdkMsbUJBQW1CLEVBQUUsT0FBQyxDQUFDLEtBQUssQ0FBQyxPQUFDLENBQUMsTUFBTSxFQUFFLENBQUM7U0FDekMsQ0FBQyxDQUFDO1FBRUgsT0FBTyxRQUFRLENBQStCLFlBQVksRUFBRSxNQUFNLENBQUMsQ0FBQztJQUN0RSxDQUFDO0lBQ0QsZUFBZSxFQUFFLENBQUMsS0FBbUIsRUFBRSxNQUFvQixFQUFFLEVBQUU7UUFDN0QsTUFBTSxlQUFlLEdBQUcsTUFBTSxDQUFDLGtCQUFrQixDQUFDLENBQUM7UUFFbkQsTUFBTSxTQUFTLEdBQUcsZUFBZSxDQUFDLE1BQU0sQ0FDdEMsQ0FBQyxHQUF1QixFQUFFLEtBQXNCLEVBQUUsRUFBRTtZQUNsRCxHQUFHLENBQUMsS0FBSyxDQUFDLEdBQUcsS0FBSyxDQUFDLEtBQUssQ0FBQyxDQUFDO1lBRTFCLE9BQU8sR0FBRyxDQUFDO1FBQ2IsQ0FBQyxFQUNELEVBQTRCLENBQzdCLENBQUM7UUFFRixNQUFNLGdCQUFnQixHQUFHLE9BQUMsQ0FBQyxNQUFNLENBQUMsT0FBQyxDQUFDLE1BQU0sRUFBRSxFQUFFLE9BQUMsQ0FBQyxNQUFNLEVBQUUsQ0FBQyxDQUFDO1FBRTFELE9BQU8sUUFBUSxDQUFDLGdCQUFnQixFQUFFLFNBQVMsQ0FBQyxDQUFDO0lBQy9DLENBQUM7SUFDRCxjQUFjLEVBQUUsS0FBSyxFQUFFLE1BQXNCLEVBQUUsTUFBb0IsRUFBRSxFQUFFO1FBQ3JFLE1BQU0sRUFBRSxrQkFBa0IsRUFBRSxnQkFBZ0IsRUFBRSxHQUFHLE1BQU0sQ0FBQztRQUV4RCxPQUFPLE1BQU0sQ0FBQyxHQUFHLENBQUMsS0FBSyxDQUFDLEVBQUU7WUFDeEIsTUFBTSxJQUFJLEdBQUcsS0FBSyxDQUFDLE1BQU0sQ0FBQyxDQUFDO1lBQzNCLE1BQU0sZUFBZSxHQUFHLEtBQUssQ0FBQyxrQkFBa0IsQ0FBQyxDQUFDO1lBQ2xELE1BQU0sZUFBZSxHQUFHLEtBQUssQ0FBQyxtQkFBbUIsQ0FBQyxDQUFDO1lBQ25ELE1BQU0saUJBQWlCLEdBQUcsS0FBSyxDQUFDLHFCQUFxQixDQUFDLENBQUM7WUFFdkQsTUFBTSx1QkFBdUIsR0FBRyxJQUFJLEdBQUcsZUFBZSxDQUFDO1lBRXZELE1BQU0sNEJBQTRCLEdBQUcsdUJBQXVCLEdBQUcsZUFBZSxDQUFDO1lBRS9FLE1BQU0seUJBQXlCLEdBQUcsSUFBSSxHQUFHLGlCQUFpQixDQUFDO1lBRzNELE9BQU87Z0JBQ0wsR0FBRyxLQUFLO2dCQUNSLHNCQUFzQixFQUFFLHVCQUF1QjtnQkFDL0MsMkJBQTJCLEVBQUUsNEJBQTRCO2dCQUN6RCx3QkFBd0IsRUFBRSx5QkFBeUI7YUFDcEQsQ0FBQztRQUNKLENBQUMsQ0FBQyxDQUFDO0lBQ0wsQ0FBQztDQUNGLENBQUMsQ0FBQztBQUVILFNBQVMsUUFBUSxDQUFJLE1BQW9CLEVBQUUsSUFBYTtJQUN0RCxNQUFNLE1BQU0sR0FBRyxNQUFNLENBQUMsU0FBUyxDQUFDLElBQUksQ0FBQyxDQUFDO0lBQ3RDLElBQUksQ0FBQyxNQUFNLENBQUMsT0FBTztRQUFFLE1BQU0sSUFBSSxLQUFLLENBQUMsTUFBTSxDQUFDLEtBQUssQ0FBQyxPQUFPLENBQUMsQ0FBQztJQUMzRCxPQUFPLE1BQU0sQ0FBQyxJQUFTLENBQUM7QUFDMUIsQ0FBQyIsInNvdXJjZXNDb250ZW50IjpbImltcG9ydCB7UGx1Z2luRmFjdG9yeX0gZnJvbSAnQGdybnNmdC9pZi1jb3JlL2ludGVyZmFjZXMnO1xuaW1wb3J0IHtQbHVnaW5QYXJhbXMsIENvbmZpZ1BhcmFtc30gZnJvbSAnQGdybnNmdC9pZi1jb3JlL3R5cGVzJztcbmltcG9ydCB7IHogfSBmcm9tICd6b2QnO1xuXG5leHBvcnQgY29uc3QgTWlzY1NlcnZpY2VzTW9kZWxQbHVnaW4gPSBQbHVnaW5GYWN0b3J5KHtcbiAgY29uZmlnVmFsaWRhdGlvbjogKGNvbmZpZzogQ29uZmlnUGFyYW1zKSA9PiB7XG4gICAgaWYgKCFjb25maWcgfHwgIU9iamVjdC5rZXlzKGNvbmZpZyk/Lmxlbmd0aCkge1xuICAgICAgdGhyb3cgbmV3IEVycm9yKCdNaXNzaW5nIG9yIGVtcHR5IGNvbmZpZ3VyYXRpb24uJyk7XG4gICAgfVxuXG4gICAgY29uc3QgY29uZmlnU2NoZW1hID0gei5vYmplY3Qoe1xuICAgICAgJ2lucHV0LXBhcmFtZXRlcnMnOiB6LmFycmF5KHouc3RyaW5nKCkpLFxuICAgICAgJ291dHB1dC1wYXJhbWV0ZXJzJzogei5hcnJheSh6LnN0cmluZygpKSxcbiAgICB9KTtcblxuICAgIHJldHVybiB2YWxpZGF0ZTx6LmluZmVyPHR5cGVvZiBjb25maWdTY2hlbWE+Pihjb25maWdTY2hlbWEsIGNvbmZpZyk7XG4gIH0sXG4gIGlucHV0VmFsaWRhdGlvbjogKGlucHV0OiBQbHVnaW5QYXJhbXMsIGNvbmZpZzogQ29uZmlnUGFyYW1zKSA9PiB7XG4gICAgY29uc3QgaW5wdXRQYXJhbWV0ZXJzID0gY29uZmlnWydpbnB1dC1wYXJhbWV0ZXJzJ107XG5cbiAgICBjb25zdCBpbnB1dERhdGEgPSBpbnB1dFBhcmFtZXRlcnMucmVkdWNlKFxuICAgICAgKGFjYzoge1t4OiBzdHJpbmddOiBhbnl9LCBwYXJhbTogc3RyaW5nIHwgbnVtYmVyKSA9PiB7XG4gICAgICAgIGFjY1twYXJhbV0gPSBpbnB1dFtwYXJhbV07XG5cbiAgICAgICAgcmV0dXJuIGFjYztcbiAgICAgIH0sXG4gICAgICB7fSBhcyBSZWNvcmQ8c3RyaW5nLCBudW1iZXI+XG4gICAgKTtcblxuICAgIGNvbnN0IHZhbGlkYXRpb25TY2hlbWEgPSB6LnJlY29yZCh6LnN0cmluZygpLCB6Lm51bWJlcigpKTtcblxuICAgIHJldHVybiB2YWxpZGF0ZSh2YWxpZGF0aW9uU2NoZW1hLCBpbnB1dERhdGEpO1xuICB9LFxuICBpbXBsZW1lbnRhdGlvbjogYXN5bmMgKGlucHV0czogUGx1Z2luUGFyYW1zW10sIGNvbmZpZzogQ29uZmlnUGFyYW1zKSA9PiB7XG4gICAgY29uc3QgeyAnaW5wdXQtcGFyYW1ldGVycyc6IF9pbnB1dFBhcmFtZXRlcnMgfSA9IGNvbmZpZztcblxuICAgIHJldHVybiBpbnB1dHMubWFwKGlucHV0ID0+IHtcbiAgICAgIGNvbnN0IGNvc3QgPSBpbnB1dFsnY29zdCddO1xuICAgICAgY29uc3QgY2FyYm9uSW50ZW5zaXR5ID0gaW5wdXRbJ2NhcmJvbi1pbnRlbnNpdHknXTtcbiAgICAgIGNvbnN0IGVuZXJneUNvc3RSYXRpbyA9IGlucHV0WydlbmVyZ3ktY29zdC1yYXRpbyddO1xuICAgICAgY29uc3QgZW1ib2RpZWRDb3N0UmF0aW8gPSBpbnB1dFsnZW1ib2RpZWQtY29zdC1yYXRpbyddO1xuXG4gICAgICBjb25zdCBtaXNjU2VydmljZXNFbmVyZ3lWYWx1ZSA9IGNvc3QgKiBlbmVyZ3lDb3N0UmF0aW87XG5cbiAgICAgIGNvbnN0IG1pc2NTZXJ2aWNlc09wZXJhdGlvbmFsVmFsdWUgPSBtaXNjU2VydmljZXNFbmVyZ3lWYWx1ZSAqIGNhcmJvbkludGVuc2l0eTtcblxuICAgICAgY29uc3QgbWlzY1NlcnZpY2VzRW1ib2RpZWRWYWx1ZSA9IGNvc3QgKiBlbWJvZGllZENvc3RSYXRpbztcblxuXG4gICAgICByZXR1cm4ge1xuICAgICAgICAuLi5pbnB1dCxcbiAgICAgICAgXCJtaXNjLXNlcnZpY2VzLWVuZXJneVwiOiBtaXNjU2VydmljZXNFbmVyZ3lWYWx1ZSxcbiAgICAgICAgXCJtaXNjLXNlcnZpY2VzLW9wZXJhdGlvbmFsXCI6IG1pc2NTZXJ2aWNlc09wZXJhdGlvbmFsVmFsdWUsXG4gICAgICAgIFwibWlzYy1zZXJ2aWNlcy1lbWJvZGllZFwiOiBtaXNjU2VydmljZXNFbWJvZGllZFZhbHVlLFxuICAgICAgfTtcbiAgICB9KTtcbiAgfSxcbn0pO1xuXG5mdW5jdGlvbiB2YWxpZGF0ZTxUPihzY2hlbWE6IHouWm9kVHlwZUFueSwgZGF0YTogdW5rbm93bik6IFQge1xuICBjb25zdCByZXN1bHQgPSBzY2hlbWEuc2FmZVBhcnNlKGRhdGEpO1xuICBpZiAoIXJlc3VsdC5zdWNjZXNzKSB0aHJvdyBuZXcgRXJyb3IocmVzdWx0LmVycm9yLm1lc3NhZ2UpO1xuICByZXR1cm4gcmVzdWx0LmRhdGEgYXMgVDtcbn1cbiJdfQ==