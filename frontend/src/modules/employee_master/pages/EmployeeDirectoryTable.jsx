import { useNavigate } from "react-router-dom";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { EmployeeTableSkeleton, SearchBarSkeleton } from "@/shared/ui/skeletons";
import { cn } from "@/shared/lib/utils";
import {
  ArrowUpDown,
  Key,
  RefreshCw,
  Users,
} from "lucide-react";
import {
  COLUMN_DEFS,
  renderCell,
} from "@/modules/employee_master/pages/EmployeeDirectoryPage.support";

const formatEmployeeDirectoryDate = (value) => {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return value;
  }
};

const EmployeeDirectoryTable = ({
  actionLoading,
  canManageEmployeeAccounts,
  dir,
  getProvisioningAvailability,
  handleProvisionAccount,
  isPortalPath,
  labelMaps,
  tableRef,
  visibleColumns,
}) => {
  const navigate = useNavigate();

  const SortHeader = ({ field, children, className }) => (
    <TableHead
      className={cn("cursor-pointer select-none hover:text-slate-900 transition-colors", className)}
      onClick={() => dir.toggleSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        <ArrowUpDown
          className={cn(
            "w-3 h-3 opacity-40",
            dir.sortField === field && "opacity-100 text-blue-600"
          )}
        />
      </span>
    </TableHead>
  );

  if (dir.loading) {
    return (
      <div data-testid="employees-loading" className="space-y-6">
        <SearchBarSkeleton />
        <EmployeeTableSkeleton rows={8} />
      </div>
    );
  }

  if (dir.employees.length === 0) {
    return (
      <Card>
        <CardContent className="py-16">
          <div className="flex flex-col items-center justify-center text-center">
            <Users className="w-7 h-7 text-slate-300 mb-3" />
            <p className="text-sm font-medium text-slate-600">No employees found</p>
            <p className="text-xs text-slate-400 mt-1">
              {dir.query ? "Try a different search term" : "No employee records yet"}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div
      className="rounded-xl border bg-white shadow-sm overflow-hidden"
      data-testid="employees-table"
    >
      <div
        ref={tableRef}
        className="max-h-[70vh] overflow-auto"
      >
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-slate-50/95 backdrop-blur-sm">
            <TableRow className="border-b-2 border-slate-200">
              {COLUMN_DEFS.filter((col) => visibleColumns.has(col.key)).map((col) => (
                <SortHeader key={col.key} field={col.sortField}>{col.label}</SortHeader>
              ))}
              {canManageEmployeeAccounts && (
                <TableHead className="text-right">Login Account</TableHead>
              )}
            </TableRow>
          </TableHeader>
          <TableBody>
            {dir.employees.map((emp, rowIdx) => {
              const profilePath = isPortalPath
                ? `/portal/employees/${emp.employee_id}`
                : `/employees/${emp.employee_id}`;

              return (
                <TableRow
                  key={emp.employee_id}
                  className={cn(
                    "hover:bg-blue-50/60 cursor-pointer group transition-colors",
                    rowIdx % 2 === 1 && "bg-slate-50/40"
                  )}
                  onClick={() => navigate(profilePath)}
                  data-testid={`employees-row-${emp.employee_id}`}
                >
                  {COLUMN_DEFS.filter((col) => visibleColumns.has(col.key)).map((col) => (
                    <TableCell key={col.key} className="whitespace-nowrap text-sm text-slate-600">
                      {renderCell(emp, col.key, formatEmployeeDirectoryDate, labelMaps)}
                    </TableCell>
                  ))}
                  {canManageEmployeeAccounts && (
                    <TableCell className="text-right">
                      {(() => {
                        const availability = getProvisioningAvailability(emp);
                        const isProvisioning = actionLoading === `provision-${emp.employee_id}`;

                        return availability.canProvision ? (
                          <Button
                            variant="outline"
                            size="sm"
                            className="gap-1.5"
                            data-testid={`employees-provision-${emp.employee_id}`}
                            disabled={isProvisioning}
                            title={availability.reason}
                            onClick={(event) => {
                              event.stopPropagation();
                              void handleProvisionAccount(emp);
                            }}
                          >
                            {isProvisioning ? (
                              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Key className="w-3.5 h-3.5" />
                            )}
                            {isProvisioning ? "Provisioning..." : availability.label}
                          </Button>
                        ) : (
                          <div className="inline-flex flex-col items-end gap-1">
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-[11px] font-normal",
                                emp?.has_login_account
                                  ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                                  : "text-slate-500"
                              )}
                            >
                              {availability.label}
                            </Badge>
                            <span className="text-[11px] text-slate-400">{availability.reason}</span>
                          </div>
                        );
                      })()}
                    </TableCell>
                  )}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default EmployeeDirectoryTable;
