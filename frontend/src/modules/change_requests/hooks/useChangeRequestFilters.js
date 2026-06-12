import { useCallback, useMemo } from "react";
import { useUrlTableState } from "@/shared/lib/useUrlTableState";

// Status filter is URL-synced (?status=) so a filtered view is bookmarkable
// and survives refresh — same pattern as the directory and work queue.
const CHANGE_REQUEST_FILTERS = {
  status: { param: "status", defaultValue: "ALL" },
};

export function useChangeRequestFilters({ requests }) {
  const { values, setValue } = useUrlTableState({ filters: CHANGE_REQUEST_FILTERS });
  const statusFilter = values.status;
  const setStatusFilter = useCallback((value) => setValue("status", value), [setValue]);

  const filteredRequests = useMemo(() => {
    if (statusFilter === "ALL") return requests || [];
    return (requests || []).filter((request) => request.status === statusFilter);
  }, [requests, statusFilter]);

  const pendingCount = useMemo(
    () => (requests || []).filter((request) => request.status === "PENDING").length,
    [requests]
  );

  return {
    statusFilter,
    setStatusFilter,
    filteredRequests,
    pendingCount,
  };
}

export default useChangeRequestFilters;
