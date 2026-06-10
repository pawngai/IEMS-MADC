import { useMemo, useState } from "react";

export function useChangeRequestFilters({ requests }) {
  const [statusFilter, setStatusFilter] = useState("ALL");

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
