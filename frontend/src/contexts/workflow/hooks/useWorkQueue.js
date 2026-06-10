import { useMemo } from "react";
import { useWorkflowQueueQuery } from "@/contexts/workflow/hooks/useWorkflowQueueQuery";
import { useWorkflowQueueActions } from "@/contexts/workflow/hooks/useWorkflowQueueActions";
import {
  selectCountsByStage,
  selectCountsByType,
  selectSlaCounts,
} from "@/contexts/workflow/model/workflowQueueSelectors";

export default function useWorkQueue() {
  const { loading, refreshing, items, refresh, authority, authorityLabel } = useWorkflowQueueQuery();
  const { getActions, performAction } = useWorkflowQueueActions({ authority });

  const countsByStage = useMemo(() => selectCountsByStage(items), [items]);
  const countsByType = useMemo(() => selectCountsByType(items), [items]);
  const slaCounts = useMemo(() => selectSlaCounts(items), [items]);

  return {
    loading,
    refreshing,
    items,
    refresh,
    countsByStage,
    countsByType,
    slaCounts,
    authority,
    authorityLabel,
    getActions,
    performAction,
  };
}
