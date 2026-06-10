import { UserPlus } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/shared/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "@/shared/ui/sheet";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { SearchableSelect } from "@/shared/ui/searchable-select";
import { Textarea } from "@/shared/ui/textarea";

const AdminActionDialogs = ({
  createUserDialog,
  setCreateUserDialog,
  newUser,
  setNewUser,
  authorityOptions,
  employees,
  handleCreateUser,
  confirmDialog,
  setConfirmDialog,
  confirmAction,
  reasonDialog,
  setReasonDialog,
  actionReason,
  setActionReason,
  confirmReasonAction,
}) => {
  const employeeOptions = (employees || []).map((employee) => ({
    value: employee.employee_id,
    label: `${employee.employee_code || employee.employee_id} - ${employee.full_name || employee.employee_id}`,
    search: [
      employee.employee_id,
      employee.employee_code,
      employee.full_name,
      employee.current_department_id,
    ].filter(Boolean).join(" "),
  }));

  return (
    <>
      <Sheet open={createUserDialog} onOpenChange={setCreateUserDialog}>
        <SheetContent side="right" size="md">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2"><UserPlus className="w-4 h-4" />Create New User</SheetTitle>
            <SheetDescription>Add a new user to the system with an initial role.</SheetDescription>
          </SheetHeader>
          <div className="space-y-5 py-4">
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-slate-600">Email *</Label>
              <Input type="email" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} placeholder="user@iems.gov.in" className="rounded-lg" />
              {newUser.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newUser.email) && <p className="text-xs text-red-500">Invalid email format</p>}
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-slate-600">Full Name *</Label>
              <Input value={newUser.name} onChange={(e) => setNewUser({ ...newUser, name: e.target.value })} className="rounded-lg" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-slate-600">Password *</Label>
              <Input type="password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} className="rounded-lg" />
              {newUser.password && (
                <div className="space-y-1">
                  <div className="flex gap-1">
                    <div className={`h-1 flex-1 rounded ${newUser.password.length >= 8 ? "bg-green-500" : "bg-red-300"}`} />
                    <div className={`h-1 flex-1 rounded ${/[A-Z]/.test(newUser.password) && /[a-z]/.test(newUser.password) ? "bg-green-500" : "bg-red-300"}`} />
                    <div className={`h-1 flex-1 rounded ${/[0-9]/.test(newUser.password) ? "bg-green-500" : "bg-red-300"}`} />
                    <div className={`h-1 flex-1 rounded ${/[^A-Za-z0-9]/.test(newUser.password) ? "bg-green-500" : "bg-slate-200"}`} />
                  </div>
                  <p className="text-xs text-slate-500">Min 8 chars, upper + lower + number. Special char recommended.</p>
                </div>
              )}
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-slate-600">Role</Label>
              <SearchableSelect
                value={newUser.authorities[0] || "none"}
                onValueChange={(v) => setNewUser({ ...newUser, authorities: v === "none" ? [] : [v] })}
                options={authorityOptions}
                placeholder="Select role"
                searchPlaceholder="Search roles..."
                dataTestId="new-user-role"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-slate-600">Linked Employee (optional)</Label>
              <SearchableSelect
                value={newUser.employee_id || ""}
                onValueChange={(value) => setNewUser({ ...newUser, employee_id: value })}
                options={employeeOptions}
                placeholder="Search employee by code, ID, or name"
                searchPlaceholder="Search employees..."
                emptyMessage="No employees available"
                dataTestId="new-user-employee"
              />
              <p className="text-xs text-slate-500">
                Link a user to an employee record when the account should inherit employee context.
              </p>
            </div>
          </div>
          <SheetFooter className="mt-6 gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setCreateUserDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateUser} className="gap-1.5"><UserPlus className="w-3.5 h-3.5" />Create User</Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      <Dialog open={confirmDialog.open} onOpenChange={(open) => !open && setConfirmDialog({ open: false, action: null, data: null })}>
        <DialogContent>
          <DialogHeader><DialogTitle>Confirm Action</DialogTitle><DialogDescription>{confirmDialog.action === "reset_password" && `Reset password for ${confirmDialog.data?.name}?`}</DialogDescription></DialogHeader>
          <DialogFooter><Button variant="outline" onClick={() => setConfirmDialog({ open: false, action: null, data: null })}>Cancel</Button><Button onClick={confirmAction}>Confirm</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={reasonDialog.open} onOpenChange={(open) => {
        if (!open) {
          setReasonDialog({ open: false, action: null, data: null });
          setActionReason("");
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reason Required</DialogTitle>
            <DialogDescription>This action requires a mandatory reason.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Textarea value={actionReason} onChange={(e) => setActionReason(e.target.value)} placeholder="Enter reason..." rows={3} />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setReasonDialog({ open: false, action: null, data: null });
                setActionReason("");
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={confirmReasonAction}
              disabled={!actionReason.trim()}
            >
              Submit
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default AdminActionDialogs;