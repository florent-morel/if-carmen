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
            // Define input parameters
            const computeEnergy = input['compute-energy'];
            const storageEnergy = input['storage-energy'];
            const computeEmbodied = input['compute-embodied'];
            const storageEmbodied = input['storage-embodied'];
            const computeCost = input['compute-cost'];
            const storageCost = input['storage-cost'];
            const miscServicesCost = input['misc-services-cost'];
            const carbonIntensity = input['carbon-intensity'];
            // Calculate the outputs
            // TODO: Magic numbers to be put in config
            // TODO: Add this formula in documentation (and point explicitely to this file/model)
            const miscServicesEnergyValue = miscServicesCost * (0.75 * (computeEnergy / computeCost) + 0.25 * (storageEnergy / storageCost));
            const miscServicesOperationalValue = miscServicesEnergyValue * carbonIntensity;
            const miscServicesEmbodiedValue = miscServicesCost * (0.75 * (computeEmbodied / computeCost) + 0.25 * (storageEmbodied / storageCost));
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
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW5kZXguanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvbGliL21pc2Mtc2VydmljZXMtbW9kZWwtcGx1Z2luL2luZGV4LnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7OztBQUFBLDJEQUF5RDtBQUV6RCw2QkFBd0I7QUFFWCxRQUFBLHVCQUF1QixHQUFHLElBQUEsMEJBQWEsRUFBQztJQUNuRCxnQkFBZ0IsRUFBRSxDQUFDLE1BQW9CLEVBQUUsRUFBRTtRQUN6QyxJQUFJLENBQUMsTUFBTSxJQUFJLENBQUMsTUFBTSxDQUFDLElBQUksQ0FBQyxNQUFNLENBQUMsRUFBRSxNQUFNLEVBQUUsQ0FBQztZQUM1QyxNQUFNLElBQUksS0FBSyxDQUFDLGlDQUFpQyxDQUFDLENBQUM7UUFDckQsQ0FBQztRQUVELE1BQU0sWUFBWSxHQUFHLE9BQUMsQ0FBQyxNQUFNLENBQUM7WUFDNUIsa0JBQWtCLEVBQUUsT0FBQyxDQUFDLEtBQUssQ0FBQyxPQUFDLENBQUMsTUFBTSxFQUFFLENBQUM7WUFDdkMsbUJBQW1CLEVBQUUsT0FBQyxDQUFDLEtBQUssQ0FBQyxPQUFDLENBQUMsTUFBTSxFQUFFLENBQUM7U0FDekMsQ0FBQyxDQUFDO1FBRUgsT0FBTyxRQUFRLENBQStCLFlBQVksRUFBRSxNQUFNLENBQUMsQ0FBQztJQUN0RSxDQUFDO0lBQ0QsZUFBZSxFQUFFLENBQUMsS0FBbUIsRUFBRSxNQUFvQixFQUFFLEVBQUU7UUFDN0QsTUFBTSxlQUFlLEdBQUcsTUFBTSxDQUFDLGtCQUFrQixDQUFDLENBQUM7UUFFbkQsTUFBTSxTQUFTLEdBQUcsZUFBZSxDQUFDLE1BQU0sQ0FDdEMsQ0FBQyxHQUF1QixFQUFFLEtBQXNCLEVBQUUsRUFBRTtZQUNsRCxHQUFHLENBQUMsS0FBSyxDQUFDLEdBQUcsS0FBSyxDQUFDLEtBQUssQ0FBQyxDQUFDO1lBRTFCLE9BQU8sR0FBRyxDQUFDO1FBQ2IsQ0FBQyxFQUNELEVBQTRCLENBQzdCLENBQUM7UUFFRixNQUFNLGdCQUFnQixHQUFHLE9BQUMsQ0FBQyxNQUFNLENBQUMsT0FBQyxDQUFDLE1BQU0sRUFBRSxFQUFFLE9BQUMsQ0FBQyxNQUFNLEVBQUUsQ0FBQyxDQUFDO1FBRTFELE9BQU8sUUFBUSxDQUFDLGdCQUFnQixFQUFFLFNBQVMsQ0FBQyxDQUFDO0lBQy9DLENBQUM7SUFDRCxjQUFjLEVBQUUsS0FBSyxFQUFFLE1BQXNCLEVBQUUsTUFBb0IsRUFBRSxFQUFFO1FBQ3JFLE1BQU0sRUFBRSxrQkFBa0IsRUFBRSxnQkFBZ0IsRUFBRSxHQUFHLE1BQU0sQ0FBQztRQUV4RCxPQUFPLE1BQU0sQ0FBQyxHQUFHLENBQUMsS0FBSyxDQUFDLEVBQUU7WUFDeEIsMEJBQTBCO1lBQzFCLE1BQU0sYUFBYSxHQUFHLEtBQUssQ0FBQyxnQkFBZ0IsQ0FBQyxDQUFDO1lBQzlDLE1BQU0sYUFBYSxHQUFHLEtBQUssQ0FBQyxnQkFBZ0IsQ0FBQyxDQUFDO1lBQzlDLE1BQU0sZUFBZSxHQUFHLEtBQUssQ0FBQyxrQkFBa0IsQ0FBQyxDQUFDO1lBQ2xELE1BQU0sZUFBZSxHQUFHLEtBQUssQ0FBQyxrQkFBa0IsQ0FBQyxDQUFDO1lBQ2xELE1BQU0sV0FBVyxHQUFHLEtBQUssQ0FBQyxjQUFjLENBQUMsQ0FBQztZQUMxQyxNQUFNLFdBQVcsR0FBRyxLQUFLLENBQUMsY0FBYyxDQUFDLENBQUM7WUFDMUMsTUFBTSxnQkFBZ0IsR0FBRyxLQUFLLENBQUMsb0JBQW9CLENBQUMsQ0FBQztZQUNyRCxNQUFNLGVBQWUsR0FBRyxLQUFLLENBQUMsa0JBQWtCLENBQUMsQ0FBQztZQUVsRCx3QkFBd0I7WUFDbEIsMENBQTBDO1lBQzFDLHFGQUFxRjtZQUMzRixNQUFNLHVCQUF1QixHQUFHLGdCQUFnQixHQUFHLENBQUMsSUFBSSxHQUFHLENBQUMsYUFBYSxHQUFHLFdBQVcsQ0FBQyxHQUFHLElBQUksR0FBRyxDQUFDLGFBQWEsR0FBRyxXQUFXLENBQUMsQ0FBQyxDQUFDO1lBRWpJLE1BQU0sNEJBQTRCLEdBQUcsdUJBQXVCLEdBQUcsZUFBZSxDQUFDO1lBRS9FLE1BQU0seUJBQXlCLEdBQUcsZ0JBQWdCLEdBQUcsQ0FBQyxJQUFJLEdBQUcsQ0FBQyxlQUFlLEdBQUcsV0FBVyxDQUFDLEdBQUcsSUFBSSxHQUFHLENBQUMsZUFBZSxHQUFHLFdBQVcsQ0FBQyxDQUFDLENBQUM7WUFHdkksT0FBTztnQkFDTCxHQUFHLEtBQUs7Z0JBQ1Isc0JBQXNCLEVBQUUsdUJBQXVCO2dCQUMvQywyQkFBMkIsRUFBRSw0QkFBNEI7Z0JBQ3pELHdCQUF3QixFQUFFLHlCQUF5QjthQUNwRCxDQUFDO1FBQ0osQ0FBQyxDQUFDLENBQUM7SUFDTCxDQUFDO0NBQ0YsQ0FBQyxDQUFDO0FBRUgsU0FBUyxRQUFRLENBQUksTUFBb0IsRUFBRSxJQUFhO0lBQ3RELE1BQU0sTUFBTSxHQUFHLE1BQU0sQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLENBQUM7SUFDdEMsSUFBSSxDQUFDLE1BQU0sQ0FBQyxPQUFPO1FBQUUsTUFBTSxJQUFJLEtBQUssQ0FBQyxNQUFNLENBQUMsS0FBSyxDQUFDLE9BQU8sQ0FBQyxDQUFDO0lBQzNELE9BQU8sTUFBTSxDQUFDLElBQVMsQ0FBQztBQUMxQixDQUFDIiwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0IHtQbHVnaW5GYWN0b3J5fSBmcm9tICdAZ3Juc2Z0L2lmLWNvcmUvaW50ZXJmYWNlcyc7XG5pbXBvcnQge1BsdWdpblBhcmFtcywgQ29uZmlnUGFyYW1zfSBmcm9tICdAZ3Juc2Z0L2lmLWNvcmUvdHlwZXMnO1xuaW1wb3J0IHsgeiB9IGZyb20gJ3pvZCc7XG5cbmV4cG9ydCBjb25zdCBNaXNjU2VydmljZXNNb2RlbFBsdWdpbiA9IFBsdWdpbkZhY3Rvcnkoe1xuICBjb25maWdWYWxpZGF0aW9uOiAoY29uZmlnOiBDb25maWdQYXJhbXMpID0+IHtcbiAgICBpZiAoIWNvbmZpZyB8fCAhT2JqZWN0LmtleXMoY29uZmlnKT8ubGVuZ3RoKSB7XG4gICAgICB0aHJvdyBuZXcgRXJyb3IoJ01pc3Npbmcgb3IgZW1wdHkgY29uZmlndXJhdGlvbi4nKTtcbiAgICB9XG5cbiAgICBjb25zdCBjb25maWdTY2hlbWEgPSB6Lm9iamVjdCh7XG4gICAgICAnaW5wdXQtcGFyYW1ldGVycyc6IHouYXJyYXkoei5zdHJpbmcoKSksXG4gICAgICAnb3V0cHV0LXBhcmFtZXRlcnMnOiB6LmFycmF5KHouc3RyaW5nKCkpLFxuICAgIH0pO1xuXG4gICAgcmV0dXJuIHZhbGlkYXRlPHouaW5mZXI8dHlwZW9mIGNvbmZpZ1NjaGVtYT4+KGNvbmZpZ1NjaGVtYSwgY29uZmlnKTtcbiAgfSxcbiAgaW5wdXRWYWxpZGF0aW9uOiAoaW5wdXQ6IFBsdWdpblBhcmFtcywgY29uZmlnOiBDb25maWdQYXJhbXMpID0+IHtcbiAgICBjb25zdCBpbnB1dFBhcmFtZXRlcnMgPSBjb25maWdbJ2lucHV0LXBhcmFtZXRlcnMnXTtcblxuICAgIGNvbnN0IGlucHV0RGF0YSA9IGlucHV0UGFyYW1ldGVycy5yZWR1Y2UoXG4gICAgICAoYWNjOiB7W3g6IHN0cmluZ106IGFueX0sIHBhcmFtOiBzdHJpbmcgfCBudW1iZXIpID0+IHtcbiAgICAgICAgYWNjW3BhcmFtXSA9IGlucHV0W3BhcmFtXTtcblxuICAgICAgICByZXR1cm4gYWNjO1xuICAgICAgfSxcbiAgICAgIHt9IGFzIFJlY29yZDxzdHJpbmcsIG51bWJlcj5cbiAgICApO1xuXG4gICAgY29uc3QgdmFsaWRhdGlvblNjaGVtYSA9IHoucmVjb3JkKHouc3RyaW5nKCksIHoubnVtYmVyKCkpO1xuXG4gICAgcmV0dXJuIHZhbGlkYXRlKHZhbGlkYXRpb25TY2hlbWEsIGlucHV0RGF0YSk7XG4gIH0sXG4gIGltcGxlbWVudGF0aW9uOiBhc3luYyAoaW5wdXRzOiBQbHVnaW5QYXJhbXNbXSwgY29uZmlnOiBDb25maWdQYXJhbXMpID0+IHtcbiAgICBjb25zdCB7ICdpbnB1dC1wYXJhbWV0ZXJzJzogX2lucHV0UGFyYW1ldGVycyB9ID0gY29uZmlnO1xuXG4gICAgcmV0dXJuIGlucHV0cy5tYXAoaW5wdXQgPT4ge1xuICAgICAgLy8gRGVmaW5lIGlucHV0IHBhcmFtZXRlcnNcbiAgICAgIGNvbnN0IGNvbXB1dGVFbmVyZ3kgPSBpbnB1dFsnY29tcHV0ZS1lbmVyZ3knXTtcbiAgICAgIGNvbnN0IHN0b3JhZ2VFbmVyZ3kgPSBpbnB1dFsnc3RvcmFnZS1lbmVyZ3knXTtcbiAgICAgIGNvbnN0IGNvbXB1dGVFbWJvZGllZCA9IGlucHV0Wydjb21wdXRlLWVtYm9kaWVkJ107XG4gICAgICBjb25zdCBzdG9yYWdlRW1ib2RpZWQgPSBpbnB1dFsnc3RvcmFnZS1lbWJvZGllZCddO1xuICAgICAgY29uc3QgY29tcHV0ZUNvc3QgPSBpbnB1dFsnY29tcHV0ZS1jb3N0J107XG4gICAgICBjb25zdCBzdG9yYWdlQ29zdCA9IGlucHV0WydzdG9yYWdlLWNvc3QnXTtcbiAgICAgIGNvbnN0IG1pc2NTZXJ2aWNlc0Nvc3QgPSBpbnB1dFsnbWlzYy1zZXJ2aWNlcy1jb3N0J107XG4gICAgICBjb25zdCBjYXJib25JbnRlbnNpdHkgPSBpbnB1dFsnY2FyYm9uLWludGVuc2l0eSddO1xuXG4gICAgICAvLyBDYWxjdWxhdGUgdGhlIG91dHB1dHNcbiAgICAgICAgICAgIC8vIFRPRE86IE1hZ2ljIG51bWJlcnMgdG8gYmUgcHV0IGluIGNvbmZpZ1xuICAgICAgICAgICAgLy8gVE9ETzogQWRkIHRoaXMgZm9ybXVsYSBpbiBkb2N1bWVudGF0aW9uIChhbmQgcG9pbnQgZXhwbGljaXRlbHkgdG8gdGhpcyBmaWxlL21vZGVsKVxuICAgICAgY29uc3QgbWlzY1NlcnZpY2VzRW5lcmd5VmFsdWUgPSBtaXNjU2VydmljZXNDb3N0ICogKDAuNzUgKiAoY29tcHV0ZUVuZXJneSAvIGNvbXB1dGVDb3N0KSArIDAuMjUgKiAoc3RvcmFnZUVuZXJneSAvIHN0b3JhZ2VDb3N0KSk7XG5cbiAgICAgIGNvbnN0IG1pc2NTZXJ2aWNlc09wZXJhdGlvbmFsVmFsdWUgPSBtaXNjU2VydmljZXNFbmVyZ3lWYWx1ZSAqIGNhcmJvbkludGVuc2l0eTtcblxuICAgICAgY29uc3QgbWlzY1NlcnZpY2VzRW1ib2RpZWRWYWx1ZSA9IG1pc2NTZXJ2aWNlc0Nvc3QgKiAoMC43NSAqIChjb21wdXRlRW1ib2RpZWQgLyBjb21wdXRlQ29zdCkgKyAwLjI1ICogKHN0b3JhZ2VFbWJvZGllZCAvIHN0b3JhZ2VDb3N0KSk7XG5cblxuICAgICAgcmV0dXJuIHtcbiAgICAgICAgLi4uaW5wdXQsXG4gICAgICAgIFwibWlzYy1zZXJ2aWNlcy1lbmVyZ3lcIjogbWlzY1NlcnZpY2VzRW5lcmd5VmFsdWUsXG4gICAgICAgIFwibWlzYy1zZXJ2aWNlcy1vcGVyYXRpb25hbFwiOiBtaXNjU2VydmljZXNPcGVyYXRpb25hbFZhbHVlLFxuICAgICAgICBcIm1pc2Mtc2VydmljZXMtZW1ib2RpZWRcIjogbWlzY1NlcnZpY2VzRW1ib2RpZWRWYWx1ZSxcbiAgICAgIH07XG4gICAgfSk7XG4gIH0sXG59KTtcblxuZnVuY3Rpb24gdmFsaWRhdGU8VD4oc2NoZW1hOiB6LlpvZFR5cGVBbnksIGRhdGE6IHVua25vd24pOiBUIHtcbiAgY29uc3QgcmVzdWx0ID0gc2NoZW1hLnNhZmVQYXJzZShkYXRhKTtcbiAgaWYgKCFyZXN1bHQuc3VjY2VzcykgdGhyb3cgbmV3IEVycm9yKHJlc3VsdC5lcnJvci5tZXNzYWdlKTtcbiAgcmV0dXJuIHJlc3VsdC5kYXRhIGFzIFQ7XG59XG4iXX0=