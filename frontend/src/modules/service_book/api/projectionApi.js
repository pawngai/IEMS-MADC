import { apiClient as api } from "@/platform/api/httpClient";
import { PARTS_INFO } from "@/modules/service_book/model/partsInfoSchema";
import { normalizeComplete } from "@/modules/service_book/services/projectionNormalizer";

export const listEntries = async (employeeId, opts = {}) => {
  const params = { active: opts.active ?? true };
  if (opts.part_key) params.part_key = opts.part_key;
  if (opts.schema_key) params.schema_key = opts.schema_key;
  if (opts.statuses?.length) params.statuses = opts.statuses.join(",");
  const response = await api.get(`/service-book/employees/${employeeId}/entries`, { params });
  const entries = Array.isArray(response?.data) ? response.data : [];
  return { response, entries };
};

const getComplete = async (employeeId, opts = {}) => {
  const { response, entries } = await listEntries(employeeId, opts);
  return {
    ...response,
    data: normalizeComplete(employeeId, entries),
  };
};

const getPartFromComplete = async (employeeId, selector, opts = {}) => {
  const response = await getComplete(employeeId, opts);
  return {
    ...response,
    data: selector(response?.data || {}),
  };
};

export const projectionAPI = {
  getPartsInfo: async () => ({
    data: {
      parts: PARTS_INFO,
      total_parts: Object.keys(PARTS_INFO).length,
    },
  }),
  getPartInfo: async (part) => ({ data: PARTS_INFO[part] }),
  listEntries,
  getComplete,
  getPartI: (employeeId) => getPartFromComplete(employeeId, (x) => x.part_i),
  getPartIIA: (employeeId) => getPartFromComplete(employeeId, (x) => x.part_ii_a),
  getPartIIB: (employeeId) => getPartFromComplete(employeeId, (x) => x.part_ii_b),
  getPartIII: (employeeId) => getPartFromComplete(employeeId, (x) => x.part_iii),
  getPartIV: (employeeId) => getPartFromComplete(employeeId, (x) => x.part_iv),
  getPartV: (employeeId) => getPartFromComplete(employeeId, (x) => x.part_v),
  getPartVI: (employeeId) => getPartFromComplete(employeeId, (x) => x.part_vi),
  getPartVII: (employeeId) => getPartFromComplete(employeeId, (x) => x.part_vii),
  getPartVIII: (employeeId) => getPartFromComplete(employeeId, (x) => x.part_viii),
};