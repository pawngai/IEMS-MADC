/**
 * HomePage — Unified landing page that composes role-specific summary sections.
 *
 * Each section renders only if the user has the relevant permissions.
 * Clicking any action card navigates to the existing detailed page.
 *
 * All API calls are batched in a single useEffect to avoid waterfall requests.
 */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/app/layout/Layout";
import { useAuth } from "@/contexts/identity";
import { canEnterEssPortal } from "@/app/layout/Layout";
import { Permissions } from "@/platform/permissions";
import { ESS, DEPT, OPS, MAIN, ADMIN } from "@/shared/lib/routes";
import { filterQueuedProfilesByStage, getProfileQueueStagesForAuthority } from "@/shared/lib/profileWorkflowQueue";
import { fetchMyProfile } from "@/contexts/ess/model/essHomeGateway";
import { canAccessEssDocuments } from "@/contexts/ess/services/essDomainService";
import { fetchMyLeaves, fetchPendingLeaveActions } from "@/contexts/leave/model/leaveHomeGateway";
import { fetchDepartmentDashboard } from "@/contexts/department/model/departmentHomeGateway";
import { listProfilesByStatus } from "@/contexts/applications/model/globalPortalGateway";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { CardSkeleton, PageHeaderSkeleton, StatGridSkeleton } from "@/shared/ui/skeletons";
import {
  Calendar,
  ClipboardList,
  Edit3,
  Eye,
  FileText,
  FolderOpen,
  GitBranch,
  Shield,
  Users,
  User,
  Bell,
  AlertTriangle,
} from "lucide-react";

/* ── Shared sub-components ─────────────────────────────────────────── */

const StatCard = ({ icon: Icon, label, value, hint, color = "bg-blue-100 text-blue-700" }) => (
  <Card className="border-0 shadow-sm">
    <CardContent className="p-4 flex items-start gap-3">
      <div className={`p-2.5 rounded-lg ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-sm font-medium text-slate-700">{label}</p>
        {hint && <p className="text-xs text-slate-500 mt-0.5">{hint}</p>}
      </div>
    </CardContent>
  </Card>
);

const ActionButton = ({ icon: Icon, label, onClick, badge }) => (
  <Button variant="outline" className="h-auto py-3 px-4 justify-start gap-3 relative" onClick={onClick}>
    <Icon className="w-5 h-5 text-slate-600" />
    <span className="text-sm font-medium">{label}</span>
    {badge > 0 && (
      <Badge className="ml-auto bg-blue-600 text-white text-[10px] px-1.5 py-0">{badge}</Badge>
    )}
  </Button>
);

/* ── Section: My Work (ESS) ────────────────────────────────────────── */

const MyWorkSection = ({ profile, leaveCount, showDocuments }) => {
  const navigate = useNavigate();
  const status = profile?.workflow_status || "DRAFT";
  const completion = profile?.employee_section_completed ? "Complete" : "Incomplete";

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2"><User className="w-5 h-5" /> My Work</h3>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <StatCard icon={FileText} label="Profile Status" value={status} hint={`Employee section: ${completion}`} />
        <StatCard icon={Calendar} label="Active Leave" value={String(leaveCount)} hint="Pending requests" color="bg-green-100 text-green-700" />
        <StatCard icon={Bell} label="Notifications" value="-" hint="Check notifications" color="bg-amber-100 text-amber-700" />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        <ActionButton icon={FileText} label="My Profile" onClick={() => navigate(ESS.PROFILE)} />
        {showDocuments && <ActionButton icon={FolderOpen} label="Documents" onClick={() => navigate(ESS.DOCUMENTS)} />}
        <ActionButton icon={Calendar} label="Leave" onClick={() => navigate(ESS.LEAVE)} />
        <ActionButton icon={Bell} label="Notifications" onClick={() => navigate(ESS.NOTIFICATIONS)} />
        <ActionButton icon={Edit3} label="Change Requests" onClick={() => navigate(ESS.CHANGE_REQUESTS)} />
      </div>
    </div>
  );
};

/* ── Section: Department ───────────────────────────────────────────── */

const DepartmentSection = ({ summary }) => {
  const navigate = useNavigate();

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2"><Users className="w-5 h-5" /> Department</h3>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <StatCard icon={Users} label="Total Employees" value={String(summary.totalEmployees)} />
        <StatCard icon={AlertTriangle} label="Pending Work" value={String(summary.pendingWorkItems)} color="bg-amber-100 text-amber-700" />
        <StatCard icon={ClipboardList} label="Leave Requests" value={String(summary.pendingLeaveActions)} color="bg-green-100 text-green-700" />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <ActionButton icon={Users} label="Directory" onClick={() => navigate(DEPT.DIRECTORY)} />
        <ActionButton icon={AlertTriangle} label="Pending Work" badge={summary.pendingWorkItems} onClick={() => navigate(DEPT.PENDING_WORK)} />
        <ActionButton icon={ClipboardList} label="Leave" badge={summary.pendingLeaveActions} onClick={() => navigate(DEPT.LEAVE)} />
      </div>
    </div>
  );
};

/* ── Section: Operations ───────────────────────────────────────────── */

const OperationsSection = ({ profileCount, leaveCount }) => {
  const navigate = useNavigate();
  const { canAny } = useAuth();

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2"><GitBranch className="w-5 h-5" /> Operations</h3>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <StatCard icon={GitBranch} label="Work Queue" value={String(profileCount + leaveCount)} hint="Total pending items" />
        <StatCard icon={Users} label="Pending Profiles" value={String(profileCount)} color="bg-purple-100 text-purple-700" />
        <StatCard icon={Calendar} label="Leave Queue" value={String(leaveCount)} color="bg-green-100 text-green-700" />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <ActionButton icon={GitBranch} label="Work Queue" badge={profileCount + leaveCount} onClick={() => navigate(OPS.WORK_QUEUE)} />
        <ActionButton icon={Users} label="Directory" onClick={() => navigate(OPS.EMPLOYEES)} />
        <ActionButton icon={Calendar} label="Leave" badge={leaveCount} onClick={() => navigate(OPS.LEAVE)} />
        {canAny([Permissions.AUDIT_READ_ALL]) && (
          <ActionButton icon={Eye} label="Audit Logs" onClick={() => navigate(OPS.AUDIT)} />
        )}
      </div>
    </div>
  );
};

/* ── Section: Administration ───────────────────────────────────────── */

const AdminSection = () => {
  const navigate = useNavigate();
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2"><Shield className="w-5 h-5" /> Administration</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <ActionButton icon={Shield} label="System Admin" onClick={() => navigate(ADMIN.HOME)} />
        <ActionButton icon={Users} label="Employee Directory" onClick={() => navigate(MAIN.EMPLOYEES)} />
        <ActionButton icon={Eye} label="Audit Logs" onClick={() => navigate(MAIN.AUDITOR)} />
      </div>
    </div>
  );
};

const HomePageSkeleton = () => (
  <div className="space-y-6" data-testid="home-page-loading">
    <PageHeaderSkeleton />
    <StatGridSkeleton count={3} />
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <CardSkeleton lines={4} />
      <CardSkeleton lines={4} />
    </div>
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <CardSkeleton lines={4} />
      <CardSkeleton lines={4} />
    </div>
  </div>
);

/* ── Main HomePage ─────────────────────────────────────────────────── */

const HomePage = () => {
  const { user, can, canAny, canAccessEssPortal, getPrimaryAuthority } = useAuth();
  const authorities = Array.isArray(user?.authorities) ? user.authorities : [];
  const primaryAuth = getPrimaryAuthority();
  const isSystemAdmin = primaryAuth === "SYSTEM_ADMIN";

  const hasEssPermissions = canAny([
    Permissions.DOCUMENT_READ_OWN,
    Permissions.PROFILE_READ_OWN, Permissions.SERVICE_BOOK_READ_OWN,
    Permissions.LEAVE_APPLY_OWN, Permissions.LEAVE_READ_OWN,
    Permissions.PROFILE_UPDATE_OWN_LIMITED, Permissions.PROFILE_UPDATE_ALL,
  ]);
  const showEss = canEnterEssPortal({
    authorities, employeeId: user?.employee_id,
    canAccessEssPortal: canAccessEssPortal(), hasEssPermissions,
  });
  const showEssDocuments = canAccessEssDocuments({ user, can });
  const showDept =
    authorities.some((a) => ["DEPT_DATA_ENTRY", "HOD"].includes(a)) &&
    can(Permissions.PROFILE_READ_ALL);
  const showOps = authorities.some((a) => a && a !== "EMPLOYEE") && !isSystemAdmin;
  const showAdmin = isSystemAdmin;

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    essProfile: null, essLeaveCount: 0,
    deptSummary: { totalEmployees: 0, pendingWorkItems: 0, pendingLeaveActions: 0 },
    opsProfileCount: 0, opsLeaveCount: 0,
  });

  useEffect(() => {
    let active = true;
    const load = async () => {
      const calls = [];

      if (showEss) {
        calls.push(
          fetchMyProfile().catch(() => ({ data: null })),
          fetchMyLeaves().catch(() => ({ data: [] })),
        );
      } else {
        calls.push(null, null);
      }

      if (showDept) {
        calls.push(fetchDepartmentDashboard().catch(() => ({ data: {} })));
      } else {
        calls.push(null);
      }

      if (showOps) {
        const opsProfileStages = getProfileQueueStagesForAuthority(primaryAuth);
        calls.push(
          Promise.all(
            opsProfileStages.map((stage) =>
              listProfilesByStatus(stage).then((profiles) => filterQueuedProfilesByStage(profiles, stage))
            )
          ).then((batches) => batches.flat()).catch(() => []),
          fetchPendingLeaveActions({
            canRecommend: can(Permissions.LEAVE_RECOMMEND),
            canSanction: can(Permissions.LEAVE_SANCTION),
          }).catch(() => ({ data: [] })),
        );
      } else {
        calls.push(null, null);
      }

      const [profileRes, leavesRes, deptRes, opsProfiles, opsLeaves] = await Promise.all(calls);
      if (!active) return;

      const leaves = leavesRes ? (Array.isArray(leavesRes.data) ? leavesRes.data : []) : [];
      setData({
        essProfile: profileRes?.data || null,
        essLeaveCount: leaves.filter((l) => l.status === "SUBMITTED" || l.status === "RECOMMENDED").length,
        deptSummary: deptRes?.data
          ? {
              totalEmployees: deptRes.data.total_employees ?? deptRes.data.totalEmployees ?? 0,
              pendingWorkItems: deptRes.data.pending_work_items ?? deptRes.data.pendingWorkItems ?? (Array.isArray(deptRes.data.workflow_breakdown) ? deptRes.data.workflow_breakdown.filter(b => b.status !== 'LOCKED').reduce((sum, b) => sum + (b.count || 0), 0) : 0),
              pendingLeaveActions: deptRes.data.pending_leave_actions ?? deptRes.data.pendingLeaveActions ?? 0,
            }
          : { totalEmployees: 0, pendingWorkItems: 0, pendingLeaveActions: 0 },
        opsProfileCount: Array.isArray(opsProfiles) ? opsProfiles.length : 0,
        opsLeaveCount: Array.isArray(opsLeaves?.data) ? opsLeaves.data.length : 0,
      });
      setLoading(false);
    };

    load();
    return () => { active = false; };
  }, [showEss, showDept, showOps, primaryAuth, can]);

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in" data-testid="home-page">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Welcome back, {user?.name || "User"}</h2>
          <p className="text-sm text-slate-500 mt-1">
            Here&rsquo;s an overview of your current work across all modules.
          </p>
        </div>

        {loading ? (
          <HomePageSkeleton />
        ) : (
          <>
            {showEss && <MyWorkSection profile={data.essProfile} leaveCount={data.essLeaveCount} showDocuments={showEssDocuments} />}
            {showDept && <DepartmentSection summary={data.deptSummary} />}
            {showOps && <OperationsSection profileCount={data.opsProfileCount} leaveCount={data.opsLeaveCount} />}
            {showAdmin && <AdminSection />}

            {!showEss && !showDept && !showOps && !showAdmin && (
              <Card>
                <CardHeader>
                  <CardTitle>No modules available</CardTitle>
                  <CardDescription>Your account does not have access to any modules yet.</CardDescription>
                </CardHeader>
              </Card>
            )}
          </>
        )}
      </div>
    </Layout>
  );
};

export default HomePage;
