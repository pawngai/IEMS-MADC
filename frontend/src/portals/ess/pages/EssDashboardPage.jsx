import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import AccessDeniedPage from "@/app/pages/system-admin/AccessDeniedPage";
import Layout from "@/app/layout/Layout";
import { ESS } from "@/shared/lib/routes";
import { useAuth } from "@/contexts/identity";
import { usePermissions } from "@/contexts/identity_access";
import { essAPI } from "@/contexts/ess";
import { leaveAPI } from "@/contexts/leave";
import {
  assertEssPortalSession,
  assertEssSelfScope,
  canAccessEssDocuments,
  canShowEssServiceBook,
} from "@/contexts/ess";
import { getMyProfileAuditTrail, normalizeEssProfile } from "@/contexts/ess";
import { Permissions } from "@/platform/permissions";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import {
  Bell,
  BookOpen,
  Calendar,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Clock,
  GitPullRequestDraft,
  History,
  ThumbsUp,
  TrendingUp,
  UserRound,
  AlertTriangle,
  FileText,
} from "lucide-react";
import { toast } from "sonner";
import { DashboardSkeleton } from "@/shared/ui/skeletons";

const PROFILE_STATUS_STYLES = {
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
};

const EVENT_ACTION_LABELS = {
  APPROVE: "Approved",
  APPROVED: "Approved",
  CANCEL: "Cancelled",
  CANCELLED: "Cancelled",
  LOCK: "Locked",
  LOCKED: "Locked",
  RECOMMEND: "Recommended",
  RECOMMENDED: "Recommended",
  REJECT: "Rejected",
  REJECTED: "Rejected",
  SANCTION: "Sanctioned",
  SANCTIONED: "Sanctioned",
  SUBMIT: "Submitted",
  SUBMITTED: "Submitted",
  UPDATE: "Updated",
  UPDATE_PROFILE: "Updated Profile",
  UPDATE_PROFILE_EXTENSION: "Updated Profile Extension",
  UPDATE_CONTACT: "Updated Contact",
  VERIFY: "Verified",
  VERIFIED: "Verified",
};

const pickLeaveTimestamp = (leave) =>
  leave?.sanctioned_at ||
  leave?.rejected_at ||
  leave?.cancelled_at ||
  leave?.recommended_at ||
  leave?.applied_at ||
  null;

const formatDateTime = (value) => {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
};

const formatEventActionLabel = (value, fallback = "Unknown") => {
  const normalized = String(value || "").trim();
  if (!normalized) return fallback;

  const lookupKey = normalized.toUpperCase().replace(/[\s-]+/g, "_");
  if (EVENT_ACTION_LABELS[lookupKey]) return EVENT_ACTION_LABELS[lookupKey];

  return normalized
    .replace(/[_-]+/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

const EssDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { can } = usePermissions();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [serviceBook, setServiceBook] = useState(null);
  const [leaveBalances, setLeaveBalances] = useState({});
  const [myLeaves, setMyLeaves] = useState([]);
  const [profileAudit, setProfileAudit] = useState([]);
  const [loadError, setLoadError] = useState(false);
  const [accessDenied, setAccessDenied] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const canEditProfile = can(Permissions.PROFILE_UPDATE_OWN_LIMITED) || can(Permissions.PROFILE_UPDATE_ALL);
  const canReadOwnDocuments = canAccessEssDocuments({ user, can });
  const canUseLeave = can(Permissions.LEAVE_APPLY_OWN) || can(Permissions.LEAVE_READ_OWN);
  const canReadOwnServiceBook = can(Permissions.SERVICE_BOOK_READ_OWN);

  useEffect(() => {
    let active = true;

    const load = async () => {
      setLoading(true);
      setAccessDenied(false);
      setLoadError(false);
      try {
        assertEssPortalSession({ user });
        const [profileRes, leavesRes, dashboardRes] = await Promise.all([
          essAPI.getMyProfile(),
          leaveAPI.listMy().catch(() => ({ data: [] })),
          essAPI.getDashboard().catch(() => ({ data: null })),
        ]);

        const nextProfile = normalizeEssProfile(profileRes.data || null);
        if (!nextProfile?.employee_id) {
          throw new Error("ESS dashboard requires a linked employee profile");
        }
        const targetEmployeeId = nextProfile?.employee_id || user?.employee_id || null;
        assertEssSelfScope({ user, targetEmployeeId });
        const nextLeaves = Array.isArray(leavesRes.data) ? leavesRes.data : [];

        let serviceBookEligible = false;
        if (nextProfile) {
          serviceBookEligible = canShowEssServiceBook({ profile: nextProfile, user });
        }

        let serviceBookRes = { data: null };
        if (serviceBookEligible && targetEmployeeId) {
          serviceBookRes = await essAPI.getMyServiceBook().catch((error) => {
            const detail = error?.response?.data?.detail;
            const detailError = detail?.error;
            const detailMessage = detail?.message;
            const notApplicable =
              error?.response?.status === 403 &&
              (detailError === "Service Book not applicable" ||
                (typeof detailMessage === "string" && detailMessage.toLowerCase().includes("service book")) ||
                (typeof detail === "string" && detail.toLowerCase().includes("service book")));

            if (notApplicable) {
              serviceBookEligible = false;
              return { data: null };
            }

            return { data: null };
          });
        }

        if (!active) return;
        setProfile(nextProfile);
        setDashboardStats(dashboardRes.data || null);
        setServiceBook(serviceBookRes.data || null);
        setMyLeaves(nextLeaves);

        const loads = [];
        if (user?.employee_id && canUseLeave) {
          loads.push(
            essAPI.getMyLeaveBalances().catch(() => ({ data: { balances: {} } }))
          );
        } else {
          loads.push(Promise.resolve({ data: { balances: {} } }));
        }

        if (nextProfile?.employee_id) {
          loads.push(
            getMyProfileAuditTrail(nextProfile.employee_id)
              .then((auditTrail) => ({ data: { audit_trail: auditTrail } }))
              .catch(() => ({ data: { audit_trail: [] } }))
          );
        } else {
          loads.push(Promise.resolve({ data: { audit_trail: [] } }));
        }

        const [balanceRes, auditRes] = await Promise.all(loads);
        if (!active) return;
        setLeaveBalances(balanceRes.data?.balances || {});
        setProfileAudit(auditRes.data?.audit_trail || []);
      } catch (error) {
        if (!active) return;
        const message = String(error?.message || "").toLowerCase();
        if (message.includes("linked employee account") || message.includes("self scope")) {
          setAccessDenied(true);
        } else {
          setLoadError(true);
          toast.error("Failed to load employee dashboard");
        }
      } finally {
        if (active) setLoading(false);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, [user, canUseLeave, canReadOwnServiceBook, reloadKey]);

  const serviceBookEntries = useMemo(() => {
    const entryCount = Number(dashboardStats?.service_book_entries);
    if (Number.isFinite(entryCount) && entryCount >= 0) return entryCount;
    return 0;
  }, [dashboardStats]);

  const serviceBookAvailableParts = useMemo(() => {
    if (Array.isArray(serviceBook?.available_parts)) return serviceBook.available_parts.length;
    return 0;
  }, [serviceBook]);

  const pendingLeaves = useMemo(
    () => myLeaves.filter((leave) => ["SUBMITTED", "RECOMMENDED"].includes(leave?.status)).length,
    [myLeaves]
  );

  const serviceBookEligible = useMemo(() => {
    try {
      if (!profile) return false;
      return canShowEssServiceBook({ profile, user });
    } catch {
      return false;
    }
  }, [profile, user, canReadOwnServiceBook]);

  const pendingActions = useMemo(() => {
    const actions = [];
    const profileStatus = profile?.workflow_status || "DRAFT";
    const profileIncomplete = profile && !profile?.employee_section_completed && ["DRAFT", "REJECTED"].includes(profileStatus);
    if (profileIncomplete && canEditProfile) {
      actions.push("Complete your profile section and submit it for review.");
    }
    if (pendingLeaves > 0) {
      actions.push(`Track ${pendingLeaves} pending leave request${pendingLeaves > 1 ? "s" : ""}.`);
    }
    if (serviceBookEligible && serviceBookEntries === 0 && serviceBook && !loading) {
      actions.push("Service Book exists but has no finalized entries yet.");
    }
    return actions;
  }, [profile, canEditProfile, pendingLeaves, serviceBookEntries, serviceBook, serviceBookEligible, loading]);

  const recentUpdates = useMemo(() => {
    const leaveEvents = (myLeaves || []).map((leave) => ({
      id: `leave:${leave.id}`,
      when: pickLeaveTimestamp(leave),
      title: `Leave ${formatEventActionLabel(leave.status)}`,
      note: `${leave.leave_type_code || "Leave"}  ${leave.from_date || "-"} \u2192 ${leave.to_date || "-"}`,
      type: "leave",
    }));

    const profileEvents = (profileAudit || []).map((log, index) => ({
      id: `profile:${log.id || index}`,
      when: log.timestamp,
      title: `Profile ${formatEventActionLabel(log.action, "Updated")}`,
      note: log.remarks || log.reason || "Profile activity recorded",
      type: "profile",
    }));

    return [...leaveEvents, ...profileEvents]
      .filter((event) => event.when)
      .sort((a, b) => new Date(b.when) - new Date(a.when))
      .slice(0, 8);
  }, [myLeaves, profileAudit]);

  if (loading) {
    return (
      <Layout>
        <div className="max-w-6xl mx-auto">
          <DashboardSkeleton />
        </div>
      </Layout>
    );
  }

  if (accessDenied) {
    return (
      <AccessDeniedPage
        title="ESS access denied"
        description="Employee Self-Service is available only to signed-in users linked to their own employee profile."
      />
    );
  }

  if (loadError) {
    return (
      <Layout>
        <div className="max-w-3xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                Dashboard unavailable
              </CardTitle>
              <CardDescription>
                Your employee dashboard could not be loaded right now. Retry, or contact support if the problem persists.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setReloadKey((value) => value + 1)}>Retry</Button>
            </CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  const workflowStatus = profile?.workflow_status || "DRAFT";
  const statusClass = PROFILE_STATUS_STYLES[workflowStatus] || PROFILE_STATUS_STYLES.DRAFT;
  const el = leaveBalances?.EL?.available_days ?? 0;
  const hpl = leaveBalances?.HPL?.available_days ?? 0;
  const cl = leaveBalances?.CL?.available_days ?? 0;

  const recommendedLeaves = dashboardStats?.leave_stats?.recommended ?? 0;
  const sanctionedLeaves = dashboardStats?.leave_stats?.sanctioned ?? 0;
  const notificationsUnread = dashboardStats?.notifications_unread ?? 0;

  const employeeCode = profile?.employee_code || null;
  const employmentType = profile?.employment_type || null;
  const serviceStatus = normalizeServiceStatus(profile?.service_status || profile?.employee_status);
  const joiningDate = profile?.date_of_initial_engagement
    ? formatJoiningDate(profile.date_of_initial_engagement)
    : null;

  const serviceStatusColors = {
    ACTIVE: "bg-green-100 text-green-700",
    RETIRED: "bg-slate-100 text-slate-600",
    RESIGNED: "bg-orange-100 text-orange-700",
    TERMINATED: "bg-red-100 text-red-700",
    DECEASED: "bg-slate-200 text-slate-700",
  };
  const serviceStatusClass = serviceStatusColors[serviceStatus] || "bg-slate-100 text-slate-600";

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in" data-testid="ess-dashboard">

        {/* ── Header ── */}
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Employee Self-Service Portal</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">
              {profile?.full_name || user?.name || "Employee"}
            </h2>
            <div className="flex flex-wrap items-center gap-2 text-sm text-slate-500">
              {employeeCode && (
                <span className="font-mono font-medium text-slate-700">{employeeCode}</span>
              )}
              {employeeCode && (joiningDate || employmentType) && (
                <span className="text-slate-300">|</span>
              )}
              {employmentType && (
                <span>{employmentType.replace(/_/g, " ")}</span>
              )}
              {joiningDate && (
                <>
                  <span className="text-slate-300">|</span>
                  <span className="flex items-center gap-1">
                    <CalendarDays className="w-3.5 h-3.5" />
                    Joined {joiningDate}
                  </span>
                </>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2 shrink-0">
            <Badge className={statusClass}>Profile: {workflowStatus}</Badge>
            <Badge className={serviceStatusClass}>{serviceStatus}</Badge>
            {notificationsUnread > 0 && (
              <button
                type="button"
                onClick={() => navigate(ESS.NOTIFICATIONS)}
                className="inline-flex items-center gap-1.5 rounded-full bg-red-50 text-red-600 border border-red-200 px-2.5 py-0.5 text-xs font-semibold hover:bg-red-100 transition-colors"
              >
                <Bell className="w-3 h-3" />
                {notificationsUnread} unread
              </button>
            )}
          </div>
        </div>

        {/* ── Stat Cards ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Leave Balance */}
          <Card className="layer-2-card">
            <CardContent className="pt-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Leave Balance</p>
                  <div className="flex gap-3">
                    <LeaveBalancePill type="EL" days={el} />
                    <LeaveBalancePill type="HPL" days={hpl} />
                    <LeaveBalancePill type="CL" days={cl} />
                  </div>
                </div>
                <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                  <Calendar className="w-5 h-5" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Leave Activity */}
          <Card className="layer-2-card">
            <CardContent className="pt-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Leave Activity</p>
                  <div className="flex flex-col gap-1">
                    <LeaveActivityRow icon={Clock} label="Pending" count={pendingLeaves} color="text-amber-600" />
                    <LeaveActivityRow icon={TrendingUp} label="Recommended" count={recommendedLeaves} color="text-blue-600" />
                    <LeaveActivityRow icon={ThumbsUp} label="Sanctioned" count={sanctionedLeaves} color="text-green-600" />
                  </div>
                </div>
                <div className="w-10 h-10 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
                  <CalendarDays className="w-5 h-5" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Service Book */}
          {serviceBookEligible && (
            <Card className="layer-2-card">
              <CardContent className="pt-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500 mb-1">Service Book</p>
                    <p className="text-2xl font-bold text-slate-900">{serviceBookEntries}</p>
                    <p className="text-xs text-slate-500 mt-1">
                      {serviceBookAvailableParts > 0
                        ? `${serviceBookAvailableParts} parts available`
                        : "No parts available"}
                    </p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
                    <BookOpen className="w-5 h-5" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Notifications */}
          <Card
            className="layer-2-card cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => navigate(ESS.NOTIFICATIONS)}
          >
            <CardContent className="pt-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500 mb-1">Notifications</p>
                  <p className="text-2xl font-bold text-slate-900">{notificationsUnread}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {notificationsUnread === 0 ? "All caught up" : `Unread message${notificationsUnread !== 1 ? "s" : ""}`}
                  </p>
                </div>
                <div className={[
                  "w-10 h-10 rounded-full flex items-center justify-center shrink-0 relative",
                  notificationsUnread > 0 ? "bg-red-100 text-red-600" : "bg-slate-100 text-slate-500",
                ].join(" ")}>
                  <Bell className="w-5 h-5" />
                  {notificationsUnread > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center">
                      {notificationsUnread > 9 ? "9+" : notificationsUnread}
                    </span>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Quick Actions ── */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Quick Actions</CardTitle>
            <CardDescription>Frequently used employee actions.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <ActionTile
              icon={UserRound}
              label="My Profile"
              description="View and update your profile information"
              onClick={() => navigate(ESS.PROFILE)}
            />
            {serviceBookEligible && (
              <ActionTile
                icon={BookOpen}
                label="Service Book"
                description="View your service history and entries"
                onClick={() => navigate(ESS.SERVICE_BOOK)}
              />
            )}
            <ActionTile
              icon={Calendar}
              label="Leave"
              description="Apply for leave or track your requests"
              onClick={() => navigate(ESS.LEAVE)}
            />
            <ActionTile
              icon={GitPullRequestDraft}
              label="Change Requests"
              description="Submit or track data change requests"
              onClick={() => navigate(ESS.CHANGE_REQUESTS)}
            />
            {canReadOwnDocuments && (
              <ActionTile
                icon={FileText}
                label="My Documents"
                description="Open documents linked to your employee record"
                onClick={() => navigate(ESS.DOCUMENTS)}
              />
            )}
            <ActionTile
              icon={Bell}
              label="Notifications"
              description={notificationsUnread > 0 ? `${notificationsUnread} unread notification${notificationsUnread !== 1 ? "s" : ""}` : "Check your notifications"}
              onClick={() => navigate(ESS.NOTIFICATIONS)}
              badge={notificationsUnread > 0 ? String(notificationsUnread) : null}
            />
          </CardContent>
        </Card>

        {/* ── Pending Actions + Recent Updates ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ClipboardList className="w-5 h-5" />
                Pending Actions
              </CardTitle>
              <CardDescription>Items that may need your attention.</CardDescription>
            </CardHeader>
            <CardContent>
              {pendingActions.length === 0 ? (
                <div className="text-sm text-slate-500 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  No immediate action required.
                </div>
              ) : (
                <ul className="space-y-2 text-sm text-slate-700">
                  {pendingActions.map((action) => (
                    <li key={action} className="flex items-start gap-2">
                      <span className="mt-1 w-1.5 h-1.5 rounded-full bg-blue-600 flex-shrink-0" />
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <History className="w-5 h-5" />
                Recent Updates
              </CardTitle>
              <CardDescription>Latest profile and leave activity.</CardDescription>
            </CardHeader>
            <CardContent>
              {recentUpdates.length === 0 ? (
                <div className="text-sm text-slate-500">No recent updates found.</div>
              ) : (
                <div className="space-y-2">
                  {recentUpdates.map((event) => (
                    <div key={event.id} className="flex items-start gap-3 rounded-lg border p-3">
                      <div className={[
                        "mt-0.5 w-7 h-7 rounded-full flex items-center justify-center shrink-0",
                        event.type === "leave" ? "bg-emerald-100 text-emerald-600" : "bg-blue-100 text-blue-600",
                      ].join(" ")}>
                        {event.type === "leave"
                          ? <Calendar className="w-3.5 h-3.5" />
                          : <UserRound className="w-3.5 h-3.5" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-medium text-sm text-slate-900 truncate">{event.title}</p>
                          <Badge variant="outline" className="text-[10px] uppercase shrink-0">{event.type}</Badge>
                        </div>
                        <p className="text-xs text-slate-600 mt-0.5 truncate">{event.note}</p>
                        <p className="text-[11px] text-slate-400 mt-1">{formatDateTime(event.when)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

      </div>
    </Layout>
  );
};

// ── Helpers ────────────────────────────────────────────────────────────────

const normalizeServiceStatus = (value) => {
  const normalized = String(value || "").trim().toUpperCase();
  return normalized || "ACTIVE";
};

const formatJoiningDate = (value) => {
  if (!value) return null;
  try {
    const d = new Date(value);
    if (isNaN(d.getTime())) return null;
    return d.toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return null;
  }
};

// ── Sub-components ──────────────────────────────────────────────────────────

const LeaveBalancePill = ({ type, days }) => (
  <div className="flex flex-col items-center">
    <span className="text-lg font-bold text-slate-900 leading-none">{days}</span>
    <span className="text-[10px] text-slate-500 uppercase font-semibold mt-0.5">{type}</span>
  </div>
);

const LeaveActivityRow = ({ icon: Icon, label, count, color }) => (
  <div className="flex items-center gap-2">
    <Icon className={`w-3.5 h-3.5 ${color}`} />
    <span className="text-xs text-slate-600 flex-1">{label}</span>
    <span className={`text-xs font-bold ${count > 0 ? color : "text-slate-400"}`}>{count}</span>
  </div>
);

const ActionTile = ({ icon: Icon, label, description, onClick, badge = null }) => (
  <button
    type="button"
    onClick={onClick}
    className="text-left flex items-start gap-3 rounded-lg border border-slate-200 p-4 hover:bg-slate-50 hover:border-slate-300 transition-colors"
  >
    <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center shrink-0 mt-0.5">
      <Icon className="w-4 h-4" />
    </div>
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-slate-900">{label}</span>
        {badge && (
          <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-bold">
            {badge}
          </span>
        )}
      </div>
      <p className="text-xs text-slate-500 mt-0.5 leading-snug">{description}</p>
    </div>
  </button>
);

export default EssDashboard;

