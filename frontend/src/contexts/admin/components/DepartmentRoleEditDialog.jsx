import { useState, useMemo } from "react";
import { AlertTriangle, Building2, Search } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";

export default function DepartmentRoleEditDialog({
  editDialog,
  onClose,
  onSave,
  employees,
  loadingEmployees,
  resolveEmployeeName,
  saving,
}) {
  const dept = editDialog?.department;
  const [hodId, setHodId] = useState(editDialog?.hod_employee_id || "");
  const [deId, setDeId] = useState(editDialog?.data_entry_employee_id || "");
  const [reason, setReason] = useState("");
  const [hodSearch, setHodSearch] = useState("");
  const [deSearch, setDeSearch] = useState("");

  // Reset state when dialog re-opens (controlled by key in parent)
  const filteredForHod = useMemo(() => {
    if (!hodSearch) return employees.slice(0, 20);
    const q = hodSearch.toLowerCase();
    return employees.filter(
      (e) =>
        (e.name || e.full_name || "").toLowerCase().includes(q) ||
        (e.employee_id || e.id || "").toLowerCase().includes(q)
    ).slice(0, 20);
  }, [employees, hodSearch]);

  const filteredForDe = useMemo(() => {
    if (!deSearch) return employees.slice(0, 20);
    const q = deSearch.toLowerCase();
    return employees.filter(
      (e) =>
        (e.name || e.full_name || "").toLowerCase().includes(q) ||
        (e.employee_id || e.id || "").toLowerCase().includes(q)
    ).slice(0, 20);
  }, [employees, deSearch]);

  const sameEmployee = hodId && deId && hodId === deId;
  const canSave = reason.trim().length >= 3 && !sameEmployee && !saving;

  const handleSave = () => {
    if (!canSave || !dept) return;
    onSave(dept.code, {
      hod_employee_id: hodId || "",
      data_entry_employee_id: deId || "",
      reason: reason.trim(),
    });
  };

  if (!dept) return null;

  return (
    <Dialog open={editDialog.open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <Building2 className="w-4 h-4" />
            Edit Department Roles
          </DialogTitle>
          <DialogDescription>
            Assign HOD and Data Entry Operator for <strong>{dept.name}</strong> ({dept.code})
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-1">
          <div className="p-3 bg-amber-50/60 border border-amber-200/60 rounded-xl text-xs text-amber-700 flex items-start gap-2">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
            <span>Changing role holders will automatically update user authorities. The old holder will lose the authority and the new holder will gain it.</span>
          </div>

          {/* HOD Picker */}
          <div className="space-y-1.5">
            <Label className="text-xs font-medium text-slate-600">Head of Department (HOD)</Label>
            {hodId && (
              <div className="flex items-center gap-2 p-2 bg-blue-50/60 border border-blue-200/60 rounded-lg text-xs">
                <span className="font-medium">{resolveEmployeeName(hodId) || hodId}</span>
                <Button variant="ghost" size="sm" className="h-5 px-1.5 text-[10px] ml-auto" onClick={() => setHodId("")}>Clear</Button>
              </div>
            )}
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
              <Input
                placeholder="Search employee..."
                value={hodSearch}
                onChange={(e) => setHodSearch(e.target.value)}
                className="pl-8 h-8 text-xs"
              />
            </div>
            <div className="max-h-32 overflow-auto border rounded-lg divide-y">
              {loadingEmployees ? (
                <div className="px-3 py-3 text-xs text-slate-400 text-center">Loading department employees...</div>
              ) : filteredForHod.length === 0 ? (
                <div className="px-3 py-2 text-xs text-slate-400 text-center">No employees found</div>
              ) : (
                filteredForHod.map((emp) => {
                const empId = emp.employee_id || emp.id;
                const name = emp.name || emp.full_name || empId;
                return (
                  <div
                    key={empId}
                    className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-blue-50 flex justify-between ${hodId === empId ? "bg-blue-50 font-medium" : ""}`}
                    onClick={() => { setHodId(empId); setHodSearch(""); }}
                  >
                    <span>{name}</span>
                    <span className="text-slate-400">{empId}</span>
                  </div>
                );
              }))
              }
            </div>
          </div>

          {/* Data Entry Picker */}
          <div className="space-y-1.5">
            <Label className="text-xs font-medium text-slate-600">Data Entry Operator</Label>
            {deId && (
              <div className="flex items-center gap-2 p-2 bg-emerald-50/60 border border-emerald-200/60 rounded-lg text-xs">
                <span className="font-medium">{resolveEmployeeName(deId) || deId}</span>
                <Button variant="ghost" size="sm" className="h-5 px-1.5 text-[10px] ml-auto" onClick={() => setDeId("")}>Clear</Button>
              </div>
            )}
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
              <Input
                placeholder="Search employee..."
                value={deSearch}
                onChange={(e) => setDeSearch(e.target.value)}
                className="pl-8 h-8 text-xs"
              />
            </div>
            <div className="max-h-32 overflow-auto border rounded-lg divide-y">
              {loadingEmployees ? (
                <div className="px-3 py-3 text-xs text-slate-400 text-center">Loading department employees...</div>
              ) : filteredForDe.length === 0 ? (
                <div className="px-3 py-2 text-xs text-slate-400 text-center">No employees found</div>
              ) : (
                filteredForDe.map((emp) => {
                const empId = emp.employee_id || emp.id;
                const name = emp.name || emp.full_name || empId;
                return (
                  <div
                    key={empId}
                    className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-emerald-50 flex justify-between ${deId === empId ? "bg-emerald-50 font-medium" : ""}`}
                    onClick={() => { setDeId(empId); setDeSearch(""); }}
                  >
                    <span>{name}</span>
                    <span className="text-slate-400">{empId}</span>
                  </div>
                );
              }))
              }
            </div>
          </div>

          {sameEmployee && (
            <div className="p-2.5 bg-red-50/60 border border-red-200/60 rounded-xl text-xs text-red-700">
              The same employee cannot hold both HOD and Data Entry Operator roles.
            </div>
          )}

          {/* Reason */}
          <div className="space-y-1.5">
            <Label className="text-xs font-medium text-slate-600">Reason for Change <span className="text-red-500">*</span></Label>
            <Textarea
              placeholder="Describe reason for role change (min 3 characters)..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="text-xs resize-none"
              rows={2}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button onClick={handleSave} disabled={!canSave}>
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
