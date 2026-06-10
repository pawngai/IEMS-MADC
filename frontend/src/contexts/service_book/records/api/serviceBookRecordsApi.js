import { apiClient as api } from "@/platform/api/httpClient";
import {
  applyApprovedServiceRecord,
  classifyServiceRecord,
  recordServiceBookRecord,
  routeServiceRecordToServiceBook,
  validateServiceRecordPayload,
} from "@/contexts/service_book/records/services/serviceBookRecordDomainService";

const BASE = "/service-book/records";

/**
 * Record a new Service Book record for an employee.
 * POST /api/service-book/records  (or /api/service-book/records/record)
 */
const recordEvent = (data) => recordServiceBookRecord(data);

/**
 * Correct a previously recorded Service Book record.
 * PATCH /api/service-book/records/:serviceEventId/correct
 */
const correctEvent = (serviceEventId, data) =>
  api.patch(`${BASE}/${serviceEventId}/correct`, data);

/**
 * Void a Service Book record.
 * POST /api/service-book/records/:serviceEventId/void
 */
const voidEvent = (serviceEventId, data) =>
  api.post(`${BASE}/${serviceEventId}/void`, data);

/**
 * Attach a document to a Service Book record.
 * POST /api/service-book/records/:serviceEventId/documents
 */
const attachDocument = (serviceEventId, data) =>
  api.post(`${BASE}/${serviceEventId}/documents`, data);

const listAccessibleDocuments = (params = {}) =>
  api.get("/documents/files", { params });

const uploadLinkedDocument = (file, metadata = {}) => {
  const params = new URLSearchParams();
  Object.entries(metadata || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, value);
  });

  const formData = new FormData();
  formData.append("file", file);

  const suffix = params.toString();
  return api.post(`/documents/document${suffix ? `?${suffix}` : ""}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

/**
 * Get the full event stream (timeline) for an employee.
 * GET /api/service-book/records/employees/:employeeId
 */
const getEventStream = (employeeId) =>
  api.get(`${BASE}/employees/${employeeId}`);

const getRecordSchema = () => api.get(`${BASE}/schema`);

const approveEvent = (serviceEventId) => applyApprovedServiceRecord(serviceEventId);

const getEmployeeIdentity = (employeeId) =>
  api.get(`/employee-identities/${employeeId}`);

export const serviceBookRecordsAPI = {
  recordEvent,
  correctEvent,
  voidEvent,
  attachDocument,
  listAccessibleDocuments,
  uploadLinkedDocument,
  getEventStream,
  getRecordSchema,
  approveEvent,
  getEmployeeIdentity,
};

export default serviceBookRecordsAPI;

export {
  recordServiceBookRecord,
  validateServiceRecordPayload,
  classifyServiceRecord,
  applyApprovedServiceRecord,
  routeServiceRecordToServiceBook,
};
