import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import Layout from "@/app/layout/Layout";
import { documentsAPI } from "@/contexts/documents";
import { useAuth } from "@/contexts/identity_access";
import { usePermissions } from "@/contexts/identity_access";
import { essAPI } from "@/contexts/ess";
import { leaveAPI } from "@/contexts/leave/api/leaveApi";
import { employeeIdentityApi } from "@/contexts/employee_master";
import { Permissions } from "@/platform/permissions";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { Checkbox } from "@/shared/ui/checkbox";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { CardSkeleton, PageHeaderSkeleton, StatGridSkeleton, TableSkeleton } from "@/shared/ui/skeletons";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { Textarea } from "@/shared/ui/textarea";
import { SearchableSelect } from "@/shared/ui/searchable-select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { getApiErrorMessage, getLeaveTypeUnavailableMessage } from "@/shared/lib/utils";
import { toast } from "sonner";
import { ArrowLeft, Calendar, CheckCircle2, Clock, Inbox, XCircle, RefreshCw } from "lucide-react";
import { LeaveStatusBadge } from "@/contexts/leave/components/LeaveStatusBadge";
import LeaveSupportingDocumentsField from "@/contexts/leave/components/LeaveSupportingDocumentsField";
import LeaveActionDialog from "@/contexts/leave/components/LeaveActionDialog";
import { EMPLOYEE, resolveScopeAccess } from "@/contexts/access_control";
import {
  buildLeaveApplicationPayload,
  COMMUTED_LEAVE_BASIS_OPTIONS,
  createInitialLeaveApplyForm,
  getLeaveEligibilityValidationMessage,
  getLeaveSupportingDocumentRecommendation,
  getLeaveSupportingDocumentRequirementMessage,
  getLeaveSupportingDocumentValidationMessage,
  isChildCareLeave,
  isCommutedLeave,
  isMaternityLeave,
  isPaternityLeave,
} from "@/contexts/leave/model/leaveApplyForm";

const formatDate = (isoDate) => {
  if (!isoDate) return "";
  const d = new Date(isoDate + "T00:00:00");
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
};

const BALANCE_CARD_STYLES = {
  EL:  { bg: "bg-emerald-50", iconBg: "bg-emerald-100", iconColor: "text-emerald-600", accent: "border-l-emerald-500" },
  HPL: { bg: "bg-violet-50",  iconBg: "bg-violet-100",  iconColor: "text-violet-600",  accent: "border-l-violet-500" },
  CML: { bg: "bg-cyan-50",    iconBg: "bg-cyan-100",    iconColor: "text-cyan-600",    accent: "border-l-cyan-500" },
  LND: { bg: "bg-sky-50",     iconBg: "bg-sky-100",     iconColor: "text-sky-600",     accent: "border-l-sky-500" },
  CL:  { bg: "bg-amber-50",   iconBg: "bg-amber-100",   iconColor: "text-amber-600",   accent: "border-l-amber-500" },
};
const DEFAULT_CARD_STYLE = { bg: "bg-slate-50", iconBg: "bg-slate-100", iconColor: "text-slate-600", accent: "border-l-slate-500" };
const LEAVE_TYPE_LABELS = { EL: "Earned Leave", HPL: "Half Pay Leave", CML: "Commuted Leave", LND: "Leave Not Due", CL: "Casual Leave" };

const extractBalanceMap = (response) => response?.data?.balances || response?.balances || {};

const extractAttachmentFilename = (attachment) => {
  const filename = String(attachment?.filename || "").trim();
  if (filename) return filename;
  const directUrl = String(attachment?.url || "").trim();
  if (directUrl.startsWith("/api/documents/files/")) {
    return directUrl.slice("/api/documents/files/".length).split("/")[0] || "";
  }
  return "";
};

const LeaveAttachmentLinks = ({ attachments = [] }) => {
  const visibleAttachments = (attachments || []).filter((attachment) => extractAttachmentFilename(attachment));

  if (visibleAttachments.length === 0) {
    return null;
  }

  return (
    <div className="mt-1.5 flex flex-wrap gap-1.5">
      {visibleAttachments.map((attachment, index) => {
        const filename = extractAttachmentFilename(attachment);
        const label = attachment?.original_name || attachment?.filename || `Attachment ${index + 1}`;
        return (
          <button
            type="button"
            key={`${attachment?.filename || attachment?.url || "attachment"}-${index}`}
            onClick={() => documentsAPI.openDocument(filename)}
            className="inline-flex items-center rounded-full border border-slate-200 px-2.5 py-0.5 text-[11px] font-medium text-slate-600 hover:bg-slate-50"
          >
            {label}
          </button>
        );
      })}
    </div>
  );
};

const LeaveDashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const { can, canAccessModule } = usePermissions();
  const leaveModuleEnabled = canAccessModule("leave");
  const canApply = leaveModuleEnabled && can(Permissions.LEAVE_APPLY_OWN);
  const canReadOwn = leaveModuleEnabled && can(Permissions.LEAVE_READ_OWN);
  const canReadAll = leaveModuleEnabled && can(Permissions.LEAVE_READ_ALL);
  const canRecommend = leaveModuleEnabled && can(Permissions.LEAVE_RECOMMEND);
  const canSanction = leaveModuleEnabled && can(Permissions.LEAVE_SANCTION);
  const leaveApplyScope = resolveScopeAccess(user);
  const isEmployeeSelf = leaveApplyScope.scope === EMPLOYEE;
  const canApplySelf = canApply && isEmployeeSelf && leaveApplyScope.allowed;
  const selectedEmployeeId = (searchParams.get("employee_id") || "").trim();
  const canViewEmployeeHistory = leaveModuleEnabled && (canReadAll || canRecommend || canSanction);
  const isEmployeeHistoryMode = Boolean(selectedEmployeeId && canViewEmployeeHistory);
  const employeeHistoryReturnPath = location.state?.returnTo || "";

  const [profile, setProfile] = useState(null);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [balances, setBalances] = useState({});
  const [myLeaves, setMyLeaves] = useState([]);
  const [selectedEmployeeLeaves, setSelectedEmployeeLeaves] = useState([]);
  const [selectedEmployeeBalances, setSelectedEmployeeBalances] = useState({});
  const [selectedEmployeeInfo, setSelectedEmployeeInfo] = useState(null);
  const [selectedEmployeeLeaveType, setSelectedEmployeeLeaveType] = useState("");
  const [employeeHistorySearchQuery, setEmployeeHistorySearchQuery] = useState("");
  const [employeeHistorySearchResults, setEmployeeHistorySearchResults] = useState([]);
  const [employeeHistorySearchLoading, setEmployeeHistorySearchLoading] = useState(false);
  const [pendingRecommend, setPendingRecommend] = useState([]);
  const [pendingSanction, setPendingSanction] = useState([]);
  const [leaveTypeUnavailableMessage, setLeaveTypeUnavailableMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const [applyForm, setApplyForm] = useState(createInitialLeaveApplyForm);
  const [submitting, setSubmitting] = useState(false);

  const [actionDialog, setActionDialog] = useState({ open: false, action: null, record: null });

  const daysApplied = useMemo(() => {
    if (!applyForm.from_date || !applyForm.to_date) return 0;
    const start = new Date(applyForm.from_date);
    const end = new Date(applyForm.to_date);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;
    const diffMs = end - start;
    if (diffMs < 0) return 0;
    return Math.floor(diffMs / (1000 * 60 * 60 * 24)) + 1;
  }, [applyForm.from_date, applyForm.to_date]);

  const selectedBalance = balances?.[applyForm.leave_type_code];
  const leaveTypeOptions = useMemo(
    () =>
      leaveTypes.map((lt) => {
        const code = lt.leave_code || lt.code;
        return {
          value: code,
          label: lt.description ? `${lt.description} (${code})` : code,
          search: `${lt.description || ""} ${code || ""}`,
        };
      }),
    [leaveTypes]
  );
  const employeeHistoryLeaveTypeOptions = useMemo(() => {
    const seen = new Set();

    return selectedEmployeeLeaves
      .map((leave) => leave.leave_type_code)
      .filter((code) => {
        if (!code || seen.has(code)) return false;
        seen.add(code);
        return true;
      })
      .sort((left, right) => left.localeCompare(right))
      .map((code) => ({
        value: code,
        label: LEAVE_TYPE_LABELS[code] ? `${LEAVE_TYPE_LABELS[code]} (${code})` : code,
        search: `${LEAVE_TYPE_LABELS[code] || ""} ${code}`,
      }));
  }, [selectedEmployeeLeaves]);
  const filteredSelectedEmployeeLeaves = useMemo(() => {
    if (!selectedEmployeeLeaveType) return selectedEmployeeLeaves;
    return selectedEmployeeLeaves.filter((leave) => leave.leave_type_code === selectedEmployeeLeaveType);
  }, [selectedEmployeeLeaveType, selectedEmployeeLeaves]);
  const selectedEmployeeLeaveSummary = useMemo(() => {
    const summary = {
      totalApplications: selectedEmployeeLeaves.length,
      totalDays: 0,
      sanctionedCount: 0,
      pendingCount: 0,
      rejectedCount: 0,
      cancelledCount: 0,
      leaveTypeCounts: {},
    };

    selectedEmployeeLeaves.forEach((leave) => {
      const leaveTypeCode = leave.leave_type_code || "Unknown";
      summary.totalDays += Number(leave.days_applied) || 0;
      summary.leaveTypeCounts[leaveTypeCode] = (summary.leaveTypeCounts[leaveTypeCode] || 0) + 1;

      if (leave.status === "SANCTIONED") {
        summary.sanctionedCount += 1;
      } else if (leave.status === "SUBMITTED" || leave.status === "RECOMMENDED") {
        summary.pendingCount += 1;
      } else if (leave.status === "REJECTED") {
        summary.rejectedCount += 1;
      } else if (leave.status === "CANCELLED") {
        summary.cancelledCount += 1;
      }
    });

    summary.leaveTypeEntries = Object.entries(summary.leaveTypeCounts)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([leaveTypeCode, count]) => ({ leaveTypeCode, count }));

    return summary;
  }, [selectedEmployeeLeaves]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (isEmployeeSelf && (canApply || canReadOwn)) {
        const profileRes = await essAPI.getMyProfile().catch((error) => ({ data: null, error }));
        const profileData = profileRes.data || null;
        setProfile(profileData);

        let leaveTypeError = null;

        if (user?.employee_id) {
          const balanceRes = await leaveAPI.getBalances(user.employee_id).catch((error) => ({
            data: { balances: {} },
            error,
          }));
          const fetchedBalances = extractBalanceMap(balanceRes);
          setBalances(fetchedBalances);
          setLeaveTypes(Object.values(fetchedBalances));
          leaveTypeError = balanceRes.error || null;
          setLeaveTypeUnavailableMessage(
            Object.keys(fetchedBalances).length > 0
              ? ""
              : getLeaveTypeUnavailableMessage({
                  userEmployeeId: user.employee_id,
                  profile: profileData,
                  errorOrDetail: leaveTypeError || profileRes.error,
                })
          );
        } else {
          setBalances({});
          setLeaveTypes([]);
          setLeaveTypeUnavailableMessage(
            getLeaveTypeUnavailableMessage({ profile: profileData, errorOrDetail: profileRes.error })
          );
        }

        if (canReadOwn) {
          const myRes = await leaveAPI.listMy().catch(() => ({ data: [] }));
          setMyLeaves(myRes.data || []);
        }
      }

      if (canRecommend) {
        const pendingRes = await leaveAPI.list({ status: "SUBMITTED" }).catch(() => ({ data: [] }));
        setPendingRecommend(pendingRes.data || []);
      }
      if (canSanction) {
        const pendingRes = await leaveAPI.list({ status: "RECOMMENDED" }).catch(() => ({ data: [] }));
        setPendingSanction(pendingRes.data || []);
      }
      if (selectedEmployeeId && canViewEmployeeHistory) {
        const [employeeHistoryRes, empBalanceRes, empIdentity] = await Promise.all([
          leaveAPI.list({ employee_id: selectedEmployeeId }).catch(() => ({ data: [] })),
          leaveAPI.getBalances(selectedEmployeeId).catch(() => ({})),
          employeeIdentityApi.get(selectedEmployeeId).catch(() => ({ data: null })),
        ]);
        setSelectedEmployeeLeaves(Array.isArray(employeeHistoryRes.data) ? employeeHistoryRes.data : []);
        setSelectedEmployeeBalances(extractBalanceMap(empBalanceRes));
        setSelectedEmployeeInfo(empIdentity?.data || null);
      } else {
        setSelectedEmployeeLeaves([]);
        setSelectedEmployeeBalances({});
        setSelectedEmployeeInfo(null);
      }
    } finally {
      setLoading(false);
    }
  }, [
    canApply,
    canReadOwn,
    canRecommend,
    canSanction,
    canViewEmployeeHistory,
    isEmployeeSelf,
    selectedEmployeeId,
    user?.employee_id,
  ]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!selectedEmployeeId) {
      setSelectedEmployeeLeaveType("");
      return;
    }
    if (
      selectedEmployeeLeaveType
      && !selectedEmployeeLeaves.some((leave) => leave.leave_type_code === selectedEmployeeLeaveType)
    ) {
      setSelectedEmployeeLeaveType("");
    }
  }, [selectedEmployeeId, selectedEmployeeLeaveType, selectedEmployeeLeaves]);

  useEffect(() => {
    let cancelled = false;

    if (!canViewEmployeeHistory || isEmployeeHistoryMode) {
      setEmployeeHistorySearchResults([]);
      setEmployeeHistorySearchLoading(false);
      return () => {
        cancelled = true;
      };
    }

    const normalizedQuery = employeeHistorySearchQuery.trim();
    if (normalizedQuery.length < 2) {
      setEmployeeHistorySearchResults([]);
      setEmployeeHistorySearchLoading(false);
      return () => {
        cancelled = true;
      };
    }

    setEmployeeHistorySearchLoading(true);
    employeeIdentityApi
      .list({ search: normalizedQuery, page: 1, page_size: 8 })
      .then((response) => {
        if (cancelled) return;
        const identities = Array.isArray(response?.data?.identities) ? response.data.identities : [];
        setEmployeeHistorySearchResults(identities);
      })
      .catch(() => {
        if (cancelled) return;
        setEmployeeHistorySearchResults([]);
      })
      .finally(() => {
        if (!cancelled) {
          setEmployeeHistorySearchLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [canViewEmployeeHistory, employeeHistorySearchQuery, isEmployeeHistoryMode]);

  const openEmployeeHistory = (employeeId) => {
    if (!employeeId) return;
    const nextSearchParams = new URLSearchParams(searchParams);
    nextSearchParams.set("employee_id", employeeId);
    setSearchParams(nextSearchParams);
    setEmployeeHistorySearchQuery("");
    setEmployeeHistorySearchResults([]);
  };

  const handleClearEmployeeFilter = () => {
    const nextSearchParams = new URLSearchParams(searchParams);
    nextSearchParams.delete("employee_id");
    setSearchParams(nextSearchParams);
    setEmployeeHistorySearchQuery("");
    setEmployeeHistorySearchResults([]);
  };

  const handleEmployeeHistoryBack = () => {
    if (employeeHistoryReturnPath) {
      navigate(employeeHistoryReturnPath);
      return;
    }
    navigate(-1);
  };

  const handleApply = async () => {
    if (!applyForm.leave_type_code || !applyForm.from_date || !applyForm.to_date || !applyForm.reason || !applyForm.contact_during_leave) {
      toast.error("Please fill all required fields");
      return;
    }
    if (daysApplied <= 0) {
      toast.error("Invalid date range");
      return;
    }
    const eligibilityMessage = getLeaveEligibilityValidationMessage(applyForm);
    if (eligibilityMessage) {
      toast.error(eligibilityMessage);
      return;
    }
    const supportingDocumentMessage = getLeaveSupportingDocumentValidationMessage(applyForm);
    if (supportingDocumentMessage) {
      toast.error(supportingDocumentMessage);
      return;
    }
    try {
      setSubmitting(true);
      await leaveAPI.apply(buildLeaveApplicationPayload(applyForm));
      toast.success("Leave application submitted");
      setApplyForm(createInitialLeaveApplyForm());
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to submit leave"));
    } finally {
      setSubmitting(false);
    }
  };

  const setApplyFormAttachments = (updater) => {
    setApplyForm((prev) => ({
      ...prev,
      attachments: typeof updater === "function" ? updater(prev.attachments || []) : updater,
    }));
  };

  const openActionDialog = (action, record) => {
    setActionDialog({ open: true, action, record });
  };

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6" data-testid="leave-dashboard-loading">
          <PageHeaderSkeleton />
          <StatGridSkeleton count={3} />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <CardSkeleton lines={5} />
            <CardSkeleton lines={5} />
          </div>
          <TableSkeleton rows={6} columns={5} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in">
        {isEmployeeHistoryMode && (
          <div>
            <Button variant="outline" size="sm" onClick={handleEmployeeHistoryBack}>
              <ArrowLeft className="mr-1 w-4 h-4" />
              Back
            </Button>
          </div>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">
              {isEmployeeHistoryMode ? "Leave History" : "Leave Management"}
            </h2>
            <p className="text-slate-500 text-sm">
              {isEmployeeHistoryMode
                ? "Applications and approval history for the selected employee"
                : "Apply, recommend, and sanction leave as per CCS rules"}
            </p>
            {isEmployeeHistoryMode && (
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold text-slate-800">
                  {selectedEmployeeInfo?.full_name || selectedEmployeeId}
                </span>
                {selectedEmployeeInfo?.employee_code && (
                  <Badge variant="outline" className="font-mono text-xs">
                    {selectedEmployeeInfo.employee_code}
                  </Badge>
                )}
              </div>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" className="gap-2" onClick={fetchData}>
              <RefreshCw className="w-4 h-4" />Refresh
            </Button>
          </div>
        </div>

        {!isEmployeeHistoryMode && canViewEmployeeHistory && (
          <Card>
            <CardHeader>
              <CardTitle>View Employee Leave History</CardTitle>
              <CardDescription>
                Search by employee name, code, or ID to open that employee&apos;s leave history.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="employee-history-search">Employee Search</Label>
                <Input
                  id="employee-history-search"
                  value={employeeHistorySearchQuery}
                  onChange={(event) => setEmployeeHistorySearchQuery(event.target.value)}
                  placeholder="Type at least 2 characters"
                  data-testid="employee-history-search-input"
                />
              </div>
              {employeeHistorySearchLoading ? (
                <p className="text-sm text-slate-500">Searching employees...</p>
              ) : employeeHistorySearchQuery.trim().length >= 2 ? (
                employeeHistorySearchResults.length > 0 ? (
                  <div className="rounded-lg border border-slate-200 divide-y divide-slate-100 overflow-hidden">
                    {employeeHistorySearchResults.map((employee) => {
                      const fullName = employee.full_name || employee.name || employee.employee_id;
                      return (
                        <button
                          key={employee.employee_id}
                          type="button"
                          className="flex w-full items-start justify-between gap-3 bg-white px-4 py-3 text-left hover:bg-slate-50"
                          onClick={() => openEmployeeHistory(employee.employee_id)}
                        >
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-slate-900">{fullName}</p>
                            <p className="truncate text-xs text-slate-500">{employee.employee_id}</p>
                          </div>
                          <div className="flex shrink-0 flex-wrap items-center gap-2 justify-end">
                            {employee.employee_code && (
                              <Badge variant="outline" className="font-mono text-xs">
                                {employee.employee_code}
                              </Badge>
                            )}
                            {employee.current_department_id && (
                              <Badge variant="secondary" className="text-xs">
                                {employee.current_department_id}
                              </Badge>
                            )}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No employees found.</p>
                )
              ) : (
                <p className="text-sm text-slate-500">Results will appear after you type at least 2 characters.</p>
              )}
            </CardContent>
          </Card>
        )}

        {selectedEmployeeId && canViewEmployeeHistory && (
          <>
          <Card data-testid="employee-leave-summary-card">
            <CardHeader>
              <CardTitle>Employee Leave Summary</CardTitle>
              <CardDescription>Overall leave activity for the selected employee.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                {[
                  { label: "Total Applications", value: selectedEmployeeLeaveSummary.totalApplications },
                  { label: "Total Days", value: selectedEmployeeLeaveSummary.totalDays },
                  { label: "Sanctioned", value: selectedEmployeeLeaveSummary.sanctionedCount },
                  { label: "Pending", value: selectedEmployeeLeaveSummary.pendingCount },
                  { label: "Rejected / Cancelled", value: selectedEmployeeLeaveSummary.rejectedCount + selectedEmployeeLeaveSummary.cancelledCount },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="rounded-md border border-slate-200 border-l-[3px] border-l-slate-400 bg-slate-50 px-2.5 py-2"
                    data-testid={`employee-leave-summary-${item.label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
                  >
                    <p className="text-[11px] font-medium leading-4 text-slate-600">{item.label}</p>
                    <p className="mt-1 text-xl font-bold leading-none tracking-tight text-slate-900">{item.value}</p>
                  </div>
                ))}
              </div>
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Leave Type Mix</p>
                {selectedEmployeeLeaveSummary.leaveTypeEntries.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedEmployeeLeaveSummary.leaveTypeEntries.map(({ leaveTypeCode, count }) => (
                      <Badge key={leaveTypeCode} variant="outline" className="text-xs">
                        {(LEAVE_TYPE_LABELS[leaveTypeCode] || leaveTypeCode)}: {count}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No leave records available to summarize.</p>
                )}
              </div>
              {Object.keys(selectedEmployeeBalances).length > 0 && (
                <div className="space-y-2" data-testid="employee-leave-summary-balances">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Leave Balance</p>
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                    {["EL", "HPL", "CL"].filter((code) => selectedEmployeeBalances[code]).map((code) => {
                      const style = BALANCE_CARD_STYLES[code] || DEFAULT_CARD_STYLE;
                      const available = selectedEmployeeBalances[code]?.available_days ?? 0;
                      return (
                        <div key={code} className={`${style.bg} rounded-md border border-slate-200 border-l-[3px] px-2.5 py-2 ${style.accent}`}>
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <p className="text-[11px] font-medium leading-4 text-slate-600">{LEAVE_TYPE_LABELS[code] || code}</p>
                              <p className="mt-1 text-xl font-bold leading-none tracking-tight text-slate-900">{available}</p>
                              <p className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-400">available</p>
                            </div>
                            <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${style.iconBg}`}>
                              <Calendar className={`h-3.5 w-3.5 ${style.iconColor}`} />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div className="w-full sm:max-w-xs">
                <Label>Leave Type</Label>
                <SearchableSelect
                  value={selectedEmployeeLeaveType}
                  onValueChange={setSelectedEmployeeLeaveType}
                  options={employeeHistoryLeaveTypeOptions}
                  placeholder="All leave types"
                  searchPlaceholder="Search leave types"
                  emptyMessage="No leave types found"
                  className="mt-1"
                  dataTestId="employee-history-type-filter"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedEmployeeLeaveType && (
                  <Button variant="outline" size="sm" onClick={() => setSelectedEmployeeLeaveType("")}>
                    All Types
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {filteredSelectedEmployeeLeaves.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Calendar className="w-8 h-8 text-slate-300 mb-2" />
                  <p className="text-sm text-slate-500">
                    {selectedEmployeeLeaves.length === 0
                      ? "No leave history found for this employee"
                      : "No leave history found for the selected leave type"}
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto -mx-4 sm:mx-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Type</TableHead>
                        <TableHead>Dates</TableHead>
                        <TableHead className="hidden sm:table-cell">Days</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="hidden sm:table-cell">Applied</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredSelectedEmployeeLeaves.map((leave) => (
                        <TableRow key={leave.id}>
                          <TableCell>{leave.leave_type_code}</TableCell>
                          <TableCell className="text-sm">
                            <div>{formatDate(leave.from_date)} &ndash; {formatDate(leave.to_date)}</div>
                            <LeaveAttachmentLinks attachments={leave.attachments} />
                          </TableCell>
                          <TableCell className="hidden sm:table-cell">{leave.days_applied}</TableCell>
                          <TableCell><LeaveStatusBadge status={leave.status} /></TableCell>
                          <TableCell className="hidden sm:table-cell">{leave.applied_at ? new Date(leave.applied_at).toLocaleDateString("en-GB") : "-"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
          </>
        )}

        {/* Balances */}
        {!isEmployeeHistoryMode && canReadOwn && isEmployeeSelf && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {["EL", "HPL", "CL"].map((code) => {
              const style = BALANCE_CARD_STYLES[code] || DEFAULT_CARD_STYLE;
              const available = balances?.[code]?.available_days ?? 0;
              return (
                <Card key={code} className={`${style.bg} border-l-4 ${style.accent}`}>
                  <CardContent className="pt-5">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-slate-600">{LEAVE_TYPE_LABELS[code] || code}</p>
                        <p className="text-3xl font-bold tracking-tight">{available}</p>
                        <p className="text-xs text-slate-400 mt-0.5">days available</p>
                      </div>
                      <div className={`w-10 h-10 rounded-full ${style.iconBg} flex items-center justify-center`}>
                        <Calendar className={`w-5 h-5 ${style.iconColor}`} />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Apply Form */}
        {!isEmployeeHistoryMode && canApplySelf && (
          <Card>
            <CardHeader>
              <CardTitle>Apply for Leave</CardTitle>
              <CardDescription>Submit a leave request for approval</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Leave Type *</Label>
                  <SearchableSelect
                    value={applyForm.leave_type_code}
                    onValueChange={(v) => setApplyForm({ ...applyForm, leave_type_code: v })}
                    options={leaveTypeOptions}
                    placeholder="Select leave type"
                    className="mt-1"
                    emptyMessage={leaveTypeUnavailableMessage || "No leave types available"}
                  />
                  {leaveTypes.length === 0 && (
                    <p className="text-xs text-red-600 mt-1">
                      {leaveTypeUnavailableMessage || "No leave types available. Ensure leave masters are seeded and your employment type allows leave."}
                    </p>
                  )}
                  {Number.isFinite(selectedBalance?.available_days) && (
                    <p className="text-xs text-slate-500 mt-1">Available: {selectedBalance.available_days} days</p>
                  )}
                </div>
                <div>
                  <Label>Contact During Leave *</Label>
                  <Input className="mt-1" value={applyForm.contact_during_leave} onChange={(e) => setApplyForm({ ...applyForm, contact_during_leave: e.target.value })} />
                </div>
                <div>
                  <Label>From Date *</Label>
                  <Input type="date" className="mt-1" value={applyForm.from_date} onChange={(e) => setApplyForm({ ...applyForm, from_date: e.target.value })} />
                </div>
                <div>
                  <Label>To Date *</Label>
                  <Input type="date" className="mt-1" value={applyForm.to_date} onChange={(e) => setApplyForm({ ...applyForm, to_date: e.target.value })} />
                  {daysApplied > 0 && <p className="text-xs text-slate-500 mt-1">Days: {daysApplied}</p>}
                </div>
                <div>
                  <Label>Leave Station</Label>
                  <Input className="mt-1" value={applyForm.leave_station} onChange={(e) => setApplyForm({ ...applyForm, leave_station: e.target.value })} />
                </div>
                <div className="md:col-span-2">
                  <Label>Reason *</Label>
                  <Textarea className="mt-1" rows={3} value={applyForm.reason} onChange={(e) => setApplyForm({ ...applyForm, reason: e.target.value })} />
                </div>
                {isCommutedLeave(applyForm.leave_type_code) && (
                  <>
                    <div>
                      <Label>Commuted Leave Basis</Label>
                      <Select
                        value={applyForm.commuted_leave_basis || undefined}
                        onValueChange={(value) => setApplyForm({ ...applyForm, commuted_leave_basis: value })}
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue placeholder="Select basis" />
                        </SelectTrigger>
                        <SelectContent>
                          {COMMUTED_LEAVE_BASIS_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 md:self-end">
                      <Checkbox
                        id="dashboard-medical-certificate"
                        checked={Boolean(applyForm.medical_certificate_provided)}
                        onCheckedChange={(checked) => setApplyForm({ ...applyForm, medical_certificate_provided: checked === true })}
                      />
                      <Label htmlFor="dashboard-medical-certificate" className="cursor-pointer">Medical certificate available</Label>
                    </div>
                  </>
                )}
                {isMaternityLeave(applyForm.leave_type_code) && (
                  <>
                    <div>
                      <Label>Expected Delivery Date</Label>
                      <Input type="date" className="mt-1" value={applyForm.expected_delivery_date} onChange={(e) => setApplyForm({ ...applyForm, expected_delivery_date: e.target.value })} />
                    </div>
                    <div>
                      <Label>Childbirth Date</Label>
                      <Input type="date" className="mt-1" value={applyForm.childbirth_date} onChange={(e) => setApplyForm({ ...applyForm, childbirth_date: e.target.value })} />
                    </div>
                  </>
                )}
                {isPaternityLeave(applyForm.leave_type_code) && (
                  <>
                    <div>
                      <Label>Childbirth Date</Label>
                      <Input type="date" className="mt-1" value={applyForm.childbirth_date} onChange={(e) => setApplyForm({ ...applyForm, childbirth_date: e.target.value })} />
                    </div>
                    <div>
                      <Label>Adoption Date</Label>
                      <Input type="date" className="mt-1" value={applyForm.adoption_date} onChange={(e) => setApplyForm({ ...applyForm, adoption_date: e.target.value })} />
                    </div>
                  </>
                )}
                {isChildCareLeave(applyForm.leave_type_code) && (
                  <>
                    <div>
                      <Label>Child Date of Birth</Label>
                      <Input type="date" className="mt-1" value={applyForm.child_date_of_birth} onChange={(e) => setApplyForm({ ...applyForm, child_date_of_birth: e.target.value })} />
                    </div>
                    <div>
                      <Label>Child Order</Label>
                      <Input type="number" min="1" className="mt-1" value={applyForm.child_order} onChange={(e) => setApplyForm({ ...applyForm, child_order: e.target.value })} />
                    </div>
                    <div className="md:col-span-2 flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2">
                      <Checkbox
                        id="dashboard-child-disability"
                        checked={Boolean(applyForm.child_has_disability)}
                        onCheckedChange={(checked) => setApplyForm({ ...applyForm, child_has_disability: checked === true })}
                      />
                      <Label htmlFor="dashboard-child-disability" className="cursor-pointer">Child has a disability</Label>
                    </div>
                  </>
                )}
                <LeaveSupportingDocumentsField
                  attachments={applyForm.attachments || []}
                  setAttachments={setApplyFormAttachments}
                  recommendation={getLeaveSupportingDocumentRecommendation(applyForm)}
                  requirementMessage={getLeaveSupportingDocumentRequirementMessage(applyForm)}
                />
              </div>
              <div className="flex justify-end mt-4">
                <Button onClick={handleApply} disabled={submitting || leaveTypes.length === 0}>
                  {submitting ? "Submitting..." : "Submit Leave"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* My Applications */}
        {!isEmployeeHistoryMode && canReadOwn && isEmployeeSelf && (
          <Card>
            <CardHeader>
              <CardTitle>My Leave Applications</CardTitle>
              <CardDescription>Track your leave requests</CardDescription>
            </CardHeader>
            <CardContent>
              {myLeaves.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Calendar className="w-8 h-8 text-slate-300 mb-2" />
                  <p className="text-sm text-slate-500">No leave applications yet</p>
                </div>
              ) : (
                <div className="overflow-x-auto -mx-4 sm:mx-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Type</TableHead>
                        <TableHead>Dates</TableHead>
                        <TableHead className="hidden sm:table-cell">Days</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {myLeaves.map((leave) => (
                        <TableRow key={leave.id}>
                          <TableCell>{leave.leave_type_code}</TableCell>
                          <TableCell className="text-sm">
                            <div>{formatDate(leave.from_date)} &ndash; {formatDate(leave.to_date)}</div>
                            <LeaveAttachmentLinks attachments={leave.attachments} />
                          </TableCell>
                          <TableCell className="hidden sm:table-cell">{leave.days_applied}</TableCell>
                          <TableCell><LeaveStatusBadge status={leave.status} /></TableCell>
                          <TableCell className="text-right">
                            {canApply && ["SUBMITTED", "RECOMMENDED"].includes(leave.status) ? (
                              <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => openActionDialog("cancel", leave)}>
                                <XCircle className="w-4 h-4 mr-1" /> Cancel
                              </Button>
                            ) : null}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Pending Recommendations */}
        {!isEmployeeHistoryMode && canRecommend && (
          <Card id="pending-leave-section">
            <CardHeader>
              <CardTitle>Pending Recommendations</CardTitle>
              <CardDescription>Leaves awaiting recommendation</CardDescription>
            </CardHeader>
            <CardContent>
              {pendingRecommend.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Inbox className="w-8 h-8 text-slate-300 mb-2" />
                  <p className="text-sm text-slate-500">No pending recommendations</p>
                  <p className="text-xs text-slate-400 mt-0.5">Submitted leave requests will appear here.</p>
                </div>
              ) : (
                <div className="overflow-x-auto -mx-4 sm:mx-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Employee</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Dates</TableHead>
                        <TableHead className="hidden sm:table-cell">Days</TableHead>
                        <TableHead className="hidden md:table-cell">Reason</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pendingRecommend.map((leave) => (
                        <TableRow key={leave.id}>
                          <TableCell>
                            <button
                              type="button"
                              className="min-w-0 text-left hover:underline"
                              onClick={() => openEmployeeHistory(leave.employee_id)}
                            >
                              <p className="font-medium text-blue-700 truncate">{leave.employee_name || leave.employee_id}</p>
                              <p className="text-xs text-slate-500 font-mono truncate">{leave.employee_id}</p>
                            </button>
                          </TableCell>
                          <TableCell>{leave.leave_type_code}</TableCell>
                          <TableCell className="text-sm">{formatDate(leave.from_date)} &ndash; {formatDate(leave.to_date)}</TableCell>
                          <TableCell className="hidden sm:table-cell">{leave.days_applied}</TableCell>
                          <TableCell className="hidden md:table-cell">
                            <span className="text-sm text-slate-600 truncate block max-w-[200px]" title={leave.reason}>{leave.reason}</span>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              {leave.leave_type_code === "CL" ? (
                                <Button size="sm" className="gap-1" onClick={() => openActionDialog("sanction", leave)}>
                                  <CheckCircle2 className="w-4 h-4" /> Approve
                                </Button>
                              ) : (
                                <Button size="sm" className="gap-1" onClick={() => openActionDialog("recommend", leave)}>
                                  <CheckCircle2 className="w-4 h-4" /> Recommend
                                </Button>
                              )}
                              <Button variant="outline" size="sm" className="gap-1 text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => openActionDialog("reject", leave)}>
                                <XCircle className="w-4 h-4" /> Reject
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Pending Sanctions */}
        {!isEmployeeHistoryMode && canSanction && (
          <Card id={canRecommend ? undefined : "pending-leave-section"}>
            <CardHeader>
              <CardTitle>Pending Sanctions</CardTitle>
              <CardDescription>Leaves awaiting sanction</CardDescription>
            </CardHeader>
            <CardContent>
              {pendingSanction.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Clock className="w-8 h-8 text-slate-300 mb-2" />
                  <p className="text-sm text-slate-500">No pending sanctions</p>
                  <p className="text-xs text-slate-400 mt-0.5">Recommended leave requests will appear here.</p>
                </div>
              ) : (
                <div className="overflow-x-auto -mx-4 sm:mx-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Employee</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Dates</TableHead>
                        <TableHead className="hidden sm:table-cell">Days</TableHead>
                        <TableHead className="hidden md:table-cell">Reason</TableHead>
                        <TableHead className="hidden md:table-cell">Recommended By</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pendingSanction.map((leave) => (
                        <TableRow key={leave.id}>
                          <TableCell>
                            <button
                              type="button"
                              className="min-w-0 text-left hover:underline"
                              onClick={() => openEmployeeHistory(leave.employee_id)}
                            >
                              <p className="font-medium text-blue-700 truncate">{leave.employee_name || leave.employee_id}</p>
                              <p className="text-xs text-slate-500 font-mono truncate">{leave.employee_id}</p>
                            </button>
                          </TableCell>
                          <TableCell>{leave.leave_type_code}</TableCell>
                          <TableCell className="text-sm">{formatDate(leave.from_date)} &ndash; {formatDate(leave.to_date)}</TableCell>
                          <TableCell className="hidden sm:table-cell">{leave.days_applied}</TableCell>
                          <TableCell className="hidden md:table-cell">
                            <span className="text-sm text-slate-600 truncate block max-w-[200px]" title={leave.reason}>{leave.reason}</span>
                          </TableCell>
                          <TableCell className="hidden md:table-cell">
                            <span className="text-sm text-slate-600">{leave.recommended_by_name || ""}</span>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button size="sm" className="gap-1" onClick={() => openActionDialog("sanction", leave)}>
                                <CheckCircle2 className="w-4 h-4" /> Sanction
                              </Button>
                              <Button variant="outline" size="sm" className="gap-1 text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => openActionDialog("reject", leave)}>
                                <XCircle className="w-4 h-4" /> Reject
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      <LeaveActionDialog
        dialog={actionDialog}
        onClose={() => setActionDialog({ open: false, action: null, record: null })}
        onDone={fetchData}
      />
    </Layout>
  );
};

export default LeaveDashboard;
