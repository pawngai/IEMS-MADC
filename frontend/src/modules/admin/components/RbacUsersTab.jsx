import { Ban, History, Key, Search, Settings, UserPlus, Users } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";

export default function RbacUsersTab({
  handleOpenCreateUserDialog,
  userSearch,
  setUserSearch,
  filteredUsers,
  getRoleBadge,
  handleEditUserRoles,
  handleResetPassword,
  handleDeactivateUser,
  roleChangeStats,
  roleChangeHistory,
}) {
  return (
    <>
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
                    <TableCell>{getRoleBadge(user.authorities)}</TableCell>
                    <TableCell>
                      <Badge className={`${user.is_active ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-600 border-red-200"} border`}>
                        <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${user.is_active ? 'bg-emerald-500' : 'bg-red-500'}`} />
                        {user.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1.5">
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => handleEditUserRoles(user)} title="Edit Roles"><Settings className="w-3.5 h-3.5" /></Button>
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

      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-base"><History className="w-4 h-4 text-amber-600" />Role Change Audit Log</CardTitle>
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
                            {change.roles_added.map(r => (
                              <Badge key={r} className="bg-green-100 text-green-700 text-xs">{r}</Badge>
                            ))}
                          </div>
                        )}
                        {change.roles_removed?.length > 0 && (
                          <div className="flex items-center gap-1">
                            <span className="text-red-600 text-xs">-</span>
                            {change.roles_removed.map(r => (
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
    </>
  );
}
