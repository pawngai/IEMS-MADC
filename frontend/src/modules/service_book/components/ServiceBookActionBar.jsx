import React from "react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { WorkflowActions, WorkflowStatusBadge } from "@/modules/service_book/components/serviceBookWorkflowUi";

export default function ServiceBookActionBar({
  workflowState,
  entryMeta,
  forceReadOnly,
  can,
  Permissions,
  onWorkflowAction,
  isSaving,
  canWrite,
  isAppendOnly,
  isInlineEditable,
  isEditable,
  hasPartData,
  onEdit,
}) {
  return (
    <div className="flex items-center gap-2">
      {workflowState && <WorkflowStatusBadge status={workflowState} />}

      {!forceReadOnly && entryMeta && can && Permissions && onWorkflowAction && (
        <WorkflowActions
          meta={entryMeta}
          onAction={onWorkflowAction}
          disabled={isSaving}
          can={can}
          Permissions={Permissions}
        />
      )}

      {!canWrite && <Badge variant="outline" className="text-xs">Read-only</Badge>}
      {canWrite && isAppendOnly && <Badge variant="outline" className="text-xs">Append-only</Badge>}

      {!forceReadOnly && !isSaving && !isAppendOnly && canWrite && isInlineEditable && (isEditable || !entryMeta) && (
        <Button variant="outline" size="sm" onClick={onEdit}>
          {hasPartData ? "Edit" : "Add Data"}
        </Button>
      )}
    </div>
  );
}
