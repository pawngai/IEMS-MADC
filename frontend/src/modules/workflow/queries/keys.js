/**
 * Query keys for the workflow context. The queue key carries the capability
 * snapshot it was built from, so role/permission changes produce a fresh
 * cache entry instead of serving another role's queue.
 */
export const workflowKeys = {
  all: ["workflow"],
  queue: (inputs) => [...workflowKeys.all, "queue", inputs],
};
