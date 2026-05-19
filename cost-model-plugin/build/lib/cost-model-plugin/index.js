"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CostModelPlugin = void 0;
const interfaces_1 = require("@grnsft/if-core/interfaces");
const zod_1 = require("zod");
exports.CostModelPlugin = (0, interfaces_1.PluginFactory)({
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
function validate(schema, data) {
    const result = schema.safeParse(data);
    if (!result.success)
        throw new Error(result.error.message);
    return result.data;
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW5kZXguanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvbGliL2Nvc3QtbW9kZWwtcGx1Z2luL2luZGV4LnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7OztBQUFBLDJEQUF5RDtBQUV6RCw2QkFBd0I7QUFFWCxRQUFBLGVBQWUsR0FBRyxJQUFBLDBCQUFhLEVBQUM7SUFDM0MsZ0JBQWdCLEVBQUUsQ0FBQyxNQUFvQixFQUFFLEVBQUU7UUFDekMsSUFBSSxDQUFDLE1BQU0sSUFBSSxDQUFDLE1BQU0sQ0FBQyxJQUFJLENBQUMsTUFBTSxDQUFDLEVBQUUsTUFBTSxFQUFFLENBQUM7WUFDNUMsTUFBTSxJQUFJLEtBQUssQ0FBQyxpQ0FBaUMsQ0FBQyxDQUFDO1FBQ3JELENBQUM7UUFFRCxNQUFNLFlBQVksR0FBRyxPQUFDLENBQUMsTUFBTSxDQUFDO1lBQzVCLGtCQUFrQixFQUFFLE9BQUMsQ0FBQyxLQUFLLENBQUMsT0FBQyxDQUFDLE1BQU0sRUFBRSxDQUFDO1lBQ3ZDLG1CQUFtQixFQUFFLE9BQUMsQ0FBQyxLQUFLLENBQUMsT0FBQyxDQUFDLE1BQU0sRUFBRSxDQUFDO1NBQ3pDLENBQUMsQ0FBQztRQUVILE9BQU8sUUFBUSxDQUErQixZQUFZLEVBQUUsTUFBTSxDQUFDLENBQUM7SUFDdEUsQ0FBQztJQUNELGVBQWUsRUFBRSxDQUFDLEtBQW1CLEVBQUUsTUFBb0IsRUFBRSxFQUFFO1FBQzdELE1BQU0sZUFBZSxHQUFHLE1BQU0sQ0FBQyxrQkFBa0IsQ0FBQyxDQUFDO1FBRW5ELE1BQU0sU0FBUyxHQUFHLGVBQWUsQ0FBQyxNQUFNLENBQ3RDLENBQUMsR0FBdUIsRUFBRSxLQUFzQixFQUFFLEVBQUU7WUFDbEQsR0FBRyxDQUFDLEtBQUssQ0FBQyxHQUFHLEtBQUssQ0FBQyxLQUFLLENBQUMsQ0FBQztZQUUxQixPQUFPLEdBQUcsQ0FBQztRQUNiLENBQUMsRUFDRCxFQUE0QixDQUM3QixDQUFDO1FBRUYsTUFBTSxnQkFBZ0IsR0FBRyxPQUFDLENBQUMsTUFBTSxDQUFDLE9BQUMsQ0FBQyxNQUFNLEVBQUUsRUFBRSxPQUFDLENBQUMsTUFBTSxFQUFFLENBQUMsQ0FBQztRQUUxRCxPQUFPLFFBQVEsQ0FBQyxnQkFBZ0IsRUFBRSxTQUFTLENBQUMsQ0FBQztJQUMvQyxDQUFDO0lBQ0QsY0FBYyxFQUFFLEtBQUssRUFBRSxNQUFzQixFQUFFLE1BQW9CLEVBQUUsRUFBRTtRQUNyRSxNQUFNLEVBQUUsa0JBQWtCLEVBQUUsZ0JBQWdCLEVBQUUsR0FBRyxNQUFNLENBQUM7UUFFeEQsT0FBTyxNQUFNLENBQUMsR0FBRyxDQUFDLEtBQUssQ0FBQyxFQUFFO1lBQ3hCLDBCQUEwQjtZQUMxQixNQUFNLGFBQWEsR0FBRyxLQUFLLENBQUMsZ0JBQWdCLENBQUMsQ0FBQztZQUM5QyxNQUFNLGFBQWEsR0FBRyxLQUFLLENBQUMsZ0JBQWdCLENBQUMsQ0FBQztZQUM5QyxNQUFNLGVBQWUsR0FBRyxLQUFLLENBQUMsa0JBQWtCLENBQUMsQ0FBQztZQUNsRCxNQUFNLGVBQWUsR0FBRyxLQUFLLENBQUMsa0JBQWtCLENBQUMsQ0FBQztZQUNsRCxNQUFNLFdBQVcsR0FBRyxLQUFLLENBQUMsY0FBYyxDQUFDLENBQUM7WUFDMUMsTUFBTSxXQUFXLEdBQUcsS0FBSyxDQUFDLGNBQWMsQ0FBQyxDQUFDO1lBQzFDLE1BQU0sWUFBWSxHQUFHLEtBQUssQ0FBQyxlQUFlLENBQUMsQ0FBQztZQUM1QyxNQUFNLGVBQWUsR0FBRyxLQUFLLENBQUMsa0JBQWtCLENBQUMsQ0FBQztZQUVsRCx3QkFBd0I7WUFDeEIsTUFBTSxtQkFBbUIsR0FBRyxZQUFZLEdBQUcsQ0FBQyxJQUFJLEdBQUcsQ0FBQyxhQUFhLEdBQUcsV0FBVyxDQUFDLEdBQUcsSUFBSSxHQUFHLENBQUMsYUFBYSxHQUFHLFdBQVcsQ0FBQyxDQUFDLENBQUM7WUFFekgsTUFBTSx3QkFBd0IsR0FBRyxtQkFBbUIsR0FBRyxlQUFlLENBQUM7WUFFdkUsTUFBTSxxQkFBcUIsR0FBRyxZQUFZLEdBQUcsQ0FBQyxJQUFJLEdBQUcsQ0FBQyxlQUFlLEdBQUcsV0FBVyxDQUFDLEdBQUcsSUFBSSxHQUFHLENBQUMsZUFBZSxHQUFHLFdBQVcsQ0FBQyxDQUFDLENBQUM7WUFHL0gsT0FBTztnQkFDTCxHQUFHLEtBQUs7Z0JBQ1IsaUJBQWlCLEVBQUUsbUJBQW1CO2dCQUN0QyxzQkFBc0IsRUFBRSx3QkFBd0I7Z0JBQ2hELG1CQUFtQixFQUFFLHFCQUFxQjthQUMzQyxDQUFDO1FBQ0osQ0FBQyxDQUFDLENBQUM7SUFDTCxDQUFDO0NBQ0YsQ0FBQyxDQUFDO0FBRUgsU0FBUyxRQUFRLENBQUksTUFBb0IsRUFBRSxJQUFhO0lBQ3RELE1BQU0sTUFBTSxHQUFHLE1BQU0sQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLENBQUM7SUFDdEMsSUFBSSxDQUFDLE1BQU0sQ0FBQyxPQUFPO1FBQUUsTUFBTSxJQUFJLEtBQUssQ0FBQyxNQUFNLENBQUMsS0FBSyxDQUFDLE9BQU8sQ0FBQyxDQUFDO0lBQzNELE9BQU8sTUFBTSxDQUFDLElBQVMsQ0FBQztBQUMxQixDQUFDIiwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0IHtQbHVnaW5GYWN0b3J5fSBmcm9tICdAZ3Juc2Z0L2lmLWNvcmUvaW50ZXJmYWNlcyc7XG5pbXBvcnQge1BsdWdpblBhcmFtcywgQ29uZmlnUGFyYW1zfSBmcm9tICdAZ3Juc2Z0L2lmLWNvcmUvdHlwZXMnO1xuaW1wb3J0IHsgeiB9IGZyb20gJ3pvZCc7XG5cbmV4cG9ydCBjb25zdCBDb3N0TW9kZWxQbHVnaW4gPSBQbHVnaW5GYWN0b3J5KHtcbiAgY29uZmlnVmFsaWRhdGlvbjogKGNvbmZpZzogQ29uZmlnUGFyYW1zKSA9PiB7XG4gICAgaWYgKCFjb25maWcgfHwgIU9iamVjdC5rZXlzKGNvbmZpZyk/Lmxlbmd0aCkge1xuICAgICAgdGhyb3cgbmV3IEVycm9yKCdNaXNzaW5nIG9yIGVtcHR5IGNvbmZpZ3VyYXRpb24uJyk7XG4gICAgfVxuXG4gICAgY29uc3QgY29uZmlnU2NoZW1hID0gei5vYmplY3Qoe1xuICAgICAgJ2lucHV0LXBhcmFtZXRlcnMnOiB6LmFycmF5KHouc3RyaW5nKCkpLFxuICAgICAgJ291dHB1dC1wYXJhbWV0ZXJzJzogei5hcnJheSh6LnN0cmluZygpKSxcbiAgICB9KTtcblxuICAgIHJldHVybiB2YWxpZGF0ZTx6LmluZmVyPHR5cGVvZiBjb25maWdTY2hlbWE+Pihjb25maWdTY2hlbWEsIGNvbmZpZyk7XG4gIH0sXG4gIGlucHV0VmFsaWRhdGlvbjogKGlucHV0OiBQbHVnaW5QYXJhbXMsIGNvbmZpZzogQ29uZmlnUGFyYW1zKSA9PiB7XG4gICAgY29uc3QgaW5wdXRQYXJhbWV0ZXJzID0gY29uZmlnWydpbnB1dC1wYXJhbWV0ZXJzJ107XG5cbiAgICBjb25zdCBpbnB1dERhdGEgPSBpbnB1dFBhcmFtZXRlcnMucmVkdWNlKFxuICAgICAgKGFjYzoge1t4OiBzdHJpbmddOiBhbnl9LCBwYXJhbTogc3RyaW5nIHwgbnVtYmVyKSA9PiB7XG4gICAgICAgIGFjY1twYXJhbV0gPSBpbnB1dFtwYXJhbV07XG5cbiAgICAgICAgcmV0dXJuIGFjYztcbiAgICAgIH0sXG4gICAgICB7fSBhcyBSZWNvcmQ8c3RyaW5nLCBudW1iZXI+XG4gICAgKTtcblxuICAgIGNvbnN0IHZhbGlkYXRpb25TY2hlbWEgPSB6LnJlY29yZCh6LnN0cmluZygpLCB6Lm51bWJlcigpKTtcblxuICAgIHJldHVybiB2YWxpZGF0ZSh2YWxpZGF0aW9uU2NoZW1hLCBpbnB1dERhdGEpO1xuICB9LFxuICBpbXBsZW1lbnRhdGlvbjogYXN5bmMgKGlucHV0czogUGx1Z2luUGFyYW1zW10sIGNvbmZpZzogQ29uZmlnUGFyYW1zKSA9PiB7XG4gICAgY29uc3QgeyAnaW5wdXQtcGFyYW1ldGVycyc6IF9pbnB1dFBhcmFtZXRlcnMgfSA9IGNvbmZpZztcblxuICAgIHJldHVybiBpbnB1dHMubWFwKGlucHV0ID0+IHtcbiAgICAgIC8vIERlZmluZSBpbnB1dCBwYXJhbWV0ZXJzXG4gICAgICBjb25zdCBjb21wdXRlRW5lcmd5ID0gaW5wdXRbJ2NvbXB1dGUtZW5lcmd5J107XG4gICAgICBjb25zdCBzdG9yYWdlRW5lcmd5ID0gaW5wdXRbJ3N0b3JhZ2UtZW5lcmd5J107XG4gICAgICBjb25zdCBjb21wdXRlRW1ib2RpZWQgPSBpbnB1dFsnY29tcHV0ZS1lbWJvZGllZCddO1xuICAgICAgY29uc3Qgc3RvcmFnZUVtYm9kaWVkID0gaW5wdXRbJ3N0b3JhZ2UtZW1ib2RpZWQnXTtcbiAgICAgIGNvbnN0IGNvbXB1dGVDb3N0ID0gaW5wdXRbJ2NvbXB1dGUtY29zdCddO1xuICAgICAgY29uc3Qgc3RvcmFnZUNvc3QgPSBpbnB1dFsnc3RvcmFnZS1jb3N0J107XG4gICAgICBjb25zdCBzZXJ2aWNlc0Nvc3QgPSBpbnB1dFsnc2VydmljZXMtY29zdCddO1xuICAgICAgY29uc3QgY2FyYm9uSW50ZW5zaXR5ID0gaW5wdXRbJ2NhcmJvbi1pbnRlbnNpdHknXTtcblxuICAgICAgLy8gQ2FsY3VsYXRlIHRoZSBvdXRwdXRzXG4gICAgICBjb25zdCBzZXJ2aWNlc0VuZXJneVZhbHVlID0gc2VydmljZXNDb3N0ICogKDAuNzUgKiAoY29tcHV0ZUVuZXJneSAvIGNvbXB1dGVDb3N0KSArIDAuMjUgKiAoc3RvcmFnZUVuZXJneSAvIHN0b3JhZ2VDb3N0KSk7XG5cbiAgICAgIGNvbnN0IHNlcnZpY2VzT3BlcmF0aW9uYWxWYWx1ZSA9IHNlcnZpY2VzRW5lcmd5VmFsdWUgKiBjYXJib25JbnRlbnNpdHk7XG5cbiAgICAgIGNvbnN0IHNlcnZpY2VzRW1ib2RpZWRWYWx1ZSA9IHNlcnZpY2VzQ29zdCAqICgwLjc1ICogKGNvbXB1dGVFbWJvZGllZCAvIGNvbXB1dGVDb3N0KSArIDAuMjUgKiAoc3RvcmFnZUVtYm9kaWVkIC8gc3RvcmFnZUNvc3QpKTtcblxuXG4gICAgICByZXR1cm4ge1xuICAgICAgICAuLi5pbnB1dCxcbiAgICAgICAgXCJzZXJ2aWNlcy1lbmVyZ3lcIjogc2VydmljZXNFbmVyZ3lWYWx1ZSxcbiAgICAgICAgXCJzZXJ2aWNlcy1vcGVyYXRpb25hbFwiOiBzZXJ2aWNlc09wZXJhdGlvbmFsVmFsdWUsXG4gICAgICAgIFwic2VydmljZXMtZW1ib2RpZWRcIjogc2VydmljZXNFbWJvZGllZFZhbHVlLFxuICAgICAgfTtcbiAgICB9KTtcbiAgfSxcbn0pO1xuXG5mdW5jdGlvbiB2YWxpZGF0ZTxUPihzY2hlbWE6IHouWm9kVHlwZUFueSwgZGF0YTogdW5rbm93bik6IFQge1xuICBjb25zdCByZXN1bHQgPSBzY2hlbWEuc2FmZVBhcnNlKGRhdGEpO1xuICBpZiAoIXJlc3VsdC5zdWNjZXNzKSB0aHJvdyBuZXcgRXJyb3IocmVzdWx0LmVycm9yLm1lc3NhZ2UpO1xuICByZXR1cm4gcmVzdWx0LmRhdGEgYXMgVDtcbn1cbiJdfQ==