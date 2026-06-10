import { Ban, Key, Search, UserPlus, Users } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { dedupeAuthorityCodes } from "@/contexts/admin/hooks/authorityNormalization";

const DEPT_SCOPED_ROLES = new Set(["HOD", "DEPT_DATA_ENTRY"]);

const ROLE_COLORS = {
  SYSTEM_ADMIN: "bg-red-100 text-red-700",
  DEPT_DATA_ENTRY: "bg-blue-100 text-blue-700",
  GLOBAL_DATA_ENTRY: "bg-cyan-100 text-cyan-700",
  VERIFIER: "bg-amber-100 text-amber-700",
  APPROVER: "bg-purple-100 text-purple-700",
  HOD: "bg-green-100 text-green-700",
  AUDITOR: "bg-green-100 text-green-700",
};

export default function UserManagementTab({
  handleOpenCreateUserDialog,
  userSearch,
  setUserSearch,
  filteredUsers,
  handleResetPassword,
  handleDeactivateUser,
}) {
  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base"><Users className="w-4 h-4" />User Management</CardTitle>
            <CardDescription>Create users, assign roles. Soft disable only.</CardDescription>
          </div>
          <Button size="sm" className="gap-1.5" data-testid="create-user-btn" onClick={handleOpenCreateUserDialog}><UserPlus className="w-3.5 h-3.5" />Create User</Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input placeholder="Search users by name or email..." value={userSearch} onChange={(e) => setUserSearch(e.target.value)} className="pl-10 rounded-lg" />
          </div>
        </div>
        <div className="rounded-lg border overflow-hidden">
          <Table>
            <TableHeader><TableRow className="bg-slate-50/80">
              <TableHead>User</TableHead><TableHead>Role</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {filteredUsers.map((user) => (
                <TableRow key={user.id} className="hover:bg-slate-50/50">
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-medium text-slate-600">
                        {user.name?.split(' ').map(n => n[0]).join('').slice(0,2).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-sm">{user.name}</p>
                        <p className="text-xs text-slate-500">{user.email}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {dedupeAuthorityCodes(user.authorities || []).map((auth) => {
                        const label = DEPT_SCOPED_ROLES.has(auth) && user.department_code
                          ? `${auth} (${user.department_code})`
                          : auth;
                        return (
                          <Badge key={auth} className={ROLE_COLORS[auth] || "bg-slate-100 text-slate-700"}>
                            {label}
                          </Badge>
                        );
                      })}
                      {(!user.authorities || user.authorities.length === 0) && (
                        <Badge variant="outline">No Role</Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={`${user.is_active ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-600 border-red-200"} border`}>
                      <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${user.is_active ? 'bg-emerald-500' : 'bg-red-500'}`} />
                      {user.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1.5">
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => handleResetPassword(user)} title="Reset Password"><Key className="w-3.5 h-3.5" /></Button>
                      {user.is_active && <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => handleDeactivateUser(user)} title="Deactivate"><Ban className="w-3.5 h-3.5" /></Button>}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
