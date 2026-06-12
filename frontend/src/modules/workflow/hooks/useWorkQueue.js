import { useMemo } from "react";
import { useWorkflowQueueQuery } from "@/modules/workflow/hooks/useWorkflowQueueQuery";
import { useWorkflowQueueActions } from "@/modules/workflow/hooks/useWorkflowQueueActions";
import {
  selectCountsByStage,
  selectCountsByType,
  selectSlaCounts,
} from "@/modules/workflow/model/workflowQueueSelectors";

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
