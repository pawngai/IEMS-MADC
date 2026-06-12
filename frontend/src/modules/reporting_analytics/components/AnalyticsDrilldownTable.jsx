import { Badge } from "@/shared/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import {
  formatAnalyticsCategoryLabel,
  formatAnalyticsDate,
  formatGenderAnalyticsLabel,
  formatLeaveStatusLabel,
  formatLeaveTypeLabel,
  formatServiceEventTypeLabel,
  formatWorkflowStageLabel,
} from "@/modules/reporting_analytics/model/analyticsDashboardModel";

const renderEmployeeIdentity = (row) => {
  const primary = row.employee_name || row.employee_code || row.employee_id || "-";
  const secondary = row.employee_code && row.employee_code !== row.employee_name
    ? row.employee_code
    : row.employee_id;

  return (
    <div className="min-w-0">
      <p className="truncate font-medium text-slate-900">{primary}</p>
      {secondary && <p className="truncate text-xs text-muted-foreground">{secondary}</p>}
    </div>
  );
};

const AnalyticsDrilldownTable = ({
  config,
  departmentNameMap,
  designationNameMap,
  displayedRows,
  leaveTypeNameMap,
  officeNameMap,
  renderActionCell,
  rows,
  serviceEventTypeNameMap,
  serviceGroupNameMap,
  serviceNameMap,
  visibleWorkforceFieldSet,
}) => {
  const renderRows = () => {
    if (config?.section === "workforce") {
      return displayedRows.map((row) => (
        <TableRow key={row.employee_id || row.employee_code}>
          <TableCell>{renderEmployeeIdentity(row)}</TableCell>
          {visibleWorkforceFieldSet.has("department") && (
            <TableCell>{formatAnalyticsCategoryLabel(row.department_id, { emptyLabel: "Unassigned", nameMap: departmentNameMap })}</TableCell>
          )}
          {visibleWorkforceFieldSet.has("designation") && (
            <TableCell>{formatAnalyticsCategoryLabel(row.designation_id, { emptyLabel: "Unassigned", nameMap: designationNameMap })}</TableCell>
          )}
          {visibleWorkforceFieldSet.has("employmentType") && (
            <TableCell>{formatAnalyticsCategoryLabel(row.employment_type)}</TableCell>
          )}
          {visibleWorkforceFieldSet.has("status") && (
            <TableCell>
              <Badge variant="outline">{formatAnalyticsCategoryLabel(row.employee_status)}</Badge>
            </TableCell>
          )}
          {visibleWorkforceFieldSet.has("gender") && <TableCell>{formatGenderAnalyticsLabel(row.gender)}</TableCell>}
          {visibleWorkforceFieldSet.has("office") && (
            <TableCell>{formatAnalyticsCategoryLabel(row.office_id, { emptyLabel: "Unassigned", nameMap: officeNameMap })}</TableCell>
          )}
          {visibleWorkforceFieldSet.has("workflowStatus") && (
            <TableCell><Badge variant="outline">{formatWorkflowStageLabel(row.workflow_status)}</Badge></TableCell>
          )}
          {visibleWorkforceFieldSet.has("service") && (
            <TableCell>{formatAnalyticsCategoryLabel(row.service, { emptyLabel: "Unassigned", nameMap: serviceNameMap })}</TableCell>
          )}
          {visibleWorkforceFieldSet.has("serviceGroup") && (
            <TableCell>{formatAnalyticsCategoryLabel(row.service_group, { emptyLabel: "Unassigned", nameMap: serviceGroupNameMap })}</TableCell>
          )}
          {visibleWorkforceFieldSet.has("maritalStatus") && (
            <TableCell>{formatAnalyticsCategoryLabel(row.marital_status, { emptyLabel: "Not specified" })}</TableCell>
          )}
          {visibleWorkforceFieldSet.has("dateOfBirth") && <TableCell>{formatAnalyticsDate(row.date_of_birth)}</TableCell>}
          {visibleWorkforceFieldSet.has("initialEngagement") && <TableCell>{formatAnalyticsDate(row.date_of_initial_engagement)}</TableCell>}
          {visibleWorkforceFieldSet.has("statusEffectiveDate") && <TableCell>{formatAnalyticsDate(row.status_effective_date)}</TableCell>}
          {visibleWorkforceFieldSet.has("reportingOfficer") && <TableCell>{row.reporting_officer_id || "-"}</TableCell>}
          {visibleWorkforceFieldSet.has("createdAt") && <TableCell>{formatAnalyticsDate(row.created_at, { includeTime: true })}</TableCell>}
          {visibleWorkforceFieldSet.has("updatedAt") && <TableCell>{formatAnalyticsDate(row.updated_at, { includeTime: true })}</TableCell>}
          <TableCell className="text-right">{renderActionCell(row)}</TableCell>
        </TableRow>
      ));
    }

    if (config?.section === "workflow") {
      return rows.map((row) => {
        const lastStageChange = row.locked_at || row.approved_at || row.verified_at || row.submitted_at;
        return (
          <TableRow key={`${row.employee_id}-${row.workflow_status}`}>
            <TableCell>{renderEmployeeIdentity(row)}</TableCell>
            <TableCell>
              <Badge variant="outline">{formatWorkflowStageLabel(row.workflow_status)}</Badge>
            </TableCell>
            <TableCell>{formatAnalyticsCategoryLabel(row.department_id, { emptyLabel: "Unassigned", nameMap: departmentNameMap })}</TableCell>
            <TableCell>{formatAnalyticsDate(lastStageChange)}</TableCell>
            <TableCell className="text-right">{renderActionCell(row)}</TableCell>
          </TableRow>
        );
      });
    }

    if (config?.section === "leave") {
      return rows.map((row) => (
        <TableRow key={row.leave_id || `${row.employee_id}-${row.applied_at}`}>
          <TableCell>{renderEmployeeIdentity(row)}</TableCell>
          <TableCell>{formatLeaveTypeLabel(row.leave_type_code, leaveTypeNameMap)}</TableCell>
          <TableCell>
            <Badge variant="outline">{formatLeaveStatusLabel(row.status)}</Badge>
          </TableCell>
          <TableCell>{row.from_date && row.to_date ? `${row.from_date} to ${row.to_date}` : "-"}</TableCell>
          <TableCell>{formatAnalyticsDate(row.applied_at, { includeTime: true })}</TableCell>
          <TableCell className="text-right">{renderActionCell(row)}</TableCell>
        </TableRow>
      ));
    }

    return rows.map((row) => (
      <TableRow key={row.service_event_id || `${row.employee_id}-${row.created_at}`}>
        <TableCell>{renderEmployeeIdentity(row)}</TableCell>
        <TableCell>{formatServiceEventTypeLabel(row.event_type, serviceEventTypeNameMap)}</TableCell>
        <TableCell>{formatAnalyticsDate(row.effective_date)}</TableCell>
        <TableCell>{formatAnalyticsDate(row.created_at, { includeTime: true })}</TableCell>
        <TableCell className="text-right">{renderActionCell(row)}</TableCell>
      </TableRow>
    ));
  };

  const renderHeaderRow = () => {
    if (config?.section === "workforce") {
      return (
        <TableRow>
          <TableHead>Employee</TableHead>
          {visibleWorkforceFieldSet.has("department") && <TableHead>Department</TableHead>}
          {visibleWorkforceFieldSet.has("designation") && <TableHead>Designation</TableHead>}
          {visibleWorkforceFieldSet.has("employmentType") && <TableHead>Employment Type</TableHead>}
          {visibleWorkforceFieldSet.has("status") && <TableHead>Status</TableHead>}
          {visibleWorkforceFieldSet.has("gender") && <TableHead>Gender</TableHead>}
          {visibleWorkforceFieldSet.has("office") && <TableHead>Office</TableHead>}
          {visibleWorkforceFieldSet.has("workflowStatus") && <TableHead>Workflow Status</TableHead>}
          {visibleWorkforceFieldSet.has("service") && <TableHead>Service</TableHead>}
          {visibleWorkforceFieldSet.has("serviceGroup") && <TableHead>Service Group</TableHead>}
          {visibleWorkforceFieldSet.has("maritalStatus") && <TableHead>Marital Status</TableHead>}
          {visibleWorkforceFieldSet.has("dateOfBirth") && <TableHead>Date of Birth</TableHead>}
          {visibleWorkforceFieldSet.has("initialEngagement") && <TableHead>Initial Engagement</TableHead>}
          {visibleWorkforceFieldSet.has("statusEffectiveDate") && <TableHead>Status Effective</TableHead>}
          {visibleWorkforceFieldSet.has("reportingOfficer") && <TableHead>Reporting Officer</TableHead>}
          {visibleWorkforceFieldSet.has("createdAt") && <TableHead>Created</TableHead>}
          {visibleWorkforceFieldSet.has("updatedAt") && <TableHead>Updated</TableHead>}
          <TableHead className="text-right">Action</TableHead>
        </TableRow>
      );
    }

    if (config?.section === "workflow") {
      return (
        <TableRow>
          <TableHead>Employee</TableHead>
          <TableHead>Stage</TableHead>
          <TableHead>Department</TableHead>
          <TableHead>Latest Stage Change</TableHead>
          <TableHead className="text-right">Action</TableHead>
        </TableRow>
      );
    }

    if (config?.section === "leave") {
      return (
        <TableRow>
          <TableHead>Employee</TableHead>
          <TableHead>Leave Type</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Dates</TableHead>
          <TableHead>Applied</TableHead>
          <TableHead className="text-right">Action</TableHead>
        </TableRow>
      );
    }

    return (
      <TableRow>
        <TableHead>Employee</TableHead>
        <TableHead>Event Type</TableHead>
        <TableHead>Effective Date</TableHead>
        <TableHead>Recorded</TableHead>
        <TableHead className="text-right">Action</TableHead>
      </TableRow>
    );
  };

  return (
    <Table>
      <TableHeader>{renderHeaderRow()}</TableHeader>
      <TableBody>{renderRows()}</TableBody>
    </Table>
  );
};

export default AnalyticsDrilldownTable;
