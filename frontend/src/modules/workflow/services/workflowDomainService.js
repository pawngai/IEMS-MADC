import { apiClient as api } from "@/platform/api/httpClient";

const BASE = "/api/workflow/tasks";

const WORKFLOW_ACTIONS = {
  SUBMIT: "START_REVIEW",
  APPROVE: "COMPLETE",
  REJECT: "REJECT",
};

export const transitionWorkflowState = async ({ taskId, action, remarks }) => {
  const normalizedAction = String(action || "").trim().toUpperCase();
  if (!taskId) throw new Error("taskId is required");
  if (!normalizedAction) throw new Error("action is required");

  return api.post(`${BASE}/${taskId}/transition`, {
    action: normalizedAction,
    remarks: remarks || undefined,
  });
};

export const submitWorkflowAction = async ({ taskId, remarks }) =>
  transitionWorkflowState({ taskId, action: WORKFLOW_ACTIONS.SUBMIT, remarks });

export const approveWorkflowItem = async ({ taskId, remarks }) =>
  transitionWorkflowState({ taskId, action: WORKFLOW_ACTIONS.APPROVE, remarks });

export const rejectWorkflowItem = async ({ taskId, remarks }) =>
  transitionWorkflowState({ taskId, action: WORKFLOW_ACTIONS.REJECT, remarks });
