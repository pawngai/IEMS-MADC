/**
 * GlobalPortalDashboard  Central operations landing page for back-office roles.
 *
 * Mirrors the employee portal structure: stat cards, quick actions, pending items,
 * and recent activity  but scoped to the user's officer/workflow authority
 * (Verifier, Section Officer, Approving Authority, DDO, HOD, Auditor, etc.).
 */
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/app/layout/Layout";
import { OPS } from "@/shared/lib/routes";
import { filterQueuedProfilesByStage, getProfileQueueStagesForAuthority } from "@/shared/lib/profileWorkflowQueue";
import { useAuth } from "@/contexts/identity_access";
import { usePermissions } from "@/contexts/identity_access";
import { listProfilesByStatus } from "@/contexts/applications/model/globalPortalGateway";
import { leaveAPI } from "@/contexts/leave";
import { Permissions } from "@/platform/permissions";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { CardSkeleton, PageHeaderSkeleton, StatGridSkeleton, TableSkeleton } from "@/shared/ui/skeletons";
import {
  BookOpen,
  Calendar,
  CheckCircle2,
  ClipboardList,
  Clock,
  Eye,
  FileText,
  GitBranch,
  RefreshCw,
  Users,
} from "lucide-react";
import { toast } from "sonner";

/* ----------- Helpers ----------- */

const formatDateTime = (value) => {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
};

const statusText = (status) => {
  if (!status) return "Unknown";
  return status.charAt(0) + status.slice(1).toLowerCase();
};

const pickTs = (o) =>
  o?.updated_at || o?.updatedAt || o?.timestamp || o?.created_at || o?.createdAt || null;

const ageHours = (ts) => {
  if (!ts) return null;
  try {
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return null;
    return (Date.now() - d.getTime()) / 3_600_000;
  } catch {
    return null;
  }
};

const SLA_COLORS = {
  green: "bg-green-100 text-green-700",
  yellow: "bg-amber-100 text-amber-700",
  red: "bg-red-100 text-red-700",
};

const slaLabel = (hours) => {
  if (hours == null) return { color: "green", text: "N/A" };
  if (hours < 24) return { color: "green", text: "< 24 h" };
  if (hours < 72) return { color: "yellow", text: `${Math.floor(hours)}h` };
  return { color: "red", text: `${Math.floor(hours / 24)}d overdue` };
};

const STATUS_STYLES = {
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  RECOMMENDED: "bg-indigo-100 text-indigo-700",
  SANCTIONED: "bg-green-100 text-green-700",
};

/* ----------- Sub-components ----------- */

const StatCard = ({ icon: Icon, label, value, hint, color = "bg-blue-100 text-blue-700" }) => (
  <Card className="layer-2-card">
    <CardContent className="pt-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
          <p className="text-xs text-slate-500 mt-1">{hint}</p>
        </div>
        <div className={`w-11 h-11 rounded-full ${color} flex items-center justify-center`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </CardContent>
  </Card>
);

const ActionButton = ({ icon: Icon, label, onClick, badge }) => (
  <Button variant="outline" className="justify-start gap-2 h-11 relative" onClick={onClick}>
    <Icon className="w-4 h-4" />
    {label}
    {badge != null && badge > 0 && (
      <Badge className="ml-auto bg-blue-600 text-white text-[10px] px-1.5 py-0">{badge}</Badge>
    )}
  </Button>
);

/* ----------- Main Component ----------- */

const GlobalPortalDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { can, canAny, canAccessModule, getPrimaryAuthority, getAuthorityDisplayName } =
    usePermissions();
  const [loading, setLoading] = useState(true);
  const [profiles, setProfiles] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const authority = getPrimaryAuthority();
  const authorityLabel = getAuthorityDisplayName(authority);

  // Determine which profile stages to load based on authority
  const profileStages = useMemo(() => getProfileQueueStagesForAuthority(authority), [authority]);

  const canLeaveWorkflow =
    (can(Permissions.LEAVE_RECOMMEND) || can(Permissions.LEAVE_SANCTION)) &&
    canAccessModule("leave");

  const canViewAudit =
    can(Permissions.AUDIT_READ_ALL) && canAccessModule("audit");

  const canEmployeeDir = canAny([
    Permissions.PROFILE_READ_ALL,
    Permissions.PROFILE_CREATE,
    Permissions.PROFILE_UPDATE_ALL,
    Permissions.SERVICE_BOOK_READ_ALL,
    Permissions.SERVICE_BOOK_ENTRY_CREATE,
  ]);

  useEffect(() => {
    let active = true;

    const load = async () => {
      setLoading(true);
      try {
        const tasks = [];

        // Profiles for this authority
        for (const stage of profileStages) {
          tasks.push(
            listProfilesByStatus(stage, { page_size: 200 })
              .then((profiles) =>
                filterQueuedProfilesByStage(profiles, stage).map((p) => ({
                  ...p,
                  _stage: stage,
                  _type: "profile",
                }))
              )
              .catch(() => [])
          );
        }

        // Leave requests
        if (canLeaveWorkflow) {
          if (can(Permissions.LEAVE_RECOMMEND)) {
            tasks.push(
              leaveAPI
                .list({ status: "SUBMITTED" })
                .then((r) =>
                  (Array.isArray(r.data) ? r.data : []).map((l) => ({
                    ...l,
                    _stage: "SUBMITTED",
                    _type: "leave",
                  }))
                )
                .catch(() => [])
            );
          }
          if (can(Permissions.LEAVE_SANCTION)) {
            tasks.push(
              leaveAPI
                .list({ status: "RECOMMENDED" })
                .then((r) =>
                  (Array.isArray(r.data) ? r.data : []).map((l) => ({
                    ...l,
                    _stage: "RECOMMENDED",
                    _type: "leave",
                  }))
                )
                .catch(() => [])
            );
          }
        }

        const results = await Promise.all(tasks);
        if (!active) return;

        const allProfiles = [];
        const allLeaves = [];
        for (const batch of results) {
          for (const item of batch) {
            if (item._type === "profile") allProfiles.push(item);
            else if (item._type === "leave") allLeaves.push(item);
          }
        }
        setProfiles(allProfiles);
        setLeaves(allLeaves);
      } catch {
        if (active) toast.error("Failed to load dashboard data");
      } finally {
        if (active) setLoading(false);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, [profileStages, canLeaveWorkflow, can, refreshKey]);

  // Computed stats
  const profileCount = profiles.length;
  const leaveCount = leaves.length;
  const totalPending = profileCount + leaveCount;

  const overdueItems = useMemo(() => {
    const all = [
      ...profiles.map((p) => ({ ts: pickTs(p), label: p.full_name || p.employee_id })),
      ...leaves.map((l) => ({ ts: pickTs(l), label: l.leave_type_code || "Leave" })),
    ];
    return all.filter((i) => {
      const hours = ageHours(i.ts);
      return hours != null && hours > 72;
    }).length;
  }, [profiles, leaves]);

  // Recent items (combined, sorted by timestamp desc)
  const recentItems = useMemo(() => {
    const combined = [
      ...profiles.map((p) => ({
        id: `profile:${p.employee_id}`,
        title: p.full_name || p.employee_code || "Employee Profile",
        note: `Profile ${statusText(p.workflow_status || p._stage)}`,
        type: "profile",
        status: p.workflow_status || p._stage,
        when: pickTs(p),
      })),
      ...leaves.map((l) => ({
        id: `leave:${l.id}`,
        title: l.leave_type_code || "Leave",
        note: `${l.from_date || "-"} \u2192 ${l.to_date || "-"}`,
        type: "leave",
        status: l.status || l._stage,
        when: pickTs(l),
      })),
    ];
    return combined
      .filter((i) => i.when)
      .sort((a, b) => new Date(b.when) - new Date(a.when))
      .slice(0, 8);
  }, [profiles, leaves]);

  if (loading) {
    return (
      <Layout>
        <div className="max-w-6xl mx-auto space-y-6" data-testid="global-portal-dashboard-loading">
          <PageHeaderSkeleton />
          <StatGridSkeleton count={4} />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <CardSkeleton lines={4} />
            <CardSkeleton lines={4} />
          </div>
          <TableSkeleton rows={5} columns={4} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div
        className="max-w-6xl mx-auto space-y-6 animate-fade-in"
        data-testid="global-portal-dashboard"
      >
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">
              Central Operations Portal
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Central Operations Dashboard</h2>
            <p className="text-sm text-slate-500 mt-1">
              Welcome back, {user?.name || "Officer"}. Here's your work overview.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge className="bg-blue-100 text-blue-700">{authorityLabel}</Badge>
            {user?.department_code && (
              <Badge variant="outline">Dept: {user.department_code}</Badge>
            )}
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => setRefreshKey((k) => k + 1)}
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={FileText}
            label="Pending Profiles"
            value={String(profileCount)}
            hint={profileStages.join(", ") || "No profile tasks"}
            color="bg-blue-100 text-blue-700"
          />
          <StatCard
            icon={Calendar}
            label="Pending Leave"
            value={String(leaveCount)}
            hint={canLeaveWorkflow ? "Awaiting your action" : "Leave module not active"}
            color="bg-emerald-100 text-emerald-700"
          />
          <StatCard
            icon={ClipboardList}
            label="Total Work Items"
            value={String(totalPending)}
            hint="Profiles + Leave requests"
            color="bg-purple-100 text-purple-700"
          />
          <StatCard
            icon={Clock}
            label="Overdue (>72h)"
            value={String(overdueItems)}
            hint={overdueItems > 0 ? "Action needed" : "All within SLA"}
            color={overdueItems > 0 ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}
          />
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
            <CardDescription>Jump to your most-used features.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <ActionButton
              icon={GitBranch}
              label="Work Queue"
              onClick={() => navigate(OPS.WORK_QUEUE)}
              badge={totalPending}
            />
            <ActionButton
              icon={Users}
              label="Employee Directory"
              onClick={() => navigate(OPS.EMPLOYEES)}
            />
            {canLeaveWorkflow && (
              <ActionButton
                icon={Calendar}
                label="Leave Management"
                onClick={() => navigate(OPS.LEAVE)}
                badge={leaveCount}
              />
            )}
            {canViewAudit && (
              <ActionButton
                icon={Eye}
                label="Audit Logs"
                onClick={() => navigate(OPS.AUDIT)}
              />
            )}
            {canAny([Permissions.SERVICE_BOOK_READ_ALL]) && (
              <ActionButton
                icon={BookOpen}
                label="Service Book"
                onClick={() => navigate(OPS.EMPLOYEES)}
              />
            )}
          </CardContent>
        </Card>

        {/* Pending Work + Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Pending Items */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ClipboardList className="w-5 h-5" /> Pending Work
              </CardTitle>
              <CardDescription>Items awaiting your action.</CardDescription>
            </CardHeader>
            <CardContent>
              {totalPending === 0 ? (
                <div className="text-sm text-slate-500 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" /> All caught up  no pending
                  items.
                </div>
              ) : (
                <ul className="space-y-2 text-sm text-slate-700">
                  {profileCount > 0 && (
                    <li className="flex items-start gap-2">
                      <span className="mt-1 w-1.5 h-1.5 rounded-full bg-blue-600 flex-shrink-0" />
                      <span>
                        <strong>{profileCount}</strong> profile{profileCount !== 1 ? "s" : ""}{" "}
                        awaiting {profileStages.join(" / ")} action.{" "}
                        <button
                          className="text-blue-600 hover:underline font-medium"
                          onClick={() => navigate(OPS.WORK_QUEUE)}
                        >
                          Open queue ?
                        </button>
                      </span>
                    </li>
                  )}
                  {leaveCount > 0 && (
                    <li className="flex items-start gap-2">
                      <span className="mt-1 w-1.5 h-1.5 rounded-full bg-emerald-600 flex-shrink-0" />
                      <span>
                        <strong>{leaveCount}</strong> leave request{leaveCount !== 1 ? "s" : ""}{" "}
                        pending.{" "}
                        <button
                          className="text-blue-600 hover:underline font-medium"
                          onClick={() => navigate(OPS.LEAVE)}
                        >
                          Review ?
                        </button>
                      </span>
                    </li>
                  )}
                  {overdueItems > 0 && (
                    <li className="flex items-start gap-2">
                      <span className="mt-1 w-1.5 h-1.5 rounded-full bg-red-600 flex-shrink-0" />
                      <span className="text-red-700">
                        <strong>{overdueItems}</strong> item{overdueItems !== 1 ? "s" : ""} overdue
                        (&gt; 72 hours).
                      </span>
                    </li>
                  )}
                </ul>
              )}
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Clock className="w-5 h-5" /> Recent Items
              </CardTitle>
              <CardDescription>Latest work items across your queue.</CardDescription>
            </CardHeader>
            <CardContent>
              {recentItems.length === 0 ? (
                <div className="text-sm text-slate-500">No recent items found.</div>
              ) : (
                <div className="space-y-3">
                  {recentItems.map((item) => {
                    const age = ageHours(item.when);
                    const sla = slaLabel(age);
                    return (
                      <div key={item.id} className="rounded-lg border p-3">
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-medium text-sm text-slate-900 truncate">
                            {item.title}
                          </p>
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            <Badge
                              className={
                                STATUS_STYLES[item.status] || "bg-slate-100 text-slate-700"
                              }
                            >
                              {statusText(item.status)}
                            </Badge>
                            <Badge className={`text-[10px] ${SLA_COLORS[sla.color]}`}>
                              {sla.text}
                            </Badge>
                          </div>
                        </div>
                        <p className="text-xs text-slate-600 mt-1">{item.note}</p>
                        <p className="text-[11px] text-slate-400 mt-1">
                          {formatDateTime(item.when)}
                        </p>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default GlobalPortalDashboard;

