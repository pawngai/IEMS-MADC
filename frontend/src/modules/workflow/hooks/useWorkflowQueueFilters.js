import { useCallback, useDeferredValue, useMemo } from "react";
import { useUrlTableState } from "@/shared/lib/useUrlTableState";
import {
  selectFilteredQueueItems,
  selectKanbanColumns,
} from "@/modules/workflow/model/workflowQueueSelectors";

// Queue filters live in the URL so a filtered queue view can be bookmarked,
// shared, and survives refresh (same pattern as the employee directory).
const QUEUE_FILTERS = {
  query: { param: "q", defaultValue: "" },
  type: { param: "type", defaultValue: "ALL" },
  sla: { param: "sla", defaultValue: "ALL" },
};

export function useWorkflowQueueFilters({ items }) {
  const { values, setValue } = useUrlTableState({ filters: QUEUE_FILTERS });
  const { query, type: typeFilter, sla: slaFilter } = values;
  const deferredQuery = useDeferredValue(query);

  const setQuery = useCallback((value) => setValue("query", value), [setValue]);
  const setTypeFilter = useCallback((value) => setValue("type", value), [setValue]);
  const setSlaFilter = useCallback((value) => setValue("sla", value), [setValue]);

  const filteredItems = useMemo(
    () =>
      selectFilteredQueueItems({
        items,
        query: deferredQuery,
        typeFilter,
        slaFilter,
      }),
    [items, deferredQuery, typeFilter, slaFilter]
  );

  const kanbanColumns = useMemo(
    () => selectKanbanColumns(filteredItems),
    [filteredItems]
  );

  return {
    query,
    setQuery,
    typeFilter,
    setTypeFilter,
    slaFilter,
    setSlaFilter,
    filteredItems,
    kanbanColumns,
  };
}

export default useWorkflowQueueFilters;
