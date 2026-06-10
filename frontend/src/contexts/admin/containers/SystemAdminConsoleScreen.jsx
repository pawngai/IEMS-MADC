/**
 * SystemAdminConsole - MADC-HRMS Policy & Governance Console
 * 
 * ROLE: SYSTEM_ADMIN
 * SCOPE: SYSTEM_WIDE
 * NATURE: POLICY_AND_GOVERNANCE_ONLY
 * 
 * INVARIANT: System Administrator configures policy, governs access,
 * and maintains platform integrity but NEVER alters employee service
 * history or statutory decisions.
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import { useLocation } from "react-router-dom";
import Layout from "@/app/layout/Layout";
import AdminActionDialogs from "@/contexts/admin/components/AdminActionDialogs";
import AdminDetailDialogs from "@/contexts/admin/components/AdminDetailDialogs";
import UserManagementTab from "@/contexts/admin/components/UserManagementTab";
import RoleManagementTab from "@/contexts/admin/components/RoleManagementTab";
import DepartmentRolesTab from "@/contexts/admin/components/DepartmentRolesTab";
import PolicyMastersSection from "@/contexts/admin/sections/PolicyMastersSection";
import useAdminIdentityDataFetchers from "@/contexts/admin/hooks/useAdminIdentityDataFetchers";
import useAdminUserActions from "@/contexts/admin/hooks/useAdminUserActions";
import useAdminConsolePermissions from "@/contexts/admin/hooks/useAdminConsolePermissions";
import useAdminViewHelpers from "@/contexts/admin/hooks/useAdminViewHelpers";
import useAdminConsoleTabs from "@/contexts/admin/hooks/useAdminConsoleTabs";
import { CardSkeleton, PageHeaderSkeleton, TableSkeleton } from "@/shared/ui/skeletons";
import { Button } from "@/shared/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";
import { toast } from "sonner";
import {
  Shield,
  Lock,
  RefreshCw,
} from "lucide-react";

const SystemAdminConsoleScreen = () => {
  const location = useLocation();
  const { isSystemAdmin } = useAdminConsolePermissions();
  const { tabs: consoleTabs, defaultTab } = useAdminConsoleTabs();
  const resolveRouteTab = useCallback((pathname) => {
    if (pathname === "/admin/masters") return "policy-masters";
    return null;
  }, []);
  const routeTab = resolveRouteTab(location.pathname);
  const [activeTab, setActiveTab] = useState(routeTab || defaultTab);
  const [loading, setLoading] = useState(true);

  const [users, setUsers] = useState([]);
  const [userSearch, setUserSearch] = useState("");
  const [availableAuthorities, setAvailableAuthorities] = useState([]);
  const [createUserDialog, setCreateUserDialog] = useState(false);
  const [newUser, setNewUser] = useState({ email: "", name: "", password: "", authorities: [], employee_id: "" });
  const [roleChangeHistory, setRoleChangeHistory] = useState([]);
  const [roleChangeStats, setRoleChangeStats] = useState({ total_changes: 0, changes_last_7_days: 0 });
  const [editUserDialog, setEditUserDialog] = useState({ open: false, user: null });
  const [editUserRoles, setEditUserRoles] = useState([]);
  const [authorityHolders, setAuthorityHolders] = useState({});

  const [employees, setEmployees] = useState([]);
  const [employeeFilters] = useState({ department: "", employment_type: "", workflow_status: "" });
  const [employeePagination, setEmployeePagination] = useState({ offset: 0, limit: 50, total: 0 });

  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null, data: null });
  const [reasonDialog, setReasonDialog] = useState({ open: false, action: null, data: null });
  const [actionReason, setActionReason] = useState("");
  const debouncedEmployeeSearch = "";

  const {
    fetchDashboardData,
    fetchEmployeeData,
    fetchRoleChangeData,
  } = useAdminIdentityDataFetchers({
    setUsers,
    setAvailableAuthorities,
    setAuthorityHolders,
    employeePagination,
    debouncedEmployeeSearch,
    employeeFilters,
    setEmployees,
    setEmployeePagination,
    setRoleChangeHistory,
    setRoleChangeStats,
  });

  useEffect(() => {
    setLoading(true);
    const initialLoad = isSystemAdmin
      ? Promise.all([fetchDashboardData(), fetchRoleChangeData()])
      : Promise.resolve();
    initialLoad.finally(() => setLoading(false));
  }, [fetchDashboardData, fetchRoleChangeData, isSystemAdmin]);

  useEffect(() => {
    if (routeTab) {
      setActiveTab(routeTab);
      return;
    }
    if (!activeTab && defaultTab) {
      setActiveTab(defaultTab);
    }
  }, [activeTab, defaultTab, routeTab]);

  useEffect(() => {
    if (activeTab === "role-mgmt") {
      fetchRoleChangeData();
    }
  }, [activeTab, fetchRoleChangeData]);

  const {
    handleCreateUser,
    handleDeactivateUser,
    handleResetPassword,
    handleEditUserRoles,
    handleSaveUserRoles,
    confirmAction,
    confirmReasonAction,
  } = useAdminUserActions({
    newUser,
    setCreateUserDialog,
    setNewUser,
    setActionReason,
    setReasonDialog,
    setConfirmDialog,
    setEditUserRoles,
    setEditUserDialog,
    editUserDialog,
    editUserRoles,
    confirmDialog,
    reasonDialog,
    actionReason,
    fetchDashboardData,
    fetchRoleChangeData,
  });

  const handleOpenCreateUserDialog = useCallback(() => {
    fetchEmployeeData();
    setCreateUserDialog(true);
  }, [fetchEmployeeData]);

  const {
    getRoleBadge,
    getRuleBadge,
  } = useAdminViewHelpers({
    availableAuthorities,
  });

  const filteredUsers = users.filter(u =>
    u.email?.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.name?.toLowerCase().includes(userSearch.toLowerCase())
  );

  const consoleTitle = "System Administration Console";
  const consoleSubtitle = "MADC-HRMS Policy & Governance Console";

  const authorityOptions = useMemo(() => {
    const base = (availableAuthorities || [])
      .map((auth) => {
        const code = typeof auth === "string" ? auth : auth.code;
        const name = typeof auth === "string" ? auth : auth.name || auth.code;
        return { value: code, label: name };
      });
    return [{ value: "none", label: "No Role" }, ...base];
  }, [availableAuthorities]);

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6" data-testid="system-admin-console-loading">
          <PageHeaderSkeleton />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <CardSkeleton lines={3} />
            <CardSkeleton lines={3} />
          </div>
          <TableSkeleton rows={6} columns={6} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="system-admin-console">
        {/* HEADER */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-red-600 to-red-700 rounded-xl shadow-lg shadow-red-200">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{consoleTitle}</h2>
              <p className="text-slate-500 text-sm flex items-center gap-2">
                {consoleSubtitle}
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-50 text-red-600 text-xs font-medium rounded-full border border-red-100">
                  <Lock className="w-3 h-3" />Read-only for transactions
                </span>
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 border-slate-200 hover:bg-slate-50"
            onClick={() => {
              const refreshAction = Promise.all([fetchDashboardData(), fetchRoleChangeData()]);
              refreshAction.finally(() => toast.success("Refreshed"));
            }}
          >
            <RefreshCw className="w-4 h-4" />Refresh
          </Button>
        </div>

        {/* TABS */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="w-full flex flex-wrap gap-1 h-auto p-1.5 bg-slate-100/80 rounded-xl border">
            {consoleTabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <TabsTrigger key={tab.id} value={tab.id} className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-slate-900 transition-all" data-testid={`tab-${tab.id}`}>
                  <Icon className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline font-medium">{tab.label}</span>
                </TabsTrigger>
              );
            })}
          </TabsList>

          <PolicyMastersSection
            activeTab={activeTab}
            getRuleBadge={getRuleBadge}
          />

          <TabsContent value="user-mgmt" className="space-y-6">
            <UserManagementTab
              handleOpenCreateUserDialog={handleOpenCreateUserDialog}
              userSearch={userSearch}
              setUserSearch={setUserSearch}
              filteredUsers={filteredUsers}
              handleResetPassword={handleResetPassword}
              handleDeactivateUser={handleDeactivateUser}
            />
          </TabsContent>

          <TabsContent value="role-mgmt" className="space-y-6">
            <RoleManagementTab
              availableAuthorities={availableAuthorities}
              users={users}
              roleChangeStats={roleChangeStats}
              roleChangeHistory={roleChangeHistory}
              onRefresh={() => Promise.all([fetchDashboardData(), fetchRoleChangeData()])}
            />
          </TabsContent>

          <TabsContent value="dept-roles" className="space-y-6">
            <DepartmentRolesTab />
          </TabsContent>
        </Tabs>

        {/* ==================== DIALOGS ==================== */}
        <AdminActionDialogs
          createUserDialog={createUserDialog}
          setCreateUserDialog={setCreateUserDialog}
          newUser={newUser}
          setNewUser={setNewUser}
          authorityOptions={authorityOptions}
          employees={employees}
          handleCreateUser={handleCreateUser}
          confirmDialog={confirmDialog}
          setConfirmDialog={setConfirmDialog}
          confirmAction={confirmAction}
          reasonDialog={reasonDialog}
          setReasonDialog={setReasonDialog}
          actionReason={actionReason}
          setActionReason={setActionReason}
          confirmReasonAction={confirmReasonAction}
        />

        <AdminDetailDialogs
          editUserDialog={editUserDialog}
          setEditUserDialog={setEditUserDialog}
          availableAuthorities={availableAuthorities}
          authorityHolders={authorityHolders}
          editUserRoles={editUserRoles}
          setEditUserRoles={setEditUserRoles}
          handleSaveUserRoles={handleSaveUserRoles}
        />
      </div>
    </Layout>
  );
};

export default SystemAdminConsoleScreen;

