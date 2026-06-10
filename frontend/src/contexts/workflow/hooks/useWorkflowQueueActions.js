import { useCallback } from "react";
import {
  activateIdentity,
  approveProfile,
  approveServiceBookOpening,
  approveServiceBookEntry,
  lockProfile,
  lockServiceBookEntry,
  rejectIdentity,
  rejectProfile,
  reviewChangeRequest,
  submitServiceBookOpening,
  submitIdentity,
  submitProfile,
  submitServiceBookEntry,
  verifyServiceBookOpening,
  verifyIdentity,
  verifyProfile,
  verifyServiceBookEntry,
} from "@/contexts/workflow/model/workQueueGateway";

const DATA_ENTRY_AUTHORITIES = ["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT", "SECTION_OFFICER"];
const IDENTITY_DATA_ENTRY_AUTHORITIES = ["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"];

export function useWorkflowQueueActions({ authority }) {
  const getActions = useCallback(
    (item) => {
      if (!item) return [];

      if (item.type === "ess") {
        return [{ id: "ess-open", label: "Open Profile", variant: "default", requiresRemarks: false }];
      }

      if (item.type === "profile") {
        if (
          DATA_ENTRY_AUTHORITIES.includes(authority) &&
          ["DRAFT", "REJECTED"].includes(item.stage) &&
          item.raw?.employee_section_completed &&
          item.raw?.data_entry_section_completed
        ) {
          return [{ id: "profile-submit", label: "Submit", variant: "default", requiresRemarks: false }];
        }

        if (authority === "VERIFIER" && item.stage === "SUBMITTED") {
          return [
            { id: "profile-verify", label: "Verify", variant: "default", requiresRemarks: false },
            { id: "profile-reject", label: "Reject", variant: "destructive", requiresRemarks: true },
          ];
        }

        if (authority === "APPROVING_AUTHORITY" && item.stage === "VERIFIED") {
          return [
            { id: "profile-approve", label: "Approve", variant: "default", requiresRemarks: false },
            { id: "profile-reject", label: "Reject", variant: "destructive", requiresRemarks: true },
          ];
        }

        if (
          ["APPROVING_AUTHORITY", "HOD"].includes(authority) &&
          item.stage === "APPROVED"
        ) {
          return [{ id: "profile-lock", label: "Lock", variant: "default", requiresRemarks: false }];
        }

        return [];
      }

      if (item.type === "identity") {
        if (IDENTITY_DATA_ENTRY_AUTHORITIES.includes(authority) && ["DRAFT", "REJECTED"].includes(item.stage)) {
          return [{ id: "identity-submit", label: "Submit", variant: "default", requiresRemarks: false }];
        }

        if (authority === "VERIFIER" && item.stage === "SUBMITTED") {
          return [
            { id: "identity-verify", label: "Verify", variant: "default", requiresRemarks: false },
            { id: "identity-reject", label: "Reject", variant: "destructive", requiresRemarks: true },
          ];
        }

        if (authority === "APPROVING_AUTHORITY" && item.stage === "VERIFIED") {
          return [
            { id: "identity-activate", label: "Activate", variant: "default", requiresRemarks: false },
            { id: "identity-reject", label: "Reject", variant: "destructive", requiresRemarks: true },
          ];
        }

        return [];
      }

      if (item.type === "service") {
        if (DATA_ENTRY_AUTHORITIES.includes(authority) && ["DRAFT", "REJECTED"].includes(item.stage)) {
          return [
            { id: "service-submit", label: "Submit", variant: "default", requiresRemarks: false },
          ];
        }
        if (authority === "VERIFIER" && item.stage === "SUBMITTED") {
          return [
            { id: "service-verify", label: "Verify", variant: "default", requiresRemarks: false },
            { id: "service-reject", label: "Reject", variant: "destructive", requiresRemarks: true },
          ];
        }
        if (["APPROVING_AUTHORITY", "DDO"].includes(authority) && item.stage === "VERIFIED") {
          return [
            { id: "service-approve", label: "Approve", variant: "default", requiresRemarks: false },
            { id: "service-reject", label: "Reject", variant: "destructive", requiresRemarks: true },
          ];
        }
        if (["APPROVING_AUTHORITY", "HOD", "APPOINTING_AUTHORITY", "DISCIPLINARY_AUTHORITY"].includes(authority) && item.stage === "APPROVED") {
          return [
            { id: "service-attest", label: "Lock / Attest", variant: "default", requiresRemarks: false },
          ];
        }
      }

      if (item.type === "service_opening") {
        if (DATA_ENTRY_AUTHORITIES.includes(authority) && ["DRAFT", "REJECTED"].includes(item.stage)) {
          return [
            { id: "service-opening-submit", label: "Submit", variant: "default", requiresRemarks: false },
          ];
        }
        if (authority === "VERIFIER" && item.stage === "SUBMITTED") {
          return [
            { id: "service-opening-verify", label: "Verify", variant: "default", requiresRemarks: false },
          ];
        }
        if (["APPROVING_AUTHORITY", "DDO"].includes(authority) && item.stage === "VERIFIED") {
          return [
            { id: "service-opening-approve", label: "Approve", variant: "default", requiresRemarks: false },
          ];
        }
      }

      if (item.type === "change_request") {
        return [
          { id: "cr-approve", label: "Approve", variant: "default", requiresRemarks: false },
          { id: "cr-reject", label: "Reject", variant: "destructive", requiresRemarks: true },
        ];
      }

      return [];
    },
    [authority]
  );

  const performAction = useCallback(async (item, actionId, remarks = "") => {
    if (!item) throw new Error("No item");

    if (item.type === "profile") {
      if (actionId === "profile-submit") await submitProfile(item.employeeId, remarks);
      if (actionId === "profile-verify") await verifyProfile(item.employeeId, remarks);
      if (actionId === "profile-approve") await approveProfile(item.employeeId, remarks);
      if (actionId === "profile-lock") await lockProfile(item.employeeId, remarks);
      if (actionId === "profile-reject") await rejectProfile(item.employeeId, remarks);
      return;
    }

    if (item.type === "identity") {
      if (actionId === "identity-submit") await submitIdentity(item.employeeId, remarks);
      if (actionId === "identity-verify") await verifyIdentity(item.employeeId, remarks);
      if (actionId === "identity-activate") await activateIdentity(item.employeeId, remarks);
      if (actionId === "identity-reject") await rejectIdentity(item.employeeId, remarks);
      return;
    }

    if (item.type === "service") {
      const entryId = item.raw?.id;
      if (actionId === "service-submit") await submitServiceBookEntry(entryId, remarks);
      if (actionId === "service-verify") await verifyServiceBookEntry(entryId, remarks);
      if (actionId === "service-approve") await approveServiceBookEntry(entryId, remarks);
      if (actionId === "service-attest") await lockServiceBookEntry(entryId, remarks);
      return;
    }

    if (item.type === "service_opening") {
      if (actionId === "service-opening-submit") await submitServiceBookOpening(item.employeeId, remarks);
      if (actionId === "service-opening-verify") await verifyServiceBookOpening(item.employeeId, remarks);
      if (actionId === "service-opening-approve") await approveServiceBookOpening(item.employeeId, remarks);
      return;
    }

    if (item.type === "change_request") {
      const requestId = item.raw?.id || item.raw?.request_id;
      if (actionId === "cr-approve") await reviewChangeRequest(requestId, "APPROVE", remarks);
      if (actionId === "cr-reject") await reviewChangeRequest(requestId, "REJECT", remarks);
    }
  }, []);

  return { getActions, performAction };
}

export default useWorkflowQueueActions;
