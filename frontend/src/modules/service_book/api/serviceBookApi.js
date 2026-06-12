import { apiClient as api } from "@/platform/api/httpClient";
import { projectionAPI } from "@/modules/service_book/api/projectionApi";
import { printAPI } from "@/modules/service_book/api/printApi";
import {
  createServiceBookIfEligible,
  generateServiceBookPrintModel,
  rebuildServiceBookProjection,
  validateServiceBookEligibility,
} from "@/modules/service_book/services/serviceBookDomainService";

export const serviceBookAPI = {
  ...projectionAPI,
  ...printAPI,
  createEntry: async () => {
    throw new Error("Service Book is projection-only. Record lifecycle changes through Service Book records.");
  },
  submitEntry: async () => {
    throw new Error("Service Book workflow mutations have moved to Service Book records.");
  },
  verifyEntry: async () => {
    throw new Error("Service Book workflow mutations have moved to Service Book records.");
  },
  approveEntry: async () => {
    throw new Error("Service Book workflow mutations have moved to Service Book records.");
  },
  lockEntry: async () => {
    throw new Error("Service Book workflow mutations have moved to Service Book records.");
  },
  getPartIDefaults: async (employeeId) => {
    const response = await api.get(`/service-book/employees/${employeeId}/part-i/defaults`);
    return response.data;
  },
};

export { projectionAPI, printAPI };

export {
  createServiceBookIfEligible,
  validateServiceBookEligibility,
  rebuildServiceBookProjection,
  generateServiceBookPrintModel,
};
