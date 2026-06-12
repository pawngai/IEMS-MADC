import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { CardSkeleton, PageHeaderSkeleton, StatGridSkeleton, TableSkeleton } from "@/shared/ui/skeletons";
import { DataTable } from "@/shared/data-table";
import { ArrowLeft, Calendar, CheckCircle2, Clock, Inbox, XCircle, RefreshCw } from "lucide-react";
import { LeaveStatusBadge } from "@/modules/leave_attendance/components/LeaveStatusBadge";
import LeaveActionDialog from "@/modules/leave_attendance/components/LeaveActionDialog";
import LeaveAttachmentLinks from "@/modules/leave_attendance/pages/LeaveAttachmentLinks";
import LeaveDashboardApplyForm from "@/modules/leave_attendance/pages/LeaveDashboardApplyForm";
import LeaveDashboardEmployeeHistory from "@/modules/leave_attendance/pages/LeaveDashboardEmployeeHistory";
import { LEAVE_TYPE_LABELS, useLeaveDashboardController } from "@/modules/leave_attendance/pages/useLeaveDashboardController";

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

const buildEmployeeColumn = (openEmployeeHistory) => ({
  key: "employee",
  header: "Employee",
  render: (leave) => (
    <button
      type="button"
      className="min-w-0 text-left hover:underline"
      onClick={() => openEmployeeHistory(leave.employee_id)}
    >
      <p className="font-medium text-blue-700 truncate">{leave.employee_name || leave.employee_id}</p>
      <p className="text-xs text-slate-500 font-mono truncate">{leave.employee_id}</p>
    </button>
  ),
});

const REASON_COLUMN = {
  key: "reason",
  header: "Reason",
  className: "hidden md:table-cell",
  render: (leave) => (
    <span className="text-sm text-slate-600 truncate block max-w-[200px]" title={leave.reason}>{leave.reason}</span>
  ),
};
const LeaveDashboard = () => {
  const {
    actionDialog,
    applyForm,
    balances,
    canApply,
    canApplySelf,
    canReadOwn,
    canRecommend,
    canSanction,
    canViewEmployeeHistory,
    daysApplied,
    employeeHistoryLeaveTypeOptions,
    employeeHistorySearchLoading,
    employeeHistorySearchQuery,
    employeeHistorySearchResults,
    fetchData,
    filteredSelectedEmployeeLeaves,
    handleApply,
    handleEmployeeHistoryBack,
    isEmployeeHistoryMode,
    isEmployeeSelf,
    leaveTypeOptions,
    leaveTypeUnavailableMessage,
    leaveTypes,
    loading,
    myLeaves,
    openActionDialog,
    openEmployeeHistory,
    pendingRecommend,
    pendingSanction,
    selectedBalance,
    selectedEmployeeBalances,
    selectedEmployeeId,
    selectedEmployeeInfo,
    selectedEmployeeLeaveSummary,
    selectedEmployeeLeaveType,
    selectedEmployeeLeaves,
    setActionDialog,
    setApplyForm,
    setApplyFormAttachments,
    setEmployeeHistorySearchQuery,
    setSelectedEmployeeLeaveType,
    submitting,
  } = useLeaveDashboardController();

  if (loading) {
    return (
      <>
        <div className="space-y-6" data-testid="leave-dashboard-loading">
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

        <LeaveDashboardEmployeeHistory
          balanceCardStyles={BALANCE_CARD_STYLES}
          canViewEmployeeHistory={canViewEmployeeHistory}
          defaultCardStyle={DEFAULT_CARD_STYLE}
          employeeHistoryLeaveTypeOptions={employeeHistoryLeaveTypeOptions}
          employeeHistorySearchLoading={employeeHistorySearchLoading}
          employeeHistorySearchQuery={employeeHistorySearchQuery}
          employeeHistorySearchResults={employeeHistorySearchResults}
          filteredSelectedEmployeeLeaves={filteredSelectedEmployeeLeaves}
          isEmployeeHistoryMode={isEmployeeHistoryMode}
          openEmployeeHistory={openEmployeeHistory}
          selectedEmployeeBalances={selectedEmployeeBalances}
          selectedEmployeeId={selectedEmployeeId}
          selectedEmployeeLeaveSummary={selectedEmployeeLeaveSummary}
          selectedEmployeeLeaveType={selectedEmployeeLeaveType}
          selectedEmployeeLeaves={selectedEmployeeLeaves}
          setEmployeeHistorySearchQuery={setEmployeeHistorySearchQuery}
          setSelectedEmployeeLeaveType={setSelectedEmployeeLeaveType}
        />

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
          <LeaveDashboardApplyForm
            applyForm={applyForm}
            daysApplied={daysApplied}
            handleApply={handleApply}
            leaveTypeOptions={leaveTypeOptions}
            leaveTypeUnavailableMessage={leaveTypeUnavailableMessage}
            leaveTypes={leaveTypes}
            selectedBalance={selectedBalance}
            setApplyForm={setApplyForm}
            setApplyFormAttachments={setApplyFormAttachments}
            submitting={submitting}
          />
        )}

        {/* My Applications */}
        {!isEmployeeHistoryMode && canReadOwn && isEmployeeSelf && (
          <Card>
            <CardHeader>
              <CardTitle>My Leave Applications</CardTitle>
              <CardDescription>Track your leave requests</CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                rows={myLeaves}
                rowKey={(leave) => leave.id}
                emptyState={
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <Calendar className="w-8 h-8 text-slate-300 mb-2" />
                    <p className="text-sm text-slate-500">No leave applications yet</p>
                  </div>
                }
                columns={[
                  { key: "leave_type_code", header: "Type" },
                  {
                    key: "dates",
                    header: "Dates",
                    className: "text-sm",
                    headClassName: "",
                    render: (leave) => (
                      <>
                        <div>{formatDate(leave.from_date)} &ndash; {formatDate(leave.to_date)}</div>
                        <LeaveAttachmentLinks attachments={leave.attachments} />
                      </>
                    ),
                  },
                  { key: "days_applied", header: "Days", className: "hidden sm:table-cell" },
                  { key: "status", header: "Status", render: (leave) => <LeaveStatusBadge status={leave.status} /> },
                  {
                    key: "action",
                    header: "Action",
                    className: "text-right",
                    render: (leave) =>
                      canApply && ["SUBMITTED", "RECOMMENDED"].includes(leave.status) ? (
                        <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => openActionDialog("cancel", leave)}>
                          <XCircle className="w-4 h-4 mr-1" /> Cancel
                        </Button>
                      ) : null,
                  },
                ]}
              />
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
              <DataTable
                rows={pendingRecommend}
                rowKey={(leave) => leave.id}
                emptyState={
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <Inbox className="w-8 h-8 text-slate-300 mb-2" />
                    <p className="text-sm text-slate-500">No pending recommendations</p>
                    <p className="text-xs text-slate-400 mt-0.5">Submitted leave requests will appear here.</p>
                  </div>
                }
                columns={[
                  buildEmployeeColumn(openEmployeeHistory),
                  { key: "leave_type_code", header: "Type" },
                  {
                    key: "dates",
                    header: "Dates",
                    className: "text-sm",
                    headClassName: "",
                    render: (leave) => <>{formatDate(leave.from_date)} &ndash; {formatDate(leave.to_date)}</>,
                  },
                  { key: "days_applied", header: "Days", className: "hidden sm:table-cell" },
                  REASON_COLUMN,
                  {
                    key: "action",
                    header: "Action",
                    className: "text-right",
                    render: (leave) => (
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
                    ),
                  },
                ]}
              />
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
              <DataTable
                rows={pendingSanction}
                rowKey={(leave) => leave.id}
                emptyState={
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <Clock className="w-8 h-8 text-slate-300 mb-2" />
                    <p className="text-sm text-slate-500">No pending sanctions</p>
                    <p className="text-xs text-slate-400 mt-0.5">Recommended leave requests will appear here.</p>
                  </div>
                }
                columns={[
                  buildEmployeeColumn(openEmployeeHistory),
                  { key: "leave_type_code", header: "Type" },
                  {
                    key: "dates",
                    header: "Dates",
                    className: "text-sm",
                    headClassName: "",
                    render: (leave) => <>{formatDate(leave.from_date)} &ndash; {formatDate(leave.to_date)}</>,
                  },
                  { key: "days_applied", header: "Days", className: "hidden sm:table-cell" },
                  REASON_COLUMN,
                  {
                    key: "recommended_by",
                    header: "Recommended By",
                    className: "hidden md:table-cell",
                    render: (leave) => <span className="text-sm text-slate-600">{leave.recommended_by_name || ""}</span>,
                  },
                  {
                    key: "action",
                    header: "Action",
                    className: "text-right",
                    render: (leave) => (
                      <div className="flex justify-end gap-2">
                        <Button size="sm" className="gap-1" onClick={() => openActionDialog("sanction", leave)}>
                          <CheckCircle2 className="w-4 h-4" /> Sanction
                        </Button>
                        <Button variant="outline" size="sm" className="gap-1 text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => openActionDialog("reject", leave)}>
                          <XCircle className="w-4 h-4" /> Reject
                        </Button>
                      </div>
                    ),
                  },
                ]}
              />
            </CardContent>
          </Card>
        )}
      </div>

      <LeaveActionDialog
        dialog={actionDialog}
        onClose={() => setActionDialog({ open: false, action: null, record: null })}
        onDone={fetchData}
      />
    </>
  );
};

export default LeaveDashboard;
