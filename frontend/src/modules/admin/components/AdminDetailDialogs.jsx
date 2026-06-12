import { AlertTriangle, CheckCircle2, Settings } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/shared/ui/dialog";
import { Label } from "@/shared/ui/label";
import { dedupeAuthorityCodes } from "@/modules/admin/hooks/authorityNormalization";

const DEPARTMENT_MANAGED_ROLES = new Set(["DEPT_DATA_ENTRY", "HOD"]);

const AdminDetailDialogs = ({
  editUserDialog,
  setEditUserDialog,
  availableAuthorities,
  authorityHolders = {},
  editUserRoles,
  setEditUserRoles,
  handleSaveUserRoles,
}) => {
  return (
    <>
      <Dialog open={editUserDialog.open} onOpenChange={(open) => !open && setEditUserDialog({ open: false, user: null })}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base"><Settings className="w-4 h-4" />Edit User Roles</DialogTitle>
            <DialogDescription>
              Modify roles for: <strong>{editUserDialog.user?.name}</strong> ({editUserDialog.user?.email})
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-1">
            <div className="p-3 bg-amber-50/60 border border-amber-200/60 rounded-xl text-xs text-amber-700 flex items-start gap-2">
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              <span>Role changes are logged to the audit trail. Department-scoped roles (HOD, Data Entry) are managed in the Department Roles tab.</span>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-slate-600">Current Roles</Label>
              <div className="flex flex-wrap gap-1.5 p-2.5 bg-slate-50/80 rounded-xl border border-slate-100 min-h-[40px]">
                {dedupeAuthorityCodes(editUserDialog.user?.authorities || []).map((a) => (
                  <Badge key={a} variant="outline" className="text-xs">{a}</Badge>
                )) || <span className="text-slate-400 text-xs">No roles assigned</span>}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-slate-600">Select New Roles</Label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-64 overflow-auto p-2 border rounded-xl">
                {availableAuthorities
                  .filter((auth) => {
                    const code = typeof auth === "string" ? auth : auth.code;
                    return !DEPARTMENT_MANAGED_ROLES.has(code);
                  })
                  .map((auth) => {
                  const code = typeof auth === "string" ? auth : auth.code;
                  const name = typeof auth === "string" ? auth : auth.name;
                  const isSelected = editUserRoles.includes(code);
                  const holder = authorityHolders[code];
                  const heldByOther = holder && holder.user_id !== editUserDialog.user?.id;
                  const blocked = heldByOther && !isSelected;
                  return (
                    <div
                      key={code}
                      className={`p-2.5 border rounded-lg transition-all ${blocked ? "opacity-40 cursor-not-allowed bg-slate-50" : "cursor-pointer"} ${isSelected && !blocked ? "bg-blue-50/80 border-blue-300 shadow-sm" : !blocked ? "hover:bg-slate-50 hover:border-slate-300" : ""}`}
                      onClick={() => {
                        if (blocked) return;
                        if (isSelected) {
                          setEditUserRoles(editUserRoles.filter((r) => r !== code));
                        } else {
                          setEditUserRoles([...editUserRoles, code]);
                        }
                      }}
                      title={heldByOther ? `Held by ${holder.name} (${holder.email})` : ""}
                    >
                      <div className="flex items-center gap-2">
                        <div className={`w-4 h-4 border rounded ${isSelected && !blocked ? "bg-blue-500 border-blue-500" : "border-slate-300"}`}>
                          {isSelected && !blocked && <CheckCircle2 className="w-4 h-4 text-white" />}
                        </div>
                        <span className="text-sm">{name}</span>
                      </div>
                      {heldByOther && (
                        <p className="text-[10px] text-red-500 mt-1 ml-6 truncate">Held by {holder.name}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditUserDialog({ open: false, user: null })}>Cancel</Button>
            <Button onClick={handleSaveUserRoles}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default AdminDetailDialogs;