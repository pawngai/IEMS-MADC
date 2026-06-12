import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/modules/identity_access";
import { usePermissions } from "@/modules/identity_access";
import { essAPI } from "@/modules/ess";
import { leaveAPI } from "@/modules/leave_attendance/api/leaveApi";
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
import { AlertTriangle, Calendar, ChevronDown, ChevronUp, RefreshCw, RotateCcw, XCircle } from "lucide-react";
import { toast } from "sonner";
import { LeaveStatusBadge } from "@/modules/leave_attendance/components/LeaveStatusBadge";
import LeaveSupportingDocumentsField from "@/modules/leave_attendance/components/LeaveSupportingDocumentsField";
import { documentsAPI } from "@/modules/documents";
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
} from "@/modules/leave_attendance/model/leaveApplyForm";

/** Format ISO date string to readable format like "01 Jul 2026" */
const formatDate = (isoDate) => {
  if (!isoDate) return "";
  const d = new Date(isoDate + "T00:00:00");
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
};

/** Color config for each leave type balance card */
const BALANCE_CARD_STYLES = {
  EL:  { bg: "bg-emerald-50", iconBg: "bg-emerald-100", iconColor: "text-emerald-600", accent: "border-l-emerald-500" },
  HPL: { bg: "bg-violet-50",  iconBg: "bg-violet-100",  iconColor: "text-violet-600",  accent: "border-l-violet-500" },
  CML: { bg: "bg-cyan-50",    iconBg: "bg-cyan-100",    iconColor: "text-cyan-600",    accent: "border-l-cyan-500" },
  LND: { bg: "bg-sky-50",     iconBg: "bg-sky-100",     iconColor: "text-sky-600",     accent: "border-l-sky-500" },
  CL:  { bg: "bg-amber-50",   iconBg: "bg-amber-100",   iconColor: "text-amber-600",   accent: "border-l-amber-500" },
};
const DEFAULT_CARD_STYLE = { bg: "bg-slate-50", iconBg: "bg-slate-100", iconColor: "text-slate-600", accent: "border-l-slate-500" };

const LEAVE_TYPE_LABELS = { EL: "Earned Leave", HPL: "Half Pay Leave", CML: "Commuted Leave", LND: "Leave Not Due", CL: "Casual Leave" };

const extractLeaveAttachmentFilename = (attachment) => {
  const filename = String(attachment?.filename || "").trim();
  if (filename) return filename;
  const directUrl = String(attachment?.url || "").trim();
  if (directUrl.startsWith("/api/documents/files/")) {
    return directUrl.slice("/api/documents/files/".length).split("/")[0] || "";
  }
  return "";
};

const EssLeavePage = () => {
  const { user } = useAuth();
  const { can } = usePermissions();
  const canApply = can(Permissions.LEAVE_APPLY_OWN);
  const canReadOwn = can(Permissions.LEAVE_READ_OWN);
  // On ESS portal, a dual-role user acting as EMPLOYEE should be able to
  // apply leave for themselves.  resolveScopeAccess evaluates ALL authorities
  // which wrongly yields GLOBAL/DEPARTMENT for dual-role users.  The ESS
  // leave form is always self-service, so we only need: permission + EMPLOYEE
  // authority + an employee_id.
  const hasEmployeeAuthority = Array.isArray(user?.authorities) && user.authorities.includes("EMPLOYEE");
  const canApplySelf = canApply && hasEmployeeAuthority && Boolean(user?.employee_id);

  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [balances, setBalances] = useState({});
  const [myLeaves, setMyLeaves] = useState([]);
  const [leaveTypeUnavailableMessage, setLeaveTypeUnavailableMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [cancellingId, setCancellingId] = useState(null);
  const [confirmCancelId, setConfirmCancelId] = useState(null);
  const [expandedLeaveId, setExpandedLeaveId] = useState(null);
  const [applyForm, setApplyForm] = useState(createInitialLeaveApplyForm);

  const daysApplied = useMemo(() => {
    if (!applyForm.from_date || !applyForm.to_date) return 0;
    const start = new Date(applyForm.from_date);
    const end = new Date(applyForm.to_date);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;
    const diff = end - start;
    if (diff < 0) return 0;
    return Math.floor(diff / (1000 * 60 * 60 * 24)) + 1;
  }, [applyForm.from_date, applyForm.to_date]);

  const exceedsBalance = useMemo(() => {
    if (!applyForm.leave_type_code || daysApplied <= 0) return false;
    const avail = balances?.[applyForm.leave_type_code]?.available_days;
    return Number.isFinite(avail) && daysApplied > avail;
  }, [applyForm.leave_type_code, daysApplied, balances]);

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

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const profileRes = await essAPI.getMyProfile().catch((error) => ({ data: null, error }));
      const profileData = profileRes.data || null;
      setProfile(profileData);

      if (user?.employee_id) {
        const [balanceRes, myRes] = await Promise.all([
          essAPI.getMyLeaveBalances().catch((error) => ({ data: { balances: {} }, error })),
          leaveAPI.listMy().catch(() => ({ data: [] })),
        ]);

        const fetchedBalances = balanceRes.data?.balances || {};
        setBalances(fetchedBalances);
        setLeaveTypes(Object.values(fetchedBalances));
        setLeaveTypeUnavailableMessage(
          Object.keys(fetchedBalances).length > 0
            ? ""
            : getLeaveTypeUnavailableMessage({
                userEmployeeId: user.employee_id,
                profile: profileData,
                errorOrDetail: balanceRes.error || profileRes.error,
              })
        );
        setMyLeaves(Array.isArray(myRes.data) ? myRes.data : []);
      } else {
        setBalances({});
        setLeaveTypes([]);
        setMyLeaves([]);
        setLeaveTypeUnavailableMessage(
          getLeaveTypeUnavailableMessage({ profile: profileData, errorOrDetail: profileRes.error })
        );
      }
    } finally {
      setLoading(false);
    }
  }, [user?.employee_id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const resetApplyForm = () => {
    setApplyForm(createInitialLeaveApplyForm());
  };

  const setApplyFormAttachments = (updater) => {
    setApplyForm((prev) => ({
      ...prev,
      attachments: typeof updater === "function" ? updater(prev.attachments || []) : updater,
    }));
  };

  const handleApply = async () => {
    if (!canApply) {
      toast.error("Leave apply permission not available");
      return;
    }
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
      resetApplyForm();
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to submit leave"));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelLeave = async (leave) => {
    if (!leave?.id) return;
    try {
      setCancellingId(leave.id);
      await leaveAPI.cancel(leave.id, "Cancelled by employee");
      toast.success("Leave cancelled");
      setConfirmCancelId(null);
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to cancel leave"));
    } finally {
      setCancellingId(null);
    }
  };

  if (loading) {
    return (
      <>
        <div className="max-w-6xl mx-auto space-y-6" data-testid="ess-leave-loading">
          <PageHeaderSkeleton />
          <StatGridSkeleton count={3} />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <CardSkeleton lines={5} />
            <CardSkeleton lines={5} />
          </div>
          <TableSkeleton rows={6} columns={5} />
        </div>
      </>
    );
  }

  return (
    <>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in" data-testid="ess-leave-page">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Employee Self-Service Portal</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Leave</h2>
            <p className="text-sm text-slate-500 mt-1">
              Apply for leave and track your requests.
            </p>
          </div>
          <Button variant="outline" className="gap-2" onClick={fetchData}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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

        {canApplySelf && (
          <Card>
            <CardHeader>
              <CardTitle>Apply for Leave</CardTitle>
              <CardDescription>Submit a leave request for workflow approval.</CardDescription>
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
                <div className="hidden md:block" /> {/* spacer to keep Leave Type alone on its row */}
                <div>
                  <Label>From Date *</Label>
                  <Input
                    type="date"
                    className="mt-1"
                    value={applyForm.from_date}
                    onChange={(e) => setApplyForm({ ...applyForm, from_date: e.target.value })}
                  />
                </div>
                <div>
                  <Label>To Date *</Label>
                  <Input
                    type="date"
                    className="mt-1"
                    value={applyForm.to_date}
                    onChange={(e) => setApplyForm({ ...applyForm, to_date: e.target.value })}
                  />
                </div>
                {daysApplied > 0 && (
                  <div className="md:col-span-2">
                    <div className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium ${exceedsBalance ? "bg-red-50 text-red-700 border border-red-200" : "bg-blue-50 text-blue-700 border border-blue-200"}`}>
                      <Calendar className="w-4 h-4 shrink-0" />
                      <span>{daysApplied} day{daysApplied !== 1 ? "s" : ""} selected</span>
                      {applyForm.from_date && applyForm.to_date && (
                        <span className="text-xs opacity-75 ml-1">
                          ({formatDate(applyForm.from_date)} &ndash; {formatDate(applyForm.to_date)})
                        </span>
                      )}
                      {exceedsBalance && (
                        <span className="flex items-center gap-1 ml-auto text-xs">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          Exceeds available balance ({selectedBalance?.available_days} days)
                        </span>
                      )}
                    </div>
                  </div>
                )}
                <div>
                  <Label>Leave Station</Label>
                  <Input
                    className="mt-1"
                    placeholder="e.g. Aizawl"
                    value={applyForm.leave_station}
                    onChange={(e) => setApplyForm({ ...applyForm, leave_station: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Contact During Leave *</Label>
                  <Input
                    className="mt-1"
                    placeholder="Phone number or email"
                    value={applyForm.contact_during_leave}
                    onChange={(e) => setApplyForm({ ...applyForm, contact_during_leave: e.target.value })}
                  />
                </div>
                <div className="md:col-span-2">
                  <Label>Reason *</Label>
                  <Textarea
                    className="mt-1"
                    rows={3}
                    placeholder="Briefly describe the reason for leave"
                    value={applyForm.reason}
                    onChange={(e) => setApplyForm({ ...applyForm, reason: e.target.value })}
                  />
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
                        id="ess-medical-certificate"
                        checked={Boolean(applyForm.medical_certificate_provided)}
                        onCheckedChange={(checked) => setApplyForm({ ...applyForm, medical_certificate_provided: checked === true })}
                      />
                      <Label htmlFor="ess-medical-certificate" className="cursor-pointer">Medical certificate available</Label>
                    </div>
                  </>
                )}
                {isMaternityLeave(applyForm.leave_type_code) && (
                  <>
                    <div>
                      <Label>Expected Delivery Date</Label>
                      <Input
                        type="date"
                        className="mt-1"
                        value={applyForm.expected_delivery_date}
                        onChange={(e) => setApplyForm({ ...applyForm, expected_delivery_date: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>Childbirth Date</Label>
                      <Input
                        type="date"
                        className="mt-1"
                        value={applyForm.childbirth_date}
                        onChange={(e) => setApplyForm({ ...applyForm, childbirth_date: e.target.value })}
                      />
                    </div>
                  </>
                )}
                {isPaternityLeave(applyForm.leave_type_code) && (
                  <>
                    <div>
                      <Label>Childbirth Date</Label>
                      <Input
                        type="date"
                        className="mt-1"
                        value={applyForm.childbirth_date}
                        onChange={(e) => setApplyForm({ ...applyForm, childbirth_date: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>Adoption Date</Label>
                      <Input
                        type="date"
                        className="mt-1"
                        value={applyForm.adoption_date}
                        onChange={(e) => setApplyForm({ ...applyForm, adoption_date: e.target.value })}
                      />
                    </div>
                  </>
                )}
                {isChildCareLeave(applyForm.leave_type_code) && (
                  <>
                    <div>
                      <Label>Child Date of Birth</Label>
                      <Input
                        type="date"
                        className="mt-1"
                        value={applyForm.child_date_of_birth}
                        onChange={(e) => setApplyForm({ ...applyForm, child_date_of_birth: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>Child Order</Label>
                      <Input
                        type="number"
                        min="1"
                        className="mt-1"
                        value={applyForm.child_order}
                        onChange={(e) => setApplyForm({ ...applyForm, child_order: e.target.value })}
                      />
                    </div>
                    <div className="md:col-span-2 flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2">
                      <Checkbox
                        id="ess-child-disability"
                        checked={Boolean(applyForm.child_has_disability)}
                        onCheckedChange={(checked) => setApplyForm({ ...applyForm, child_has_disability: checked === true })}
                      />
                      <Label htmlFor="ess-child-disability" className="cursor-pointer">Child has a disability</Label>
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
              <div className="flex justify-end gap-2 mt-4">
                {(applyForm.leave_type_code || applyForm.from_date || applyForm.to_date || applyForm.reason || (applyForm.attachments || []).length > 0) && (
                  <Button variant="ghost" onClick={resetApplyForm} type="button">
                    <RotateCcw className="w-4 h-4 mr-1" />
                    Reset
                  </Button>
                )}
                <Button onClick={handleApply} disabled={submitting || leaveTypes.length === 0}>
                  {submitting ? "Submitting..." : "Submit Leave"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {canApply && !canApplySelf && (
          <Card>
            <CardHeader>
              <CardTitle>Apply for Leave</CardTitle>
              <CardDescription>Employee self-service only</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-amber-700">
                Leave can only be applied from an employee self-service account, not from a role-based operational account.
              </p>
            </CardContent>
          </Card>
        )}

        {canReadOwn && (
          <Card>
            <CardHeader>
              <CardTitle>My Leave Applications</CardTitle>
              <CardDescription>{profile?.full_name || user?.name || "Employee"} leave history.</CardDescription>
            </CardHeader>
            <CardContent>
              {myLeaves.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-center">
                  <Calendar className="w-10 h-10 text-slate-300 mb-3" />
                  <p className="text-sm font-medium text-slate-500">No leave applications yet</p>
                  <p className="text-xs text-slate-400 mt-1">Your submitted leave requests will appear here.</p>
                </div>
              ) : (
                <div className="overflow-x-auto -mx-4 sm:mx-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-8"></TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Dates</TableHead>
                      <TableHead className="hidden sm:table-cell">Days</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {myLeaves.map((leave) => {
                      const isExpanded = expandedLeaveId === leave.id;
                      const isCancellable = ["SUBMITTED", "RECOMMENDED"].includes(leave.status);
                      const isConfirming = confirmCancelId === leave.id;
                      return (
                        <Fragment key={leave.id}>
                          <TableRow
                            className="cursor-pointer hover:bg-slate-50"
                            onClick={() => setExpandedLeaveId(isExpanded ? null : leave.id)}
                          >
                            <TableCell className="pr-0 w-8">
                              {isExpanded
                                ? <ChevronUp className="w-4 h-4 text-slate-400" />
                                : <ChevronDown className="w-4 h-4 text-slate-400" />}
                            </TableCell>
                            <TableCell className="font-medium">{leave.leave_type_code}</TableCell>
                            <TableCell className="text-sm">
                              {formatDate(leave.from_date)} &ndash; {formatDate(leave.to_date)}
                            </TableCell>
                            <TableCell className="hidden sm:table-cell">{leave.days_applied}</TableCell>
                            <TableCell><LeaveStatusBadge status={leave.status} /></TableCell>
                            <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                              {isCancellable && !isConfirming && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                  disabled={cancellingId === leave.id}
                                  onClick={() => setConfirmCancelId(leave.id)}
                                >
                                  <XCircle className="w-4 h-4 mr-1" />
                                  Cancel
                                </Button>
                              )}
                              {isCancellable && isConfirming && (
                                <div className="flex items-center gap-1 justify-end">
                                  <Button
                                    variant="destructive"
                                    size="sm"
                                    disabled={cancellingId === leave.id}
                                    onClick={() => handleCancelLeave(leave)}
                                  >
                                    {cancellingId === leave.id ? "Cancelling..." : "Confirm"}
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setConfirmCancelId(null)}
                                  >
                                    No
                                  </Button>
                                </div>
                              )}
                            </TableCell>
                          </TableRow>
                          {isExpanded && (
                            <TableRow className="bg-slate-50/60">
                              <TableCell colSpan={6} className="py-3">
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-2 text-sm pl-2">
                                  {leave.reason && (
                                    <div className="col-span-2 sm:col-span-4">
                                      <span className="text-slate-500 text-xs">Reason:</span>
                                      <p className="text-slate-700">{leave.reason}</p>
                                    </div>
                                  )}
                                  {leave.leave_station && (
                                    <div>
                                      <span className="text-slate-500 text-xs">Station:</span>
                                      <p className="text-slate-700">{leave.leave_station}</p>
                                    </div>
                                  )}
                                  {leave.contact_during_leave && (
                                    <div>
                                      <span className="text-slate-500 text-xs">Contact:</span>
                                      <p className="text-slate-700">{leave.contact_during_leave}</p>
                                    </div>
                                  )}
                                  {leave.applied_at && (
                                    <div>
                                      <span className="text-slate-500 text-xs">Applied:</span>
                                      <p className="text-slate-700">{formatDate(leave.applied_at?.split("T")[0])}</p>
                                    </div>
                                  )}
                                  {leave.remarks && (
                                    <div className="col-span-2 sm:col-span-4">
                                      <span className="text-slate-500 text-xs">Remarks:</span>
                                      <p className="text-slate-700">{leave.remarks}</p>
                                    </div>
                                  )}
                                  {leave.attachments?.length > 0 && (
                                    <div className="col-span-2 sm:col-span-4">
                                      <span className="text-slate-500 text-xs">Supporting Documents:</span>
                                      <div className="mt-1 flex flex-wrap gap-2">
                                        {leave.attachments.map((attachment, index) => {
                                          const filename = extractLeaveAttachmentFilename(attachment);
                                          if (!filename) {
                                            return null;
                                          }
                                          return (
                                            <button
                                              type="button"
                                              key={`${attachment.filename || attachment.url || "attachment"}-${index}`}
                                              onClick={() => documentsAPI.openDocument(filename)}
                                              className="inline-flex items-center rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-white"
                                            >
                                              {attachment.original_name || attachment.filename || `Attachment ${index + 1}`}
                                            </button>
                                          );
                                        })}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </TableCell>
                            </TableRow>
                          )}
                        </Fragment>
                      );
                    })}
                  </TableBody>
                </Table>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
};

export default EssLeavePage;

