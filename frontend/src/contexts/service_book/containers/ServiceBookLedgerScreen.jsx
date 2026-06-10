import { useEffect, useState } from "react";
import { AlertCircle, BookOpen, X } from "lucide-react";
import { useAuth } from "@/contexts/identity";
import { mastersAPI } from "@/contexts/masters";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { CardSkeleton, TableSkeleton } from "@/shared/ui/skeletons";
import { Skeleton } from "@/shared/ui/skeleton";
import ServiceBookLedgerShell from "@/contexts/service_book/components/ServiceBookLedgerShell";
import { useServiceBookProjection } from "@/contexts/service_book/hooks/useServiceBookProjection";
import { applyCanonicalPartIOverlay } from "@/contexts/service_book/services/canonicalPartIOverlay";

const LedgerLoadingState = () => (
  <div className="space-y-4" data-testid="service-book-ledger-loading">
    <div className="rounded-xl border bg-white/80 p-4 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <Skeleton className="h-5 w-40 rounded" />
          <Skeleton className="h-4 w-56 rounded" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-24 rounded-md" />
          <Skeleton className="h-8 w-28 rounded-md" />
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Skeleton className="h-8 rounded-md" />
        <Skeleton className="h-8 rounded-md" />
        <Skeleton className="h-8 rounded-md" />
        <Skeleton className="h-8 rounded-md" />
      </div>
    </div>
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[220px_minmax(0,1fr)]">
      <CardSkeleton lines={7} />
      <div className="space-y-4">
        <CardSkeleton lines={4} />
        <TableSkeleton rows={6} columns={4} />
      </div>
    </div>
  </div>
);

export default function ServiceBookLedgerScreen({ employeeId, employeeName, partIDefaults = null, onClose, forceReadOnly = false, onCompletionChange, entryStatuses }) {
  const { user, loading: authLoading, can, Permissions } = useAuth();
  const officialProjectionMode = true;
  const effectiveReadOnly = forceReadOnly || officialProjectionMode;
  const [activePart, setActivePart] = useState("I");

  const canReadAll = can(Permissions.SERVICE_BOOK_READ_ALL) || can(Permissions.AUDIT_READ_ALL);
  const canReadOwn = can(Permissions.SERVICE_BOOK_READ_OWN) && user?.employee_id === employeeId;
  const canRead = canReadAll || canReadOwn;

  const canWrite = false;
  const canAddAuditComment = false;

  const { serviceBook, partsInfo, isLoading, notApplicable, reloadServiceBook } = useServiceBookProjection({
    employeeId,
    canRead: !authLoading && canRead,
    statuses: entryStatuses,
  });
  const effectiveServiceBook = applyCanonicalPartIOverlay(serviceBook, partIDefaults);
  const [isSaving] = useState(false);

  useEffect(() => {
    if (onCompletionChange) onCompletionChange(effectiveServiceBook?.completion_percentage || 0);
  }, [effectiveServiceBook?.completion_percentage, onCompletionChange]);

  const handleSavePart = async () => false;

  const handleWorkflowAction = async () => undefined;

  const [masterOptions, setMasterOptions] = useState({
    eventTypes: [],
    leaveTypes: [],
    casteCategories: [],
    payLevels: [],
  });

  useEffect(() => {
    const loadMasters = async () => {
      try {
        const [eventRes, leaveRes, casteRes, payRes] = await Promise.all([
          mastersAPI.getServiceEventTypes().catch(() => ({ data: [] })),
          mastersAPI.getLeaveTypes().catch(() => ({ data: [] })),
          mastersAPI.getCasteCategories().catch(() => ({ data: [] })),
          mastersAPI.getPayLevels().catch(() => ({ data: [] })),
        ]);

        const eventTypes = (eventRes.data || []).map((event) => ({
          value: event.event_code || event.code,
          label: event.description ? `${event.description} (${event.event_code || event.code})` : event.event_code || event.code,
          search: `${event.description || ""} ${event.event_code || ""} ${event.code || ""}`,
        }));

        const leaveTypes = (leaveRes.data || []).map((lt) => {
          const code = lt.leave_code || lt.code;
          return {
            value: code,
            label: lt.description ? `${lt.description} (${code})` : code,
            search: `${lt.description || ""} ${code || ""}`,
          };
        });

        const casteCategories = (casteRes.data || []).map((cat) => ({
          value: cat.code || cat.category_code,
          label: cat.description || cat.code || cat.category_code,
          search: `${cat.description || ""} ${cat.code || ""} ${cat.category_code || ""}`,
        }));

        const payLevels = (payRes.data || []).map((level) => ({
          value: level.code,
          label: level.basic_min
            ? `${level.description || level.code} (${level.basic_min}-${level.basic_max})`
            : level.description || level.code,
          search: `${level.description || ""} ${level.code || ""}`,
        }));

        setMasterOptions({ eventTypes, leaveTypes, casteCategories, payLevels });
      } catch {
        // non-fatal: part components can still render without master labels
      }
    };

    if (!authLoading && canRead) {
      loadMasters();
    }
  }, [authLoading, canRead]);

  if (authLoading) {
    return <LedgerLoadingState />;
  }

  if (!canRead) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-gray-400" />
              Service Book
            </h2>
            <p className="text-sm text-gray-500 mt-1">{employeeName || employeeId}</p>
          </div>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-800 mb-2">Access Denied</h3>
          <p className="text-red-700">You do not have permission to view this Service Book.</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return <LedgerLoadingState />;
  }

  if (notApplicable) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-gray-400" />
              Service Book
            </h2>
            <p className="text-sm text-gray-500 mt-1">{employeeName || employeeId}</p>
          </div>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 text-center">
          <AlertCircle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-amber-800 mb-2">Service Book Not Applicable</h3>
          <p className="text-amber-700 mb-4">{notApplicable.message}</p>
          <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300">
            Employment Type: {notApplicable.employment_type}
          </Badge>
          <p className="text-sm text-amber-600 mt-4">
            Service Books are only maintained for <strong>REGULAR</strong> employees as per government rules.
          </p>
        </div>
      </div>
    );
  }

  return (
    <ServiceBookLedgerShell
      employeeId={employeeId}
      employeeName={employeeName}
      onClose={onClose}
      activePart={activePart}
      onSelectPart={setActivePart}
      partsInfo={partsInfo}
      serviceBook={effectiveServiceBook}
      canWrite={canWrite}
      canAddAuditComment={canAddAuditComment}
      isSaving={isSaving}
      onSavePart={handleSavePart}
      onReload={reloadServiceBook}
      onWorkflowAction={handleWorkflowAction}
      masterOptions={masterOptions}
      can={can}
      Permissions={Permissions}
      forceReadOnly={effectiveReadOnly}
    />
  );
}
