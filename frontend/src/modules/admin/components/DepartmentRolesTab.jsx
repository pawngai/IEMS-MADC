import { useEffect } from "react";
import { Building2, ClipboardList, FileText, Pencil, Search } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import useDepartmentRoles from "@/modules/admin/hooks/useDepartmentRoles";
import DepartmentRoleEditDialog from "@/modules/admin/components/DepartmentRoleEditDialog";
import DepartmentRoleChangeLog from "@/modules/admin/components/DepartmentRoleChangeLog";
import DepartmentSanctionedStrengthDialog from "@/modules/admin/components/DepartmentSanctionedStrengthDialog";

export default function DepartmentRolesTab() {
  const {
    departments,
    employees,
    designations,
    deptEmployees,
    loadingDeptEmployees,
    loading,
    editDialog,
    logDialog,
    strengthDialog,
    setStrengthDialog,
    saving,
    fetchDepartments,
    fetchEmployees,
    openEditDialog,
    closeEditDialog,
    saveDepartmentRoles,
    openLogDialog,
    closeLogDialog,
    openStrengthDialog,
    closeStrengthDialog,
    saveDepartmentStrength,
    resolveEmployeeName,
  } = useDepartmentRoles();

  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchDepartments();
    fetchEmployees();
  }, [fetchDepartments, fetchEmployees]);

  const filtered = departments.filter((d) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (d.code || "").toLowerCase().includes(q) ||
      (d.name || "").toLowerCase().includes(q)
    );
  });

  const activeDepts = departments.filter((d) => d.is_active !== false);
  const withHod = departments.filter((d) => d.hod_employee_id);
  const withDe = departments.filter((d) => d.data_entry_employee_id);

  return (
    <>
      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Card className="border-0 shadow-sm">
          <CardContent className="pt-4 pb-3 px-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 font-medium">Active Departments</p>
                <p className="text-2xl font-bold text-slate-900">{activeDepts.length}</p>
              </div>
              <div className="p-2 bg-blue-50 rounded-lg">
                <Building2 className="w-5 h-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-sm">
          <CardContent className="pt-4 pb-3 px-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 font-medium">HOD Assigned</p>
                <p className="text-2xl font-bold text-slate-900">{withHod.length} <span className="text-sm font-normal text-slate-400">/ {activeDepts.length}</span></p>
              </div>
              <div className="p-2 bg-emerald-50 rounded-lg">
                <Building2 className="w-5 h-5 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-sm">
          <CardContent className="pt-4 pb-3 px-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 font-medium">Data Entry Assigned</p>
                <p className="text-2xl font-bold text-slate-900">{withDe.length} <span className="text-sm font-normal text-slate-400">/ {activeDepts.length}</span></p>
              </div>
              <div className="p-2 bg-amber-50 rounded-lg">
                <Building2 className="w-5 h-5 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                <Building2 className="w-4 h-4" />
                Department Role Assignments
              </CardTitle>
              <CardDescription>Manage HOD and Data Entry Operator assignments per department</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search departments by code or name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 rounded-lg"
              />
            </div>
          </div>

          {loading ? (
            <div className="py-12 text-center text-sm text-slate-400">Loading departments...</div>
          ) : (
            <div className="rounded-lg border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50/80">
                    <TableHead>Department</TableHead>
                    <TableHead>HOD</TableHead>
                    <TableHead>Data Entry Operator</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-slate-400">
                        No departments found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filtered.map((dept) => (
                      <TableRow key={dept.code} className="hover:bg-slate-50/50">
                        <TableCell>
                          <div>
                            <p className="font-medium text-sm">{dept.name}</p>
                            <p className="text-xs text-slate-500">{dept.code}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          {dept.hod_employee_id ? (
                            <div>
                              <p className="text-sm font-medium">{resolveEmployeeName(dept.hod_employee_id) || dept.hod_employee_id}</p>
                              <p className="text-[10px] text-slate-400">{dept.hod_employee_id}</p>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400 italic">Not assigned</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {dept.data_entry_employee_id ? (
                            <div>
                              <p className="text-sm font-medium">{resolveEmployeeName(dept.data_entry_employee_id) || dept.data_entry_employee_id}</p>
                              <p className="text-[10px] text-slate-400">{dept.data_entry_employee_id}</p>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400 italic">Not assigned</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge className={`${dept.is_active !== false ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-600 border-red-200"} border`}>
                            <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${dept.is_active !== false ? "bg-emerald-500" : "bg-red-500"}`} />
                            {dept.is_active !== false ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1.5">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                              onClick={() => openEditDialog(dept)}
                              title="Edit Role Assignments"
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                              onClick={() => openStrengthDialog(dept)}
                              title="Manage Sanctioned Strength"
                            >
                              <ClipboardList className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                              onClick={() => openLogDialog(dept)}
                              title="View Change Log"
                            >
                              <FileText className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialogs */}
      {editDialog.open && (
        <DepartmentRoleEditDialog
          key={editDialog.department?.code}
          editDialog={editDialog}
          onClose={closeEditDialog}
          onSave={saveDepartmentRoles}
          employees={deptEmployees}
          loadingEmployees={loadingDeptEmployees}
          resolveEmployeeName={resolveEmployeeName}
          saving={saving}
        />
      )}

      <DepartmentRoleChangeLog
        logDialog={logDialog}
        onClose={closeLogDialog}
      />

      {strengthDialog.open && (
        <DepartmentSanctionedStrengthDialog
          dialog={strengthDialog}
          setDialog={setStrengthDialog}
          designations={designations}
          onClose={closeStrengthDialog}
          onSave={saveDepartmentStrength}
          saving={saving}
        />
      )}
    </>
  );
}
