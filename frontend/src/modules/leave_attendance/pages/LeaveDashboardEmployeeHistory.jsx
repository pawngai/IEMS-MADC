import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { SearchableSelect } from "@/shared/ui/searchable-select";
import { DataTable } from "@/shared/data-table";
import { Calendar } from "lucide-react";
import { LeaveStatusBadge } from "@/modules/leave_attendance/components/LeaveStatusBadge";
import LeaveAttachmentLinks from "@/modules/leave_attendance/pages/LeaveAttachmentLinks";
import { LEAVE_TYPE_LABELS } from "@/modules/leave_attendance/pages/useLeaveDashboardController";

const formatDate = (isoDate) => {
  if (!isoDate) return "";
  const d = new Date(isoDate + "T00:00:00");
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
};

const LEAVE_HISTORY_COLUMNS = [
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
  {
    key: "days_applied",
    header: "Days",
    className: "hidden sm:table-cell",
  },
  {
    key: "status",
    header: "Status",
    render: (leave) => <LeaveStatusBadge status={leave.status} />,
  },
  {
    key: "applied_at",
    header: "Applied",
    className: "hidden sm:table-cell",
    render: (leave) => (leave.applied_at ? new Date(leave.applied_at).toLocaleDateString("en-GB") : "-"),
  },
];

const LeaveDashboardEmployeeHistory = ({
  balanceCardStyles,
  canViewEmployeeHistory,
  defaultCardStyle,
  employeeHistoryLeaveTypeOptions,
  employeeHistorySearchLoading,
  employeeHistorySearchQuery,
  employeeHistorySearchResults,
  filteredSelectedEmployeeLeaves,
  isEmployeeHistoryMode,
  openEmployeeHistory,
  selectedEmployeeBalances,
  selectedEmployeeId,
  selectedEmployeeLeaveSummary,
  selectedEmployeeLeaveType,
  selectedEmployeeLeaves,
  setEmployeeHistorySearchQuery,
  setSelectedEmployeeLeaveType,
}) => (
  <>
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
                    const style = balanceCardStyles[code] || defaultCardStyle;
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
            <DataTable
              columns={LEAVE_HISTORY_COLUMNS}
              rows={filteredSelectedEmployeeLeaves}
              rowKey={(leave) => leave.id}
              emptyState={
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Calendar className="w-8 h-8 text-slate-300 mb-2" />
                  <p className="text-sm text-slate-500">
                    {selectedEmployeeLeaves.length === 0
                      ? "No leave history found for this employee"
                      : "No leave history found for the selected leave type"}
                  </p>
                </div>
              }
            />
          </CardContent>
        </Card>
      </>
    )}
  </>
);

export default LeaveDashboardEmployeeHistory;
