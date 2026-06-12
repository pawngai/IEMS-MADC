import { useNavigate } from "react-router-dom";

import { DEPT } from "@/shared/lib/routes";
import { cn } from "@/shared/lib/utils";
import { Avatar, AvatarFallback } from "@/shared/ui/avatar";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/shared/ui/table";
import {
  ArrowUpDown, ArrowUpRight, MoreHorizontal,
} from "lucide-react";

import { STATUS_STYLES, EMPLOYEE_STATUS_STYLES } from "@/modules/organization_master/components/EmployeeCard";

const COLUMN_DEFS = [
  { key: "full_name", label: "Employee", sortField: "full_name" },
  { key: "designation", label: "Designation", sortField: "current_designation_id" },
  { key: "office", label: "Office", sortField: "current_office_id" },
  { key: "employment_type", label: "Type", sortField: "employment_type" },
  { key: "employee_status", label: "Status", sortField: "employee_status" },
  { key: "workflow_status", label: "Workflow", sortField: "workflow_status" },
];

const getInitials = (name) => {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
};

const AVATAR_COLORS = [
  "bg-blue-600", "bg-emerald-600", "bg-violet-600", "bg-amber-600",
  "bg-rose-600", "bg-cyan-600", "bg-indigo-600", "bg-teal-600",
];

const getAvatarColor = (id) => {
  if (!id) return AVATAR_COLORS[0];
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) | 0;
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
};

const renderCell = (employee, columnKey) => {
  switch (columnKey) {
    case "full_name":
      return (
        <div className="flex items-center gap-3 min-w-0">
          <Avatar className="h-8 w-8 shrink-0">
            <AvatarFallback className={cn("text-white text-xs font-semibold", getAvatarColor(employee.employee_id))}>
              {getInitials(employee.full_name)}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <p className="font-medium text-slate-900 truncate text-sm group-hover:text-blue-700 transition-colors">
              {employee.full_name || "Employee"}
            </p>
            <p className="text-xs text-slate-500 font-mono truncate">{employee.employee_code || "-"}</p>
          </div>
        </div>
      );
    case "designation":
      return <span className="truncate block max-w-[180px] text-sm">{employee.current_designation_id || employee.designation_code || "-"}</span>;
    case "office":
      return <span className="truncate block max-w-[180px] text-sm">{employee.current_office_id || employee.office_code || "-"}</span>;
    case "employment_type":
      return <Badge variant="outline" className="text-xs font-normal">{employee.employment_type || employee.employment_type_code || "-"}</Badge>;
    case "employee_status":
      return (
        <Badge variant="outline" className={cn("text-xs font-normal", EMPLOYEE_STATUS_STYLES[employee.employee_status])}>
          {employee.employee_status || "-"}
        </Badge>
      );
    case "workflow_status":
      return <Badge className={cn("text-xs", STATUS_STYLES[employee.workflow_status] || "bg-slate-100 text-slate-700")}>{employee.workflow_status || "DRAFT"}</Badge>;
    default:
      return "-";
  }
};

export function EmployeeTableView({
  employees,
  sortField,
  toggleSort,
}) {
  const navigate = useNavigate();

  return (
    <div className="rounded-xl border bg-white shadow-sm overflow-hidden" data-testid="dept-directory-table">
      <Table>
        <TableHeader className="sticky top-0 z-10 bg-slate-50/95 backdrop-blur-sm">
          <TableRow className="border-b-2 border-slate-200">
            {COLUMN_DEFS.map((col) => (
              <TableHead
                key={col.key}
                className="cursor-pointer select-none hover:text-slate-900 transition-colors"
                onClick={() => toggleSort(col.sortField)}
              >
                <span className="inline-flex items-center gap-1">
                  {col.label}
                  <ArrowUpDown className={cn("w-3 h-3 opacity-40", sortField === col.sortField && "opacity-100 text-blue-600")} />
                </span>
              </TableHead>
            ))}
            <TableHead className="text-right w-12" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {employees.map((employee, rowIndex) => {
            return (
              <TableRow
                key={employee.employee_id}
                className={cn(
                  "hover:bg-blue-50/60 cursor-pointer group transition-colors",
                  rowIndex % 2 === 1 && "bg-slate-50/40"
                )}
                onClick={() => navigate(DEPT.EMPLOYEE(employee.employee_id))}
                data-testid={`dept-directory-row-${employee.employee_id}`}
              >
                {COLUMN_DEFS.map((col) => (
                  <TableCell key={col.key} className="whitespace-nowrap text-sm text-slate-600">
                    {renderCell(employee, col.key)}
                  </TableCell>
                ))}
                <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <DropdownMenuItem onClick={() => navigate(DEPT.EMPLOYEE(employee.employee_id))}>
                        <ArrowUpRight className="w-3.5 h-3.5 mr-2" />
                        Open Profile
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
