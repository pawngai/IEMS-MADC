import { apiClient as api } from "@/platform/api/httpClient";

const workQueueInflightRequests = new Map();

const dedupeWorkQueueGet = (key, request) => {
  const existing = workQueueInflightRequests.get(key);
  if (existing) return existing;

  let pending;
  try {
    pending = Promise.resolve(request());
  } catch (error) {
    return Promise.reject(error);
  }

  pending = pending.finally(() => {
    if (workQueueInflightRequests.get(key) === pending) {
      workQueueInflightRequests.delete(key);
    }
  });

  workQueueInflightRequests.set(key, pending);
  return pending;
};

export const clearWorkQueueInflightRequests = () => {
  workQueueInflightRequests.clear();
};

export const getMyEssProfile = async () => {
  const response = await dedupeWorkQueueGet("myEssProfile", () =>
    api.get("/ess/my-profile").catch(() => ({ data: null }))
  );
  return response?.data || null;
};

export const listProfilesByStatus = async (status, pageSize = 200) => {
  const response = await dedupeWorkQueueGet(`profiles:${status}:${pageSize}`, () =>
    api.get("/employee-profiles/", {
      params: { workflow_status: status, page_size: pageSize, profile_workflow_only: true },
    })
  );
  return response?.data?.profiles || [];
};

export const listIdentitiesByStatus = async (status, pageSize = 200) => {
  const response = await dedupeWorkQueueGet(`identities:${status}:${pageSize}`, () =>
    api.get("/employee-identities/", {
      params: { status, page_size: pageSize },
    })
  );
  return response?.data?.identities || [];
};

export const getEmployeeIdentitySummary = async (employeeId) => {
  if (!employeeId) return null;
  const response = await dedupeWorkQueueGet(`identitySummary:${employeeId}`, () =>
    api.get(`/employee-identities/${employeeId}`).catch(() => ({ data: null }))
  );
  return response?.data || null;
};

export const getProfileCompletion = async (employeeId) => {
  const response = await dedupeWorkQueueGet(`profileCompletion:${employeeId}`, () =>
    api.get(`/employee-profiles/${employeeId}/completion`)
  );
  return response?.data || null;
};

export const getProfileAuditTrail = async (employeeId) => {
  const response = await dedupeWorkQueueGet(`profileAudit:${employeeId}`, () =>
    api.get(`/employee-profiles/${employeeId}/audit-trail`)
  );
  return response?.data?.audit_trail || [];
};

export const getEmployeeProfileSummary = async (employeeId) => {
  if (!employeeId) return null;
  const response = await dedupeWorkQueueGet(`profileSummary:${employeeId}`, () =>
    api.get(`/employee-profiles/${employeeId}`).catch(() => ({ data: null }))
  );
  return response?.data || null;
};

export const submitProfile = (employeeId, remarks) =>
  api.post(`/employee-profiles/${employeeId}/submit`, { remarks: remarks || undefined });

export const verifyProfile = (employeeId, remarks) =>
  api.post(`/employee-profiles/${employeeId}/verify`, { remarks: remarks || undefined });

export const approveProfile = (employeeId, remarks) =>
  api.post(`/employee-profiles/${employeeId}/approve`, { remarks: remarks || undefined });

export const lockProfile = (employeeId, remarks) =>
  api.post(`/employee-profiles/${employeeId}/lock`, { remarks: remarks || undefined });

export const rejectProfile = (employeeId, remarks) =>
  api.post(`/employee-profiles/${employeeId}/reject`, { remarks });

export const submitIdentity = (employeeId, remarks) =>
  api.post(`/employee-identities/${employeeId}/submit`, { remarks: remarks || undefined });

export const verifyIdentity = (employeeId, remarks) =>
  api.post(`/employee-identities/${employeeId}/verify`, { remarks: remarks || undefined });

export const activateIdentity = (employeeId, remarks) =>
  api.post(`/employee-identities/${employeeId}/activate`, { remarks: remarks || undefined });

export const rejectIdentity = (employeeId, remarks) =>
  api.post(`/employee-identities/${employeeId}/reject`, { remarks });

// ── Service Book ──

export const listServiceBookQueue = async (workflowState, pageSize = 200) => {
  const params = { page_size: pageSize };
  if (Array.isArray(workflowState)) {
    params.workflow_states = workflowState.filter(Boolean).join(",");
  } else if (workflowState) {
    params.workflow_state = workflowState;
  }
  const stateKey = Array.isArray(workflowState) ? workflowState.join(",") : workflowState;

  const response = await dedupeWorkQueueGet(`serviceBookQueue:${stateKey}:${pageSize}`, () =>
    api.get("/service-book/queue", {
      params,
    })
  );
  return response?.data?.entries || [];
};

export const listServiceBookOpeningQueue = async (workflowState, pageSize = 200) => {
  const params = { page_size: pageSize };
  if (Array.isArray(workflowState)) {
    params.workflow_state = workflowState[0];
  } else if (workflowState) {
    params.workflow_state = workflowState;
  }
  const stateKey = Array.isArray(workflowState) ? workflowState.join(",") : workflowState;

  const response = await dedupeWorkQueueGet(`serviceBookOpeningQueue:${stateKey}:${pageSize}`, () =>
    api.get("/service-book/opening", {
      params,
    })
  );
  return response?.data?.items || [];
};

export const submitServiceBookEntry = (entryId, remarks) =>
  api.post(`/service-book/entries/${entryId}/submit`, { remarks: remarks || undefined });

export const verifyServiceBookEntry = (entryId, remarks) =>
  api.post(`/service-book/entries/${entryId}/verify`, { remarks: remarks || undefined });

export const approveServiceBookEntry = (entryId, remarks) =>
  api.post(`/service-book/entries/${entryId}/approve`, { remarks: remarks || undefined });

export const lockServiceBookEntry = (entryId, remarks) =>
  api.post(`/service-book/entries/${entryId}/lock`, { remarks: remarks || undefined });

export const submitServiceBookOpening = (employeeId, remarks) =>
  api.post(`/service-book/opening/${employeeId}/submit`, { remarks: remarks || undefined });

export const verifyServiceBookOpening = (employeeId, remarks) =>
  api.post(`/service-book/opening/${employeeId}/verify`, { remarks: remarks || undefined });

export const approveServiceBookOpening = (employeeId, remarks) =>
  api.post(`/service-book/opening/${employeeId}/approve`, { remarks: remarks || undefined });

// ── Change Requests ──

export const listChangeRequestsByStatus = async (status, pageSize = 100) => {
  const response = await dedupeWorkQueueGet(`changeRequests:${status}:${pageSize}`, () =>
    api.get("/change-requests", {
      params: { status, page_size: pageSize },
    })
  );
  return response?.data?.items || response?.data || [];
};

export const reviewChangeRequest = (requestId, action, remarks) =>
  api.post(`/change-requests/${requestId}/review`, { action, remarks: remarks || undefined });

