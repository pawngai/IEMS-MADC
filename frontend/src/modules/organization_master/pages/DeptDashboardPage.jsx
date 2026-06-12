import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { DEPT } from "@/shared/lib/routes";
import { departmentPortalAPI } from "@/modules/organization_master/api/departmentApi";
import { useDepartmentScope } from "@/modules/organization_master/hooks/useDepartmentScope";
import { getDepartmentBulkProfileCompletion } from "@/modules/organization_master/model/departmentProfileGateway";
import { buildIdentityCreatePath } from "@/shared/lib/employeeEditorRoutes";
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { DashboardSkeleton } from "@/shared/ui/skeletons";
import { toast } from "sonner";
import {
  AlertTriangle, ArrowRight, Building2, CheckCircle2, Clock, ClipboardList,
  Lock, Plus, RefreshCw, Users,
} from "lucide-react";

const DeptDashboard = () => {
  const navigate = useNavigate();
  const {
    loading, setLoading,
    selectedDepartment,
    selectedDepartmentLabel,
    scopeError,
    canUseDepartmentPortal,
    canLeaveWorkflow,
    canCreateProfile,
  } = useDepartmentScope();

  const [refreshing, setRefreshing] = useState(false);
  const [dashboard, setDashboard] = useState(null);
  const [pendingWorkCount, setPendingWorkCount] = useState(0);
  const [bulkCompletion, setBulkCompletion] = useState(null);

  const loadDepartmentData = useCallback(
    async ({ mode = "refresh" } = {}) => {
      if (!selectedDepartment) {
        setDashboard(null);
        setPendingWorkCount(0);
        return;
      }
      if (mode === "initial") setLoading(true);
      else setRefreshing(true);

      try {
        const [dashboardRes, pendingWorkRes] = await Promise.all([
          departmentPortalAPI.getDashboard(),
          departmentPortalAPI.getPendingWork().catch(() => ({ data: { items: [] } })),
        ]);
        setDashboard(dashboardRes.data || null);
        setPendingWorkCount(Number(pendingWorkRes.data?.total ?? pendingWorkRes.data?.items?.length ?? 0));
      } catch (error) {
        console.error("Failed to load department portal data:", error);
        toast.error("Failed to load department data");
        setDashboard(null);
        setPendingWorkCount(0);
      } finally { setLoading(false); setRefreshing(false); }
    },
    [selectedDepartment, setLoading]
  );

  const loadBulkCompletion = useCallback(async () => {
    try { setBulkCompletion(await getDepartmentBulkProfileCompletion()); } catch { /* non-critical */ }
  }, []);

  useEffect(() => {
    if (canUseDepartmentPortal) loadBulkCompletion();
  }, [canUseDepartmentPortal, loadBulkCompletion]);

  useEffect(() => {
    if (!canUseDepartmentPortal || !selectedDepartment) return;
    loadDepartmentData({ mode: "initial" });
  }, [canUseDepartmentPortal, selectedDepartment, loadDepartmentData]);

  const summary = useMemo(() => {
    return {
      totalEmployees: Number(dashboard?.total_employees || 0),
      lockedProfiles: Number(dashboard?.locked_profiles || 0),
      regularEmployees: Number(dashboard?.regular_employees || 0),
      pendingLeaveActions: Number(dashboard?.pending_leave_actions || 0),
      pendingWorkItems: pendingWorkCount,
      sanctionedStrengthConfigured: Boolean(dashboard?.sanctioned_strength_configured),
      sanctionedStrengthTotal: Number(dashboard?.sanctioned_strength_total || 0),
      filledStrengthTotal: Number(dashboard?.filled_strength_total || 0),
      vacancyCount: Number(dashboard?.vacancy_count || 0),
      overStrengthCount: Number(dashboard?.over_strength_count || 0),
    };
  }, [dashboard, pendingWorkCount]);

  if (!canUseDepartmentPortal) {
    return (
      <>
        <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4" data-testid="department-portal-denied">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
            <Lock className="w-8 h-8 text-slate-400" />
          </div>
          <h2 className="text-lg font-semibold text-slate-800 mb-1">Access Restricted</h2>
          <p className="text-sm text-slate-500 max-w-md">
            Department Operations Portal is available only for Head of Department and Data Entry roles.
          </p>
        </div>
      </>
    );
  }

  if (loading) {
    return (
      <>
        <div className="max-w-7xl mx-auto" data-testid="department-portal-loading">
          <DashboardSkeleton />
        </div>
      </>
    );
  }

  if (scopeError) {
    return (
      <>
        <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4" data-testid="department-portal-scope-error">
          <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center mb-4">
            <AlertTriangle className="w-8 h-8 text-amber-500" />
          </div>
          <h2 className="text-lg font-semibold text-slate-800 mb-1">Department Not Mapped</h2>
          <p className="text-sm text-slate-500 max-w-md">{scopeError}</p>
        </div>
      </>
    );
  }

  const completionRate = summary.totalEmployees > 0
    ? Math.round((summary.lockedProfiles / summary.totalEmployees) * 100) : 0;
  const avgFieldCompletion = bulkCompletion?.summary?.average_completion ?? null;
  const bothSectionsCount = bulkCompletion?.summary?.both_sections_complete ?? 0;
  const empSectionCount = bulkCompletion?.summary?.employee_section_complete ?? 0;
  const deSectionCount = bulkCompletion?.summary?.data_entry_section_complete ?? 0;
  const unlocked = summary.totalEmployees - summary.lockedProfiles;
  const occupancyValue = summary.sanctionedStrengthTotal > 0
    ? `${Math.round((summary.filledStrengthTotal / summary.sanctionedStrengthTotal) * 100)}%`
    : "0%";
  const strengthDrilldown = () => navigate(DEPT.SANCTIONED_STRENGTH);

  const pendingActions = [];
  if (summary.pendingWorkItems > 0)
    pendingActions.push({ text: `${summary.pendingWorkItems} profile(s) need attention (Draft or Rejected).`, action: () => navigate(DEPT.PENDING_WORK) });
  if (summary.pendingLeaveActions > 0)
    pendingActions.push({ text: `${summary.pendingLeaveActions} leave request(s) pending action.`, action: () => navigate(DEPT.LEAVE) });
  if (summary.totalEmployees > 0 && completionRate < 100)
    pendingActions.push({ text: `${unlocked} profile(s) not yet locked.`, action: () => navigate(DEPT.DIRECTORY) });
  if (summary.sanctionedStrengthConfigured && summary.vacancyCount > 0)
    pendingActions.push({ text: `${summary.vacancyCount} sanctioned post(s) are vacant.`, action: strengthDrilldown });

  const strengthHint = !summary.sanctionedStrengthConfigured
    ? "Not configured"
    : summary.overStrengthCount > 0
      ? `${summary.vacancyCount} vacant, ${summary.overStrengthCount} over`
      : `${summary.vacancyCount} vacant`;
  const strengthAccent = !summary.sanctionedStrengthConfigured
    ? "slate"
    : summary.vacancyCount > 0 || summary.overStrengthCount > 0
      ? "amber"
      : "blue";

  return (
    <>
      <div className="max-w-7xl mx-auto space-y-6 animate-fade-in" data-testid="dept-dashboard">
        {/* ── Header ── */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Department Operations Portal</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Dashboard</h2>
            <p className="text-sm text-slate-500 mt-1">{selectedDepartmentLabel}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {canCreateProfile && (
              <Button
                size="sm" className="gap-2"
                onClick={() => navigate(buildIdentityCreatePath("department"), { state: { returnTo: DEPT.DASHBOARD } })}
                data-testid="dept-new-employee"
              >
                <Plus className="w-4 h-4" /> New Employee
              </Button>
            )}
            <Button
              variant="outline" size="sm" className="gap-2"
              onClick={() => { loadDepartmentData({ mode: "refresh" }); loadBulkCompletion(); }}
              disabled={refreshing} data-testid="dept-refresh"
            >
              <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} /> Refresh
            </Button>
          </div>
        </div>

        {/* ── Metric Tiles — row 1: operational KPIs ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricTile icon={Users} label="Total Employees" value={summary.totalEmployees} accent="blue"
            hint={`${summary.regularEmployees} regular`} onClick={() => navigate(DEPT.DIRECTORY)} />
          <MetricTile icon={CheckCircle2} label="Locked Profiles" value={summary.lockedProfiles} accent="green"
            hint={`${completionRate}% completion`} />
          <MetricTile icon={Clock} label="Pending Work" value={summary.pendingWorkItems}
            accent={summary.pendingWorkItems > 0 ? "amber" : "slate"}
            hint="Draft or rejected" onClick={() => navigate(DEPT.PENDING_WORK)} />
          <MetricTile icon={ClipboardList} label="Leave Requests" value={summary.pendingLeaveActions}
            accent={summary.pendingLeaveActions > 0 ? "red" : "slate"}
            hint="Pending action" onClick={canLeaveWorkflow ? () => navigate(DEPT.LEAVE) : undefined} />
        </div>

        {/* ── Metric Tiles — row 2: sanctioned strength ── */}
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">Sanctioned Strength</p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricTile icon={Building2} label="Sanctioned Posts" value={summary.sanctionedStrengthTotal} accent="blue"
            hint={strengthHint} onClick={strengthDrilldown} />
          <MetricTile icon={CheckCircle2} label="Filled Posts" value={summary.filledStrengthTotal}
            accent="green"
            hint="Directory drilldown" onClick={strengthDrilldown} />
          <MetricTile icon={AlertTriangle} label="Vacancies" value={summary.vacancyCount}
            accent="amber"
            hint={summary.sanctionedStrengthConfigured ? "Directory drilldown" : "Not configured"}
            onClick={strengthDrilldown} />
          <MetricTile icon={Building2} label="Occupancy" value={occupancyValue}
            accent="violet"
            hint={summary.overStrengthCount > 0 ? `${summary.overStrengthCount} over strength` : "Directory drilldown"}
            onClick={strengthDrilldown} />
        </div>
        </div>

        {/* ── Completion + Pending side by side ── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* Completion rings */}
          {summary.totalEmployees > 0 && (
            <Card className="lg:col-span-2">
              <CardContent className="p-6">
                <h3 className="text-sm font-semibold text-slate-700 mb-4">Profile Completion</h3>
                <div className="flex items-center justify-around">
                  <CompletionRing percent={completionRate} label="Locked" sublabel={`${summary.lockedProfiles} of ${summary.totalEmployees}`} />
                  {avgFieldCompletion !== null && (
                    <CompletionRing percent={avgFieldCompletion} size={100} strokeWidth={8} label="Field Avg" />
                  )}
                </div>
                {avgFieldCompletion !== null && (
                  <div className="flex flex-wrap gap-x-4 gap-y-1 mt-4 justify-center text-[10px] text-slate-500">
                    <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-green-500" /> Emp Section: {empSectionCount}</span>
                    <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-blue-500" /> DE Section: {deSectionCount}</span>
                    <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-purple-500" /> Both Ready: {bothSectionsCount}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Action items */}
          <Card className={summary.totalEmployees > 0 ? "lg:col-span-3" : "lg:col-span-5"}>
            <CardContent className="p-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <ClipboardList className="w-4 h-4" /> Action Items
              </h3>
              {pendingActions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <div className="w-12 h-12 rounded-full bg-green-50 flex items-center justify-center mb-3">
                    <CheckCircle2 className="w-6 h-6 text-green-500" />
                  </div>
                  <p className="text-sm font-medium text-slate-700">All caught up</p>
                  <p className="text-xs text-slate-400 mt-1">No immediate action required.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {pendingActions.map((item) => (
                    <button
                      key={item.text}
                      className="group w-full flex items-center gap-3 rounded-lg border border-transparent hover:border-slate-200 hover:bg-slate-50 p-2.5 text-left transition-colors"
                      onClick={item.action}
                    >
                      <span className="mt-0.5 w-2 h-2 rounded-full bg-amber-500 shrink-0" />
                      <span className="text-sm text-slate-700 flex-1">{item.text}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-blue-500 shrink-0 transition-colors" />
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* ── Quick Navigation ── */}
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Quick Navigation</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <ActionCard icon={Users} title="Employee Directory" description="View and manage employee records"
              onClick={() => navigate(DEPT.DIRECTORY)} />
            <ActionCard icon={AlertTriangle} title="Pending Work" description="Draft & rejected profiles"
              badge={summary.pendingWorkItems} onClick={() => navigate(DEPT.PENDING_WORK)} />
            {canLeaveWorkflow && (
              <ActionCard icon={ClipboardList} title="Leave Requests" description="Review pending leave applications"
                badge={summary.pendingLeaveActions} onClick={() => navigate(DEPT.LEAVE)} />
            )}
            <ActionCard icon={Building2} title="Sanctioned Strength" description="Maintain department establishment plan"
              badge={summary.vacancyCount} onClick={strengthDrilldown} />
          </div>
        </div>
      </div>
    </>
  );
};

/* ------------------------------------------------------------------ */
/*  CompletionRing — SVG circular progress                            */
/* ------------------------------------------------------------------ */
const CompletionRing = ({ percent, size = 120, strokeWidth = 10, label, sublabel }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;
  const color = percent >= 80 ? "text-green-500" : percent >= 50 ? "text-blue-500" : "text-amber-500";

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="currentColor"
            strokeWidth={strokeWidth} className="text-slate-100" />
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="currentColor"
            strokeWidth={strokeWidth} strokeLinecap="round" className={cn("transition-all duration-700", color)}
            strokeDasharray={circumference} strokeDashoffset={offset} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-slate-900">{percent}%</span>
        </div>
      </div>
      {label && <span className="text-xs font-medium text-slate-700">{label}</span>}
      {sublabel && <span className="text-[10px] text-slate-400">{sublabel}</span>}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/*  MetricTile — color-accented stat tile                             */
/* ------------------------------------------------------------------ */
const ACCENT_STYLES = {
  blue:  { tile: "bg-blue-50  border-blue-200",  icon: "bg-blue-500  text-white", value: "text-blue-700",  label: "text-blue-600"  },
  green: { tile: "bg-green-50 border-green-200", icon: "bg-green-500 text-white", value: "text-green-700", label: "text-green-600" },
  amber: { tile: "bg-amber-50 border-amber-200", icon: "bg-amber-500 text-white", value: "text-amber-700", label: "text-amber-600" },
  red:    { tile: "bg-red-50    border-red-200",    icon: "bg-red-500    text-white", value: "text-red-700",    label: "text-red-600"    },
  violet: { tile: "bg-violet-50 border-violet-200", icon: "bg-violet-500 text-white", value: "text-violet-700", label: "text-violet-600" },
  slate:  { tile: "bg-slate-50  border-slate-200",  icon: "bg-slate-400  text-white", value: "text-slate-700",  label: "text-slate-500"  },
};

const MetricTile = ({ icon: Icon, label, value, accent = "blue", hint, onClick }) => {
  const s = ACCENT_STYLES[accent] || ACCENT_STYLES.blue;
  const Wrapper = onClick ? "button" : "div";

  return (
    <Wrapper
      className={cn("rounded-xl border p-4 text-left transition-all", s.tile,
        onClick && "hover:shadow-md hover:brightness-[0.97] cursor-pointer active:scale-[0.98]")}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center shrink-0 shadow-sm", s.icon)}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className={cn("text-2xl font-bold leading-none", s.value)}>{value}</p>
          <p className={cn("text-[11px] font-semibold mt-1", s.label)}>{label}</p>
          {hint && <p className="text-[10px] text-slate-400 mt-0.5">{hint}</p>}
        </div>
      </div>
    </Wrapper>
  );
};

/* ------------------------------------------------------------------ */
/*  ActionCard — navigation card with arrow                           */
/* ------------------------------------------------------------------ */
const ActionCard = ({ icon: Icon, title, description, badge, onClick }) => (
  <button
    className="group flex items-center gap-4 rounded-xl border bg-white p-4 text-left hover:shadow-md hover:border-blue-200 transition-all active:scale-[0.98] w-full"
    onClick={onClick}
  >
    <div className="w-10 h-10 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center shrink-0 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
      <Icon className="w-5 h-5" />
    </div>
    <div className="min-w-0 flex-1">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-slate-900">{title}</span>
        {badge > 0 && <Badge className="bg-amber-100 text-amber-700 text-[10px] px-1.5 py-0">{badge}</Badge>}
      </div>
      <p className="text-xs text-slate-500 mt-0.5">{description}</p>
    </div>
    <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-blue-500 group-hover:translate-x-0.5 transition-all shrink-0" />
  </button>
);

export default DeptDashboard;

