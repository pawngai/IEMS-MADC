import React, { useCallback, useRef } from "react";
import { BookOpen, X } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import ServiceBookEntryList from "@/contexts/service_book/components/ServiceBookEntryList";
import ServiceBookEntryDetails from "@/contexts/service_book/components/ServiceBookEntryDetails";

const PART_KEYS = ["I", "II-A", "II-B", "III", "IV", "V", "VI", "VII", "VIII"];

const getPartData = (serviceBook, partKey) => {
  if (!serviceBook) return null;
  const keyMap = {
    I: "part_i",
    "II-A": "part_ii_a",
    "II-B": "part_ii_b",
    III: "part_iii",
    IV: "part_iv",
    V: "part_v",
    VI: "part_vi",
    VII: "part_vii",
    VIII: "part_viii",
  };
  return serviceBook[keyMap[partKey]];
};

export default function ServiceBookLedgerShell({
  employeeId,
  employeeName,
  onClose,
  activePart,
  onSelectPart,
  partsInfo,
  serviceBook,
  canWrite,
  canAddAuditComment,
  isSaving,
  onSavePart,
  onReload,
  onWorkflowAction,
  masterOptions,
  can,
  Permissions,
  forceReadOnly,
}) {
  const completionPct = serviceBook?.completion_percentage || 0;
  const dirtyRef = useRef(false);

  const handleSelectPart = useCallback((key) => {
    if (dirtyRef.current) {
      const confirmed = window.confirm("You have unsaved changes. Discard and switch parts?");
      if (!confirmed) return;
    }
    dirtyRef.current = false;
    onSelectPart(key);
  }, [onSelectPart]);

  return (
    <div className="space-y-3">
      <div className="flex flex-col lg:flex-row border border-slate-200 rounded-lg bg-white overflow-hidden min-h-[60vh] lg:min-h-[70vh]">
        <ServiceBookEntryList
          partKeys={PART_KEYS}
          activePart={activePart}
          onSelectPart={handleSelectPart}
          serviceBook={serviceBook}
          partsInfo={partsInfo}
          getPartData={getPartData}
          completionPct={completionPct}
        />

        <main className="flex-1 min-w-0 overflow-y-auto" role="tabpanel" aria-label={`Part ${activePart} content`}>
          <ServiceBookEntryDetails
            partKey={activePart}
            partInfo={partsInfo[activePart]}
            partData={getPartData(serviceBook, activePart)}
            employeeId={employeeId}
            onSave={(data) => onSavePart(activePart, data)}
            isSaving={isSaving}
            onReload={onReload}
            canWrite={canWrite}
            canAddAuditComment={canAddAuditComment}
            masterOptions={masterOptions}
            onWorkflowAction={onWorkflowAction}
            can={can}
            Permissions={Permissions}
            forceReadOnly={forceReadOnly}
            dirtyRef={dirtyRef}
          />
        </main>
      </div>
    </div>
  );
}
