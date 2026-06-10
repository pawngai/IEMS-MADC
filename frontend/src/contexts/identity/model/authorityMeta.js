/**
 * Static authority display metadata — separated from the AuthProvider
 * so domain code can reference it without pulling in the full auth context.
 */

export const AUTHORITY_DISPLAY_NAMES = {
  EMPLOYEE: "Employee",
  DEPT_DATA_ENTRY: "Dept Data Entry Operator",
  GLOBAL_DATA_ENTRY: "Global Data Entry Operator",
  DEALING_ASSISTANT: "Dealing Clerk",
  SECTION_OFFICER: "Section Officer",
  VERIFIER: "Verifier",
  NODAL_OFFICER: "Nodal Officer",
  DDO: "DDO",
  APPROVING_AUTHORITY: "Approving Authority",
  HOD: "Head of Department",
  APPOINTING_AUTHORITY: "Appointing Authority",
  DISCIPLINARY_AUTHORITY: "Disciplinary Authority",
  AUDITOR: "Auditor",
  SYSTEM_ADMIN: "System Administrator",
};

export const AUTHORITY_PRIORITY = [
  "SYSTEM_ADMIN",
  "HOD",
  "APPROVING_AUTHORITY",
  "APPOINTING_AUTHORITY",
  "DISCIPLINARY_AUTHORITY",
  "DDO",
  "AUDITOR",
  "NODAL_OFFICER",
  "VERIFIER",
  "SECTION_OFFICER",
  "DEALING_ASSISTANT",
  "DEPT_DATA_ENTRY",
  "GLOBAL_DATA_ENTRY",
  "EMPLOYEE",
];
