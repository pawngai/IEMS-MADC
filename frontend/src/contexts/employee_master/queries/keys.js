/**
 * Query keys for the employee_master context. All keys are module-prefixed
 * arrays so cross-cutting invalidation can target the whole module via
 * `employeeMasterKeys.all`.
 */
export const employeeMasterKeys = {
  all: ["employee_master"],
  directoryList: (params) => [...employeeMasterKeys.all, "directory", "list", params],
  directoryReference: () => [...employeeMasterKeys.all, "directory", "reference"],
};
