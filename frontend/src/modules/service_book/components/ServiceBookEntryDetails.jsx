import React, { useEffect, useRef, useState } from "react";
import { FileText } from "lucide-react";
import {
  APPEND_ONLY_PARTS,
  PART_COLORS,
  PART_ICONS,
  PART_NAMES,
} from "@/modules/service_book/components/serviceBookLedger.constants";
import { formatLifecycleTimestamp } from "@/modules/service_book/components/serviceBookPartHelpers";
import ServiceBookActionBar from "@/modules/service_book/components/ServiceBookActionBar";
import renderPartContent from "@/modules/service_book/components/partContentFactory";

export default function ServiceBookEntryDetails({
  partKey,
  partInfo,
  partData,
  employeeId,
  onSave,
  isSaving,
  onReload,
  canWrite,
  canAddAuditComment,
  masterOptions,
  onWorkflowAction,
  can,
  Permissions,
  forceReadOnly,
  dirtyRef,
}) {
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState(partData || {});
  const isDirtyRef = useRef(false);

  const Icon = PART_ICONS[partKey] || FileText;
  const isAppendOnly = APPEND_ONLY_PARTS.has(partKey);
  const partCanWrite = false;
  const partWorkflowAction = undefined;
  const entryMeta = partData?._meta || null;
  const workflowState = entryMeta?.workflow_state || entryMeta?.status || null;

  useEffect(() => {
    setFormData(partData || {});
    setEditMode(false);
    isDirtyRef.current = false;
    if (dirtyRef) dirtyRef.current = false;
  }, [partKey, partData, dirtyRef]);

  const handleChange = (field, value) => {
    isDirtyRef.current = true;
    if (dirtyRef) dirtyRef.current = true;
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async (data) => {
    const ok = await onSave(data);
    if (ok) {
      setEditMode(false);
      isDirtyRef.current = false;
      if (dirtyRef) dirtyRef.current = false;
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-5 py-3 border-b border-slate-200 bg-slate-50/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-1.5 rounded-lg ${PART_COLORS[partKey]}`}>
              <Icon className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                Part {partKey}: {partInfo?.name || PART_NAMES[partKey]}
              </h3>
              <p className="text-xs text-slate-500">{partInfo?.description || ""}</p>
            </div>
          </div>

          <ServiceBookActionBar
            workflowState={workflowState}
            entryMeta={entryMeta}
            forceReadOnly={forceReadOnly}
            can={can}
            Permissions={Permissions}
            onWorkflowAction={partWorkflowAction}
            isSaving={isSaving}
            canWrite={partCanWrite}
            isAppendOnly={isAppendOnly}
            isInlineEditable={false}
            isEditable={false}
            hasPartData={!!partData}
            onEdit={undefined}
          />
        </div>

        {entryMeta && !forceReadOnly && (
          <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-400">
            {formatLifecycleTimestamp(entryMeta.created_at) && <span>Created: {formatLifecycleTimestamp(entryMeta.created_at)}</span>}
            {formatLifecycleTimestamp(entryMeta.submitted_at) && <span>Submitted: {formatLifecycleTimestamp(entryMeta.submitted_at)}</span>}
            {formatLifecycleTimestamp(entryMeta.verified_at) && <span>Verified: {formatLifecycleTimestamp(entryMeta.verified_at)}</span>}
            {formatLifecycleTimestamp(entryMeta.approved_at) && <span>Approved: {formatLifecycleTimestamp(entryMeta.approved_at)}</span>}
            {formatLifecycleTimestamp(entryMeta.locked_at) && <span>Locked: {formatLifecycleTimestamp(entryMeta.locked_at)}</span>}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-5">
        {renderPartContent({
          partKey,
          partData,
          editMode,
          formData,
          handleChange,
          onSave: handleSave,
          isSaving,
          setEditMode,
          employeeId,
          onReload,
          canWrite: partCanWrite,
          canAddAuditComment,
          masterOptions,
          onWorkflowAction: partWorkflowAction,
          can,
          Permissions,
          forceReadOnly,
        })}
      </div>
    </div>
  );
}
