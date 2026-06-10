import { getEmployeeCompletionStatus } from "@/shared/lib/utils";

const DATA_ENTRY_PROFILE_AUTHORITIES = ["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT", "SECTION_OFFICER"];
const VERIFIER_PROFILE_AUTHORITIES = ["VERIFIER"];
const APPROVER_PROFILE_AUTHORITIES = ["APPROVING_AUTHORITY"];
const LOCKER_PROFILE_AUTHORITIES = ["APPROVING_AUTHORITY", "HOD"];

export const getProfileQueueStagesForAuthority = (authority) => {
  if (DATA_ENTRY_PROFILE_AUTHORITIES.includes(authority)) return ["DRAFT", "REJECTED"];
  if (VERIFIER_PROFILE_AUTHORITIES.includes(authority)) return ["SUBMITTED"];
  if (APPROVER_PROFILE_AUTHORITIES.includes(authority)) return ["VERIFIED", "APPROVED"];
  if (LOCKER_PROFILE_AUTHORITIES.includes(authority)) return ["APPROVED"];
  return [];
};

export const shouldQueueProfileItem = (profile, stage) => {
  const requestedStage = String(stage || "").trim().toUpperCase();
  const profileWorkflowStatus = String(profile?.workflow_status || "").trim().toUpperCase();
  if (!requestedStage || profileWorkflowStatus !== requestedStage) return false;

  if (requestedStage !== "DRAFT") return true;

  const identityWorkflowStatus = String(profile?.identity_workflow_status || "").trim().toUpperCase();
  if (identityWorkflowStatus && identityWorkflowStatus !== "ACTIVE") return false;

  const employeeCompletion = getEmployeeCompletionStatus(profile);
  const explicitEmployeeStarted = typeof profile?.employee_section_completed === "boolean"
    ? profile.employee_section_completed
    : null;
  const employeeStarted = explicitEmployeeStarted ?? (employeeCompletion.known ? employeeCompletion.complete : true);
  const dataEntryStarted = typeof profile?.data_entry_section_completed === "boolean"
    ? profile.data_entry_section_completed
    : Boolean(profile?.data_entry_section_completed);

  return employeeStarted || dataEntryStarted;
};

export const filterQueuedProfilesByStage = (profiles, stage) => (
  Array.isArray(profiles) ? profiles.filter((profile) => shouldQueueProfileItem(profile, stage)) : []
);
