import {
  ANALYTICS_SECTION_CONFIG,
  AnalyticsBreakdownList,
  AnalyticsCategoryTick,
  AnalyticsDataNotice,
  AnalyticsInteractionHint,
  AnalyticsSectionLoader,
  AnalyticsTrendQuickList,
  ChartCard,
  CustomTooltip,
  EmptyChart,
  KpiCard,
} from "@/contexts/analytics/components/analyticsDashboardPrimitives";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Users,
  ClipboardList,
  Calendar,
  TrendingUp,
  ArrowUpRight,
} from "lucide-react";
import {
  CHART_COLORS,
  COUNT_AXIS_PROPS,
  STATUS_COLORS,
  WORKFLOW_STAGE_LABELS,
  formatWorkflowStageSeries,
  getAnalyticsItemRawValues,
  sortWorkflowStageSeries,
} from "@/contexts/analytics/model/analyticsDashboardModel";

export {
  ANALYTICS_SECTION_CONFIG,
  AnalyticsDataNotice,
  AnalyticsInteractionHint,
  AnalyticsSectionLoader,
};

export {
  AnalyticsDrilldownSheet,
  DEFAULT_WORKFORCE_DRILLDOWN_FIELDS,
  WORKFORCE_DRILLDOWN_FIELDS,
} from "@/contexts/analytics/components/AnalyticsDrilldownSheet";

export const OverviewPanel = ({ overview, workflow, openDrilldown }) => {
  if (!overview) return <EmptyChart message="Overview data unavailable" />;

  const workflowStageData = sortWorkflowStageSeries(
    formatWorkflowStageSeries(
      Object.entries(overview.workflow_stages || {}).map(([name, value]) => ({ name, value }))
    )
  );
  const totalProfiles = workflow?.total_profiles || workflowStageData.reduce((sum, stage) => sum + stage.value, 0);
  const completedProfiles = workflow?.locked_profiles ?? overview.locked_profiles ?? 0;
  const workflowStageBreakdown = workflowStageData.map((stage) => ({
    ...stage,
    tooltipLabel: totalProfiles > 0 ? `${stage.name} (${Math.round((stage.value / totalProfiles) * 100)}%)` : stage.name,
  }));
  const openWorkflowStage = (stage) => openDrilldown({
    section: "workflow",
    dimension: "stage",
    value: stage.rawName,
    label: `${stage.name} profiles`,
    description: `Employee profiles currently in the ${stage.name} stage.`,
  });

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon={Users}
          label="Total Employees"
          value={overview.total_employees}
          subtitle={overview.active_employees === overview.total_employees ? "All active" : `${overview.active_employees} active`}
          color="text-blue-600"
          bg="bg-blue-50"
          onClick={() => openDrilldown({
            section: "workforce",
            dimension: "all",
            label: "All employees",
            description: "All employee identity records included in the workforce overview.",
          })}
        />
        <KpiCard
          icon={ClipboardList}
          label="Pending Profiles"
          value={overview.pending_profiles}
          subtitle={`${completedProfiles} completed`}
          color="text-amber-600"
          bg="bg-amber-50"
          onClick={() => openDrilldown({
            section: "workflow",
            dimension: "pending",
            label: "Pending profiles",
            description: "Profiles waiting in submitted, verified, or approved workflow stages.",
          })}
        />
        <KpiCard
          icon={Calendar}
          label="Leave Applications"
          value={overview.total_leave_applications}
          subtitle={`${overview.pending_leaves} awaiting action`}
          color="text-emerald-600"
          bg="bg-emerald-50"
          onClick={() => openDrilldown({
            section: "leave",
            dimension: "all",
            label: "All leave applications",
            description: "All leave applications counted in leave analytics.",
          })}
        />
        <KpiCard
          icon={TrendingUp}
          label="Recent Service Book Records"
          value={overview.recent_service_events_30d}
          subtitle="Last 30 days"
          color="text-violet-600"
          bg="bg-violet-50"
          onClick={() => openDrilldown({
            section: "serviceEvents",
            dimension: "recent_30d",
            label: "Recent Service Book records",
            description: "Service events recorded during the last 30 days.",
          })}
        />
      </div>

      {/* Workflow stage bar + completion rate */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ChartCard
          title="Profile Workflow Pipeline"
          description="Profiles by current workflow stage"
          className="lg:col-span-2"
        >
          {workflowStageData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={workflowStageData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis {...COUNT_AXIS_PROPS} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" name="Profiles" radius={[6, 6, 0, 0]} onClick={openWorkflowStage}>
                    {workflowStageData.map((entry) => (
                      <Cell key={entry.rawName || entry.name} fill={STATUS_COLORS[entry.rawName] || "#6b7280"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <AnalyticsBreakdownList items={workflowStageBreakdown} onSelect={openWorkflowStage} />
            </>
          ) : (
            <EmptyChart />
          )}
        </ChartCard>

        <ChartCard title="Completion Rate" description={`Profiles reaching the ${WORKFLOW_STAGE_LABELS.LOCKED} stage`}>
          <div className="flex flex-col items-center justify-center h-[280px] gap-4">
            <div className="relative w-36 h-36">
              <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#f1f5f9" strokeWidth="12" />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray={`${(workflow?.completion_rate || 0) * 2.51} 251`}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold">{workflow?.completion_rate ?? 0}%</span>
              </div>
            </div>
            <div className="text-center text-sm text-muted-foreground">
              <p>{workflow?.locked_profiles ?? 0} of {workflow?.total_profiles ?? 0} profiles</p>
              <button
                type="button"
                onClick={() => openDrilldown({
                  section: "workflow",
                  dimension: "stage",
                  value: "LOCKED",
                  label: "Completed profiles",
                  description: "Profiles that have reached the locked stage.",
                })}
                className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-sky-700 hover:text-sky-800"
              >
                View matching profiles
                <ArrowUpRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </ChartCard>
      </div>
    </div>
  );
};

/* ─── Workforce Panel ────────────────────────────────────────────── */

export const WorkforcePanel = ({ data, openDrilldown }) => {
  if (!data) return <EmptyChart message="Workforce data unavailable" />;

  const openCategory = (dimension, labelPrefix) => (item) => openDrilldown({
    section: "workforce",
    dimension,
    values: getAnalyticsItemRawValues(item),
    label: `${labelPrefix}: ${item.tooltipLabel || item.name}`,
    description: `Employees matching ${item.tooltipLabel || item.name}.`,
  });

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* By Department */}
        <ChartCard title="Employees by Department" description="Active employees per department">
          {data.by_department?.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={data.by_department} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 180 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis type="number" {...COUNT_AXIS_PROPS} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={<AnalyticsCategoryTick />}
                    width={170}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" name="Employees" fill="#3b82f6" radius={[0, 6, 6, 0]} onClick={openCategory("department", "Department")} />
                </BarChart>
              </ResponsiveContainer>
              <AnalyticsBreakdownList items={data.by_department} onSelect={openCategory("department", "Department")} />
            </>
          ) : (
            <EmptyChart />
          )}
        </ChartCard>

        {/* By Employment Type */}
        <ChartCard title="Employment Type Distribution" description="Breakdown of active workforce">
          {data.by_employment_type?.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie
                  data={data.by_employment_type}
                  cx="50%"
                  cy="50%"
                  outerRadius={110}
                  innerRadius={60}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  labelLine={false}
                  onClick={(entry) => openCategory("employment_type", "Employment type")(entry?.payload || entry)}
                >
                  {data.by_employment_type.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart />
          )}
          <AnalyticsBreakdownList items={data.by_employment_type} onSelect={openCategory("employment_type", "Employment type")} />
        </ChartCard>

        {/* By Gender */}
        <ChartCard title="Gender Distribution" description="Active employees by gender">
          {data.by_gender?.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={data.by_gender}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, value }) => `${name}: ${value}`}
                  onClick={(entry) => openCategory("gender", "Gender")(entry?.payload || entry)}
                >
                  {data.by_gender.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart />
          )}
          <AnalyticsBreakdownList items={data.by_gender} onSelect={openCategory("gender", "Gender")} />
        </ChartCard>

        {/* By Status */}
        <ChartCard title="Employee Status" description="All employees by current status">
          {data.by_status?.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.by_status} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis {...COUNT_AXIS_PROPS} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" name="Count" radius={[6, 6, 0, 0]} onClick={openCategory("status", "Status")}>
                  {data.by_status.map((entry) => (
                    <Cell key={entry.rawName || entry.name} fill={STATUS_COLORS[entry.rawName] || "#6b7280"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart />
          )}
          <AnalyticsBreakdownList items={data.by_status} onSelect={openCategory("status", "Status")} />
        </ChartCard>
      </div>

      {/* By Designation */}
      <ChartCard title="Top Designations" description="Employees by designation (top 15)">
        {data.by_designation?.length > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={360}>
              <BarChart data={data.by_designation} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 210 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" {...COUNT_AXIS_PROPS} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={<AnalyticsCategoryTick />}
                  width={200}
                />
                <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" name="Employees" fill="#8b5cf6" radius={[0, 6, 6, 0]} onClick={openCategory("designation", "Designation")} />
              </BarChart>
            </ResponsiveContainer>
            <AnalyticsBreakdownList items={data.by_designation} onSelect={openCategory("designation", "Designation")} />
          </>
        ) : (
          <EmptyChart />
        )}
      </ChartCard>
    </div>
  );
};

/* ─── Leave Panel ────────────────────────────────────────────────── */

export { LeavePanel, WorkflowPanel, ServiceEventsPanel } from "@/contexts/analytics/components/analyticsDashboardPanels";
