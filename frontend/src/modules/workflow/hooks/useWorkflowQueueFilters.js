import { useDeferredValue, useMemo, useState } from "react";
import {
  selectFilteredQueueItems,
  selectKanbanColumns,
} from "@/modules/workflow/model/workflowQueueSelectors";

export function useWorkflowQueueFilters({ items }) {
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [slaFilter, setSlaFilter] = useState("ALL");
  const deferredQuery = useDeferredValue(query);

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
