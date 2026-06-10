import { useNavigate } from "react-router-dom";

import { DEPT } from "@/shared/lib/routes";
import { cn } from "@/shared/lib/utils";
import { Avatar, AvatarFallback } from "@/shared/ui/avatar";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import {
  ArrowUpRight, MoreHorizontal,
} from "lucide-react";

const STATUS_STYLES = {
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
};

const EMPLOYEE_STATUS_STYLES = {
  ACTIVE: "border-green-300 text-green-700 bg-green-50",
  RETIRED: "border-amber-300 text-amber-700 bg-amber-50",
  SUSPENDED: "border-red-300 text-red-700 bg-red-50",
  DECEASED: "border-slate-400 text-slate-600 bg-slate-100",
};

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

export function EmployeeCard({
  employee,
}) {
  const navigate = useNavigate();

  const workflowStatus = employee?.workflow_status || "DRAFT";
  const employeeStatus = employee?.employee_status || "-";
  const initials = getInitials(employee?.full_name);
  const avatarColor = getAvatarColor(employee?.employee_id);

  return (
    <Card
      className="group hover:shadow-md hover:border-blue-200 transition-all duration-200 cursor-pointer relative overflow-hidden"
      onClick={() => navigate(DEPT.EMPLOYEE(employee.employee_id))}
      data-testid={`dept-directory-card-${employee.employee_id}`}
    >
      {/* Top accent bar based on workflow status */}
      <div className={cn("h-1 w-full", STATUS_STYLES[workflowStatus]?.replace("text-", "bg-").split(" ").find(c => c.startsWith("bg-")) || "bg-slate-200")} />

      <CardContent className="p-4">
        {/* Header row: avatar + name + overflow menu */}
        <div className="flex items-start gap-3">
          <Avatar className="h-11 w-11 shrink-0">
            <AvatarFallback className={cn("text-white text-sm font-semibold", avatarColor)}>
              {initials}
            </AvatarFallback>
          </Avatar>

          <div className="min-w-0 flex-1">
            <p className="font-semibold text-slate-900 truncate text-sm group-hover:text-blue-700 transition-colors">
              {employee.full_name || "Employee"}
            </p>
            <p className="text-xs text-slate-500 font-mono truncate">
              {employee.employee_code || employee.employee_id || "-"}
            </p>
          </div>

          {/* Overflow menu */}
          <div onClick={(e) => e.stopPropagation()}>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
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
          </div>
        </div>

        {/* Detail rows */}
        <div className="mt-3 space-y-1.5 text-xs text-slate-600">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Designation</span>
            <span className="font-medium truncate ml-2 max-w-[60%] text-right">
              {employee.current_designation_id || employee.designation_code || "-"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Office</span>
            <span className="font-medium truncate ml-2 max-w-[60%] text-right">
              {employee.current_office_id || employee.office_code || "-"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Type</span>
            <span className="font-medium">
              {employee.employment_type || employee.employment_type_code || "-"}
            </span>
          </div>
        </div>

        {/* Footer: status badges */}
        <div className="mt-3 pt-3 border-t flex items-center justify-between gap-2">
          <Badge
            variant="outline"
            className={cn("text-[10px] font-medium", EMPLOYEE_STATUS_STYLES[employeeStatus])}
          >
            {employeeStatus}
          </Badge>
          <Badge className={cn("text-[10px]", STATUS_STYLES[workflowStatus] || "bg-slate-100 text-slate-700")}>
            {workflowStatus}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

export { STATUS_STYLES, EMPLOYEE_STATUS_STYLES };
