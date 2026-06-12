import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Badge } from "@/shared/ui/badge";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/shared/ui/breadcrumb";
import { Button } from "@/shared/ui/button";
import { CardSkeleton, PageHeaderSkeleton, TableSkeleton } from "@/shared/ui/skeletons";
import { BookOpen, Printer, User, UserRound } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/modules/identity_access";
import { essAPI } from "@/modules/ess";
import {
  generateServiceBookPrintModel,
} from "@/modules/service_book/services/serviceBookDomainService";
import { applyCanonicalPartIOverlay } from "@/modules/service_book/services/canonicalPartIOverlay";
import { serviceBookAPI } from "@/modules/service_book/api/serviceBookApi";
import ServiceBookLedgerScreen from "@/modules/service_book/containers/ServiceBookLedgerScreen";
import ServiceBookPrintScreen from "@/modules/service_book/containers/ServiceBookPrintScreen";

const ESS_VISIBLE_SERVICE_BOOK_STATUSES = ["APPROVED", "LOCKED"];

const readRouteErrorMessage = (error) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (typeof detail?.message === "string" && detail.message.trim()) return detail.message;
  if (typeof detail?.error === "string" && detail.error.trim()) return detail.error;
  if (typeof error?.message === "string" && error.message.trim()) return error.message;
  return "Employee not found";
};

export default function ServiceBookReadScreen({ essMode = false }) {
  const { user } = useAuth();
  const { employeeId: routeEmployeeId } = useParams();

  const [loading, setLoading] = useState(essMode);
  const [essProfile, setEssProfile] = useState(null);
  const [serviceBook, setServiceBook] = useState(null);
  const [identityInfo, setIdentityInfo] = useState(null);
  const [completionPct, setCompletionPct] = useState(0);
  const [routeLookupPending, setRouteLookupPending] = useState(Boolean(!essMode && routeEmployeeId));
  const [routeError, setRouteError] = useState(null);

  const targetEmployeeId = useMemo(() => {
    if (essMode) return essProfile?.employee_id || user?.employee_id || null;
    return routeEmployeeId || user?.employee_id || null;
  }, [essMode, essProfile, routeEmployeeId, user?.employee_id]);

  const employeeName = useMemo(() => {
    if (essMode) return essProfile?.full_name || targetEmployeeId;
    if (identityInfo?.name_in_block_letters) return identityInfo.name_in_block_letters;
    return routeEmployeeId ? null : user?.name;
  }, [essMode, essProfile, identityInfo, routeEmployeeId, user, targetEmployeeId]);

  const employeeCode = useMemo(() => {
    if (identityInfo?.employee_code) return identityInfo.employee_code;
    return serviceBook?.employee_code || null;
  }, [identityInfo, serviceBook]);

  const resolvedEmployeeId = identityInfo?.employee_id || targetEmployeeId;
  const visibleEntryStatuses = essMode ? ESS_VISIBLE_SERVICE_BOOK_STATUSES : undefined;

  const effectiveServiceBook = useMemo(() => {
    return applyCanonicalPartIOverlay(serviceBook, identityInfo);
  }, [serviceBook, identityInfo]);

  const loadPrintProjection = useCallback(async () => {
    if (!targetEmployeeId || routeLookupPending || routeError) return;
    try {
      const res = await generateServiceBookPrintModel({
        employeeId: targetEmployeeId,
        employeeOrType: essMode ? essProfile || "REGULAR" : "REGULAR",
        statuses: visibleEntryStatuses,
      });
      setServiceBook(res?.service_book || null);
    } catch {
      // Keep print surface optional.
    }
  }, [targetEmployeeId, routeLookupPending, routeError, essMode, essProfile, visibleEntryStatuses]);

  useEffect(() => {
    let active = true;
    if (!essMode) return undefined;

    const loadEssProfile = async () => {
      setLoading(true);
      try {
        const profileRes = await essAPI.getMyProfile().catch(() => ({ data: null }));
        if (!active) return;
        setEssProfile(profileRes.data || null);
      } catch {
        if (active) toast.error("Failed to load service book");
      } finally {
        if (active) setLoading(false);
      }
    };

    loadEssProfile();
    return () => {
      active = false;
    };
  }, [essMode]);

  useEffect(() => {
    if (essMode || !targetEmployeeId) {
      setRouteLookupPending(false);
      setRouteError(null);
      return;
    }
    let active = true;
    setRouteLookupPending(true);
    setRouteError(null);
    serviceBookAPI.getPartIDefaults(targetEmployeeId)
      .then((data) => {
        if (!active) return;
        setIdentityInfo(data);
        setRouteLookupPending(false);
      })
      .catch((error) => {
        if (!active) return;
        setIdentityInfo(null);
        setRouteLookupPending(false);
        if (error?.response?.status === 404) {
          setRouteError(readRouteErrorMessage(error));
        }
      });
    return () => { active = false; };
  }, [essMode, targetEmployeeId]);

  useEffect(() => {
    loadPrintProjection();
  }, [loadPrintProjection]);

  const handlePrintFullBook = () => {
    loadPrintProjection().then(() => {
      setTimeout(() => window.print(), 200);
    });
  };

  if (loading || routeLookupPending) {
    return (
      <>
        <div className="max-w-6xl mx-auto space-y-6" data-testid={essMode ? "ess-service-book-loading" : "service-book-loading"}>
          <PageHeaderSkeleton />
          <CardSkeleton lines={2} />
          <TableSkeleton rows={8} columns={4} />
        </div>
      </>
    );
  }

  if (!targetEmployeeId) {
    return (
      <>
        <div className="max-w-4xl mx-auto text-center py-12">
          {essMode ? <UserRound className="w-14 h-14 mx-auto mb-3 text-slate-300" /> : <User className="w-16 h-16 mx-auto mb-4 text-slate-300" />}
          <h2 className="text-xl font-semibold text-slate-900">No linked employee profile</h2>
          <p className="text-slate-500 mt-2">Your account is not linked to an employee profile yet.</p>
        </div>
      </>
    );
  }

  if (routeError) {
    return (
      <>
        <div className="max-w-4xl mx-auto text-center py-12" data-testid="service-book-error">
          <User className="w-16 h-16 mx-auto mb-4 text-slate-300" />
          <h2 className="text-xl font-semibold text-slate-900">Employee not found</h2>
          <p className="text-slate-500 mt-2">{routeError}</p>
        </div>
      </>
    );
  }

  const entryCount = serviceBook?._raw_entries?.length || 0;

  return (
    <>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in" data-testid={essMode ? "ess-service-book-page" : "service-book-page"}>
        <Breadcrumb className="no-print">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink asChild>
                <Link to={essMode ? "/ess" : "/portal/employees"}>
                  {essMode ? "Self-Service" : "Employees"}
                </Link>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            {!essMode && targetEmployeeId && (
              <>
                <BreadcrumbItem>
                  <BreadcrumbLink asChild>
                    <Link to={`/employees/${resolvedEmployeeId}`}>
                      {employeeName || employeeCode || targetEmployeeId}
                    </Link>
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
              </>
            )}
            <BreadcrumbItem>
              <BreadcrumbPage>Service Book</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        <div className="layer-1-official p-4 sm:p-6 service-book-print">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500">
                {essMode ? "Employee Self-Service Official Record" : "Official Record"}
              </p>
              <h2 className="text-2xl font-bold text-slate-900 font-service-book flex items-center gap-2">
                <BookOpen className="w-5 h-5" />
                Digital Service Book
                <Badge variant="outline" className="text-xs font-normal ml-1">{completionPct}% Complete</Badge>
              </h2>
              <p className="text-sm text-slate-600 mt-1">
                {employeeName || targetEmployeeId}
                {employeeCode && employeeName ? ` (${employeeCode})` : ""}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 no-print">
              {essMode && <Badge className="official-record-badge">Read-only</Badge>}
              {essMode && <Badge variant="outline">{entryCount} entries</Badge>}
              {essMode && <Badge variant="outline">{serviceBook?.parts_completed?.length || 0} parts</Badge>}
              <Button variant="outline" className="gap-2" onClick={() => window.print()} data-testid={essMode ? "ess-service-book-print-btn" : "service-book-print-btn"}>
                <Printer className="w-4 h-4" />
                Print
              </Button>
              <Button className="gap-2" onClick={handlePrintFullBook} data-testid={essMode ? "ess-service-book-print-full-btn" : "service-book-print-full-btn"}>
                <Printer className="w-4 h-4" />
                Print Full Book
              </Button>
            </div>
          </div>

          <ServiceBookLedgerScreen
            employeeId={targetEmployeeId}
            employeeName={employeeName}
            partIDefaults={identityInfo}
            forceReadOnly={essMode}
            onCompletionChange={setCompletionPct}
            entryStatuses={visibleEntryStatuses}
          />
        </div>
      </div>

      <ServiceBookPrintScreen
        serviceBook={effectiveServiceBook}
        employeeName={employeeName || targetEmployeeId}
        employeeId={targetEmployeeId}
      />
    </>
  );
}
