import { useState, useMemo, useCallback } from "react";
import { History, Shield, Pencil, CheckCircle2, Users, Search } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/shared/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { Input } from "@/shared/ui/input";
import { toast } from "sonner";
import { userManagementAPI } from "@/contexts/identity_access";
import { normalizeAuthorityCode, dedupeAuthorityCodes } from "@/contexts/admin/hooks/authorityNormalization";

const EXCLUDED_ROLES = new Set(["DEPT_DATA_ENTRY", "HOD", "EMPLOYEE"]);

const ROLE_COLORS = {
  SYSTEM_ADMIN: "bg-red-100 text-red-700",
  GLOBAL_DATA_ENTRY: "bg-cyan-100 text-cyan-700",
  DEALING_ASSISTANT: "bg-indigo-100 text-indigo-700",
  SECTION_OFFICER: "bg-violet-100 text-violet-700",
  VERIFIER: "bg-amber-100 text-amber-700",
  DDO: "bg-orange-100 text-orange-700",
  APPROVING_AUTHORITY: "bg-purple-100 text-purple-700",
  APPOINTING_AUTHORITY: "bg-pink-100 text-pink-700",
  DISCIPLINARY_AUTHORITY: "bg-rose-100 text-rose-700",
  AUDITOR: "bg-green-100 text-green-700",
  NODAL_OFFICER: "bg-teal-100 text-teal-700",
  EMPLOYEE: "bg-slate-100 text-slate-700",
};

const LABEL_OVERRIDES = { DDO: "DDO", HOD: "HOD" };

function getAuthorityLabel(code) {
  if (LABEL_OVERRIDES[code]) return LABEL_OVERRIDES[code];
  return String(code)
    .toLowerCase()
    .split("_")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : ""))
    .join(" ");
}

export default function RoleManagementTab({
  availableAuthorities = [],
  users = [],
  roleChangeStats,
  roleChangeHistory,
  onRefresh,
}) {
  const [editDialog, setEditDialog] = useState({ open: false, role: null });
  const [selectedUserIds, setSelectedUserIds] = useState(new Set());
  const [saving, setSaving] = useState(false);
  const [roleUserSearch, setRoleUserSearch] = useState("");

  // Build roles list excluding department-managed ones
  const roles = useMemo(() => {
    return availableAuthorities
      .map((auth) => {
        const code = typeof auth === "string" ? auth : auth.code;
        const name = typeof auth === "string" ? getAuthorityLabel(auth) : auth.name || getAuthorityLabel(auth.code);
        return { code, name };
      })
      .filter((r) => !EXCLUDED_ROLES.has(r.code));
  }, [availableAuthorities]);

  // Count holders per role from users list
  const holdersByRole = useMemo(() => {
    const map = {};
    for (const role of roles) {
      map[role.code] = users.filter((u) =>
        dedupeAuthorityCodes(u.authorities || []).includes(role.code)
      );
    }
    return map;
  }, [roles, users]);

  const handleOpenEdit = useCallback((role) => {
    const currentHolders = new Set(
      (holdersByRole[role.code] || []).map((u) => u.id || u._id)
    );
    setSelectedUserIds(currentHolders);
    setRoleUserSearch("");
    setEditDialog({ open: true, role });
  }, [holdersByRole]);

  const handleToggleUser = useCallback((userId) => {
    setSelectedUserIds((prev) => {
      const next = new Set(prev);
      if (next.has(userId)) next.delete(userId);
      else next.add(userId);
      return next;
    });
  }, []);

  const handleSaveRoleAssignment = useCallback(async () => {
    if (!editDialog.role) return;
    const roleCode = editDialog.role.code;
    const currentHolderIds = new Set(
      (holdersByRole[roleCode] || []).map((u) => u.id || u._id)
    );

    const toAdd = [...selectedUserIds].filter((id) => !currentHolderIds.has(id));
    const toRemove = [...currentHolderIds].filter((id) => !selectedUserIds.has(id));

    if (toAdd.length === 0 && toRemove.length === 0) {
      setEditDialog({ open: false, role: null });
      return;
    }

    setSaving(true);
    try {
      const ops = [
        ...toAdd.map((uid) => userManagementAPI.patchAuthorities(uid, { add: [roleCode], remove: [] })),
        ...toRemove.map((uid) => userManagementAPI.patchAuthorities(uid, { add: [], remove: [roleCode] })),
      ];
      await Promise.all(ops);
      toast.success(`${editDialog.role.name} assignments updated`);
      setEditDialog({ open: false, role: null });
      onRefresh?.();
    } catch {
      toast.error("Failed to update role assignments");
    } finally {
      setSaving(false);
    }
  }, [editDialog.role, selectedUserIds, holdersByRole, onRefresh]);

  return (
    <div className="space-y-6">
      {/* ROLES LIST */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                <Shield className="w-4 h-4 text-blue-600" />RBAC Roles
              </CardTitle>
              <CardDescription>Manage role assignments across the system</CardDescription>
            </div>
            <Badge variant="outline" className="font-normal">{roles.length} roles</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Role</TableHead>
                <TableHead>Holders</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {roles.map((role) => {
                const holders = holdersByRole[role.code] || [];
                return (
                  <TableRow key={role.code}>
                    <TableCell>
                      <Badge className={`${ROLE_COLORS[role.code] || "bg-slate-100 text-slate-700"} text-xs`}>
                        {role.name}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {holders.length === 0 ? (
                        <span className="text-xs text-slate-400">No holders</span>
                      ) : (
                        <div className="flex items-center gap-1.5">
                          <Users className="w-3.5 h-3.5 text-slate-400" />
                          <span className="text-sm">{holders.length}</span>
                          {holders.length <= 3 && (
                            <span className="text-xs text-slate-500 ml-1">
                              ({holders.map((h) => h.name).join(", ")})
                            </span>
                          )}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" className="gap-1.5 h-7 text-xs" onClick={() => handleOpenEdit(role)}>
                        <Pencil className="w-3.5 h-3.5" />Edit
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* AUDIT LOG */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                <History className="w-4 h-4 text-amber-600" />Role Change Audit Log
              </CardTitle>
              <CardDescription>Track all role assignments and revocations for compliance</CardDescription>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline" className="font-normal">{roleChangeStats.total_changes || 0} total</Badge>
              <Badge className="bg-amber-50 text-amber-700 border border-amber-200 font-normal">{roleChangeStats.changes_last_7_days || 0} this week</Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {roleChangeHistory.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center mx-auto mb-3">
                <History className="w-6 h-6 text-slate-300" />
              </div>
              <p className="font-medium text-slate-600">No role changes recorded</p>
              <p className="text-xs mt-0.5">Changes will appear here when user roles are modified</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Change</TableHead>
                  <TableHead>Changed By</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {roleChangeHistory.map((change) => (
                  <TableRow key={change.id}>
                    <TableCell className="text-xs font-mono">{new Date(change.timestamp).toLocaleString()}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium text-sm">{change.target_user_name}</p>
                        <p className="text-xs text-slate-500">{change.target_user_email}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        {change.roles_added?.length > 0 && (
                          <div className="flex items-center gap-1">
                            <span className="text-green-600 text-xs">+</span>
                            {change.roles_added.map((r) => (
                              <Badge key={r} className="bg-green-100 text-green-700 text-xs">{r}</Badge>
                            ))}
                          </div>
                        )}
                        {change.roles_removed?.length > 0 && (
                          <div className="flex items-center gap-1">
                            <span className="text-red-600 text-xs">-</span>
                            {change.roles_removed.map((r) => (
                              <Badge key={r} className="bg-red-100 text-red-700 text-xs">{r}</Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">{change.changed_by_name}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* ROLE EDIT DIALOG */}
      <Dialog open={editDialog.open} onOpenChange={(open) => !open && setEditDialog({ open: false, role: null })}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <Pencil className="w-4 h-4" />Edit Role Assignment
            </DialogTitle>
            <DialogDescription>
              Select users to assign <strong>{editDialog.role?.name}</strong> role
            </DialogDescription>
          </DialogHeader>
          <div className="relative mb-2">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search users..."
              value={roleUserSearch}
              onChange={(e) => setRoleUserSearch(e.target.value)}
              className="pl-9 h-9 rounded-lg text-sm"
            />
          </div>
          <div className="space-y-2 max-h-72 overflow-auto py-1">
            {users
              .filter((u) => u.is_active !== false)
              .filter((u) => {
                if (!roleUserSearch) return true;
                const q = roleUserSearch.toLowerCase();
                return u.name?.toLowerCase().includes(q) || u.email?.toLowerCase().includes(q);
              })
              .map((user) => {
                const uid = user.id || user._id;
                const isSelected = selectedUserIds.has(uid);
                return (
                  <div
                    key={uid}
                    className={`flex items-center gap-3 p-2.5 border rounded-lg cursor-pointer transition-all ${
                      isSelected ? "bg-blue-50/80 border-blue-300 shadow-sm" : "hover:bg-slate-50 hover:border-slate-300"
                    }`}
                    onClick={() => handleToggleUser(uid)}
                  >
                    <div className={`w-4 h-4 border rounded flex items-center justify-center ${
                      isSelected ? "bg-blue-500 border-blue-500" : "border-slate-300"
                    }`}>
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-white" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{user.name}</p>
                      <p className="text-xs text-slate-500 truncate">{user.email}</p>
                    </div>
                  </div>
                );
              })}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialog({ open: false, role: null })} disabled={saving}>Cancel</Button>
            <Button onClick={handleSaveRoleAssignment} disabled={saving}>
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
