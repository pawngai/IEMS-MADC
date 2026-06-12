/** Query keys for the audit context. */
export const auditKeys = {
  all: ["audit"],
  logs: (filters) => [...auditKeys.all, "logs", filters],
  stats: () => [...auditKeys.all, "stats"],
};
