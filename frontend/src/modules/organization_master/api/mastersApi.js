import { apiClient as api } from "@/platform/api/httpClient";

const MASTER_CACHE_TTL_MS = 2 * 60 * 1000;
const masterCache = new Map();

const buildCacheKey = (key, params = {}) => {
  const normalizedParams = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .sort(([left], [right]) => left.localeCompare(right));

  if (!normalizedParams.length) return key;
  return `${key}?${JSON.stringify(normalizedParams)}`;
};

const getCachedMaster = (cacheKey) => {
  const cached = masterCache.get(cacheKey);
  if (!cached) return null;

  if (cached.value && cached.expiresAt > Date.now()) {
    return Promise.resolve(cached.value);
  }

  if (cached.promise) return cached.promise;
  masterCache.delete(cacheKey);
  return null;
};

const cacheMasterRequest = (cacheKey, request) => {
  const cached = getCachedMaster(cacheKey);
  if (cached) return cached;

  const pending = request()
    .then((response) => {
      masterCache.set(cacheKey, {
        value: response,
        expiresAt: Date.now() + MASTER_CACHE_TTL_MS,
      });
      return response;
    })
    .catch((error) => {
      masterCache.delete(cacheKey);
      throw error;
    });

  masterCache.set(cacheKey, {
    promise: pending,
    expiresAt: Date.now() + MASTER_CACHE_TTL_MS,
  });

  return pending;
};

const cachedMasterGet = (path, params) => cacheMasterRequest(
  buildCacheKey(path, params),
  () => api.get(path, params ? { params } : undefined),
);

export const clearMastersCache = () => {
  masterCache.clear();
};

export const mastersAPI = {
  getEmploymentTypes: () => cachedMasterGet('/masters/employment-types'),
  getEmploymentTypeRules: (code) => cachedMasterGet(`/masters/employment-types/${code}/rules`),
  getServiceEventTypes: () => cachedMasterGet('/masters/service-event-types'),
  getLeaveTypes: (employmentTypeCode) => cachedMasterGet('/masters/leave-types', { employment_type_code: employmentTypeCode }),
  getPayLevels: () => cachedMasterGet('/masters/pay-levels'),
  getServices: () => cachedMasterGet('/masters/services'),
  getServiceGroups: () => cachedMasterGet('/masters/service-groups'),
  getCasteCategories: () => cachedMasterGet('/masters/caste-categories'),
  getFormConfig: (formId, employmentTypeCode) =>
    api.get(`/masters/form-config/${formId}`, { params: { employment_type_code: employmentTypeCode }}),
  getDepartments: () => cachedMasterGet('/masters/departments'),
  getDesignations: () => cachedMasterGet('/masters/designations'),
  getOffices: () => cachedMasterGet('/masters/offices'),
};

export const versionedMastersAPI = {
  list: (masterType, includeInactive = false) =>
    api.get(`/masters/${masterType}`, { params: { include_inactive: includeInactive } }),
  get: (masterType, code) => api.get(`/masters/${masterType}/${code}`),
  getHistory: (masterType, code) => api.get(`/masters/${masterType}/${code}/history`),
  create: (masterType, data) => api.post(`/masters/${masterType}`, data),
  update: (masterType, code, data) => api.put(`/masters/${masterType}/${code}`, data),
  deprecate: (masterType, code, reason) =>
    api.post(`/masters/${masterType}/${code}/deprecate`, null, { params: { reason } }),
  getAuditLogs: (masterType, limit = 50) =>
    api.get(`/masters/${masterType}/audit/logs`, { params: { limit } }),
};

export const departmentManagementAPI = {
  list: (includeInactive = false) =>
    api.get('/departments/manage/', { params: { include_inactive: includeInactive } }),
  get: (code) => api.get(`/departments/manage/${code}`),
  create: (data) => api.post('/departments/manage/', data),
  update: (code, data) => api.put(`/departments/manage/${code}`, data),
  getSanctionedStrength: (code) =>
    api.get(`/departments/manage/${code}/sanctioned-strength`),
  updateSanctionedStrength: (code, data) =>
    api.put(`/departments/manage/${code}/sanctioned-strength`, data),
  getLogs: (code, limit = 50) =>
    api.get(`/departments/manage/${code}/logs`, { params: { limit } }),
  getAllLogs: (limit = 100) =>
    api.get('/departments/manage/logs/all', { params: { limit } }),
};
