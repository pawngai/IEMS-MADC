import React from "react";
import PartIContent from "@/modules/service_book/components/ledger/PartIContent";
import PartIIAContent from "@/modules/service_book/components/ledger/PartIIAContent";
import PartIIBContent from "@/modules/service_book/components/ledger/PartIIBContent";
import PartIIIContent from "@/modules/service_book/components/ledger/PartIIIContent";
import PartIVContent from "@/modules/service_book/components/ledger/PartIVContent";
import PartVContent from "@/modules/service_book/components/ledger/PartVContent";
import PartVIContent from "@/modules/service_book/components/ledger/PartVIContent";
import PartVIIContent from "@/modules/service_book/components/ledger/PartVIIContent";
import PartVIIIContent from "@/modules/service_book/components/ledger/PartVIIIContent";
import GenericPartContent from "@/modules/service_book/components/ledger/GenericPartContent";

export default function renderPartContent({
  partKey,
  partData,
  editMode,
  formData,
  handleChange,
  onSave,
  isSaving,
  setEditMode,
  employeeId,
  onReload,
  canWrite,
  canAddAuditComment,
  masterOptions,
  onWorkflowAction,
  can,
  Permissions,
  forceReadOnly,
}) {
  switch (partKey) {
    case "I":
      return (
        <PartIContent
          data={partData}
          casteCategoryOptions={masterOptions?.casteCategories || []}
        />
      );
    case "II-A":
      return (
        <PartIIAContent
          data={partData}
        />
      );
    case "II-B":
      return (
        <PartIIBContent
          data={partData}
        />
      );
    case "IV":
      return (
        <PartIVContent
          data={partData}
          employeeId={employeeId}
          onReload={onReload}
          canWrite={canWrite}
          eventTypeOptions={masterOptions?.eventTypes || []}
          payLevelOptions={masterOptions?.payLevels || []}
          onWorkflowAction={onWorkflowAction}
          can={can}
          Permissions={Permissions}
        />
      );
    case "VI":
      return (
        <PartVIContent
          data={partData}
          employeeId={employeeId}
          onReload={onReload}
          canWrite={canWrite}
          leaveTypeOptions={masterOptions?.leaveTypes || []}
          onWorkflowAction={onWorkflowAction}
          can={can}
          Permissions={Permissions}
        />
      );
    case "VIII":
      return (
        <PartVIIIContent
          data={partData}
          employeeId={employeeId}
          onReload={onReload}
          canAddAuditComment={canAddAuditComment}
          onWorkflowAction={onWorkflowAction}
          can={can}
          Permissions={Permissions}
        />
      );
    case "III":
      return (
        <PartIIIContent
          data={partData}
        />
      );
    case "V":
      return (
        <PartVContent
          data={partData}
          employeeId={employeeId}
          onReload={onReload}
          canWrite={canWrite}
          onWorkflowAction={onWorkflowAction}
          can={can}
          Permissions={Permissions}
        />
      );
    case "VII":
      return (
        <PartVIIContent
          data={partData}
          employeeId={employeeId}
          onReload={onReload}
          canWrite={canWrite}
          onWorkflowAction={onWorkflowAction}
          can={can}
          Permissions={Permissions}
        />
      );
    default:
      return <GenericPartContent data={partData} partKey={partKey} editMode={editMode} canWrite={canWrite && !forceReadOnly} />;
  }
}
