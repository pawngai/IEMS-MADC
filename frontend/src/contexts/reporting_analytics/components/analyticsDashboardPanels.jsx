import { getAnalyticsEmployeeDisplay } from "@/contexts/reporting_analytics/lib/analyticsDashboardUiHelpers";
import { Badge } from "@/shared/ui/badge";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
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
  ClipboardList,
  CheckCircle2,
  TrendingUp,
} from "lucide-react";
import {
  AnalyticsBreakdownList,
  AnalyticsCategoryTick,
  AnalyticsTrendQuickList,
  ChartCard,
  CustomTooltip,
  EmptyChart,
  KpiCard,
} from "@/contexts/reporting_analytics/components/analyticsDashboardPrimitives";
import {
  CHART_COLORS,
  COUNT_AXIS_PROPS,
  LEAVE_STATUS_COLORS,
  STATUS_COLORS,
  WORKFLOW_STAGE_ORDER,
  formatWorkflowStageSeries,
  getAnalyticsItemRawValues,
} from "@/contexts/reporting_analytics/model/analyticsDashboardModel";

export const LeavePanel = ({ data, openDrilldown }) => {
  if (!data) return <EmptyChart message="Leave data unavailable" />;

  const openLeaveCategory = (dimension, labelPrefix) => (item) => openDrilldown({
    section: "leave",
    dimension,
    values: getAnalyticsItemRawValues(item),
    label: `${labelPrefix}: ${item.tooltipLabel || item.name}`,
    description: `Leave applications matching ${item.tooltipLabel || item.name}.`,
  });

  return (
    <div className="space-y-6">
      {/* Monthly trend */}
      <ChartCard title="Leave Applications — Monthly Trend" description="Applications submitted over the last 12 months">
        {data.monthly_trend?.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.monthly_trend} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis {...COUNT_AXIS_PROPS} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="applications"
                name="Applications"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ r: 4, fill: "#3b82f6" }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart message="No leave trend data" />
        )}
        <AnalyticsTrendQuickList
          items={data.monthly_trend}
          metricKey="applications"
          metricLabel="applications"
          onSelect={(item) => openDrilldown({
            section: "leave",
            dimension: "month",
            value: item.monthKey,
            label: `Leave applications in ${item.month}`,
            description: `Leave applications submitted during ${item.month}.`,
          })}
        />
      </ChartCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* By Type */}
        <ChartCard title="Leave by Type" description="Distribution across leave categories">
          {data.by_type?.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={data.by_type}
                  cx="50%"
                  cy="50%"
                  outerRadius={110}
                  innerRadius={55}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, value }) => `${name}: ${value}`}
                  labelLine={false}
                  onClick={(entry) => openLeaveCategory("type", "Leave type")(entry?.payload || entry)}
                >
                  {data.by_type.map((_, i) => (
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
          <AnalyticsBreakdownList items={data.by_type} onSelect={openLeaveCategory("type", "Leave type")} />
        </ChartCard>

        {/* By Status */}
        <ChartCard title="Leave by Status" description="Current status of all applications">
          {data.by_status?.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={data.by_status}
                  cx="50%"
                  cy="50%"
                  outerRadius={110}
                  innerRadius={55}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, value }) => `${name}: ${value}`}
                  labelLine={false}
                  onClick={(entry) => openLeaveCategory("status", "Leave status")(entry?.payload || entry)}
                >
                  {data.by_status.map((entry, i) => (
                    <Cell key={entry.rawName || entry.name || i} fill={LEAVE_STATUS_COLORS[entry.rawName] || CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart />
          )}
          <AnalyticsBreakdownList items={data.by_status} onSelect={openLeaveCategory("status", "Leave status")} />
        </ChartCard>
      </div>

      {/* Average Duration Table */}
      {data.avg_duration_by_type?.length > 0 && (
        <ChartCard title="Average Leave Duration" description="Average days per leave type">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="pb-2 font-medium text-muted-foreground">Leave Type</th>
                  <th className="pb-2 font-medium text-muted-foreground text-right">Avg. Days</th>
                  <th className="pb-2 font-medium text-muted-foreground text-right">Total Applications</th>
                </tr>
              </thead>
              <tbody>
                {data.avg_duration_by_type.map((row) => (
                  <tr
                    key={row.type}
                    className="cursor-pointer border-b transition-colors hover:bg-slate-50 last:border-0"
                    onClick={() => openDrilldown({
                      section: "leave",
                      dimension: "type",
                      value: row.rawType,
                      label: `Leave type: ${row.type}`,
                      description: `Leave applications recorded under ${row.type}.`,
                    })}
                  >
                    <td className="py-2.5 font-medium">{row.type}</td>
                    <td className="py-2.5 text-right tabular-nums">{row.avg_days}</td>
                    <td className="py-2.5 text-right tabular-nums">{row.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ChartCard>
      )}
    </div>
  );
};

/* ─── Workflow Panel ─────────────────────────────────────────────── */

export const WorkflowPanel = ({ data, openDrilldown }) => {
  if (!data) return <EmptyChart message="Workflow data unavailable" />;

  const orderedStages = formatWorkflowStageSeries(
    WORKFLOW_STAGE_ORDER.map((name) => {
      const found = data.by_stage?.find((stage) => stage.name === name);
      return { name, value: found?.value || 0 };
    }).filter((stage) => stage.value > 0)
  );
  const workflowTotal = data.total_profiles || orderedStages.reduce((sum, stage) => sum + stage.value, 0);
  const openWorkflowCategory = (item) => openDrilldown({
    section: "workflow",
    dimension: "stage",
    value: item.rawName,
    label: `Workflow stage: ${item.tooltipLabel || item.name}`,
    description: `Profiles currently in the ${item.tooltipLabel || item.name} stage.`,
  });

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard
          icon={ClipboardList}
          label="Total Profiles"
          value={data.total_profiles}
          color="text-blue-600"
          bg="bg-blue-50"
          onClick={() => openDrilldown({
            section: "workflow",
            dimension: "all",
            label: "All profiles",
            description: "All profiles tracked in the workflow dashboard.",
          })}
        />
        <KpiCard
          icon={CheckCircle2}
          label="Completed (Locked)"
          value={data.locked_profiles}
          color="text-emerald-600"
          bg="bg-emerald-50"
          onClick={() => openDrilldown({
            section: "workflow",
            dimension: "stage",
            value: "LOCKED",
            label: "Locked profiles",
            description: "Profiles that have completed workflow and reached the locked stage.",
          })}
        />
        <KpiCard
          icon={TrendingUp}
          label="Completion Rate"
          value={`${data.completion_rate}%`}
          color="text-violet-600"
          bg="bg-violet-50"
          onClick={() => openDrilldown({
            section: "workflow",
            dimension: "stage",
            value: "LOCKED",
            label: "Profiles in locked stage",
            description: "Profiles contributing to the workflow completion rate.",
          })}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Stage distribution */}
        <ChartCard title="Workflow Stage Distribution" description="Current stage for all profiles">
          {orderedStages.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={orderedStages} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis {...COUNT_AXIS_PROPS} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" name="Profiles" radius={[6, 6, 0, 0]} onClick={openWorkflowCategory}>
                  {orderedStages.map((entry) => (
                    <Cell key={entry.rawName || entry.name} fill={STATUS_COLORS[entry.rawName] || "#6b7280"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart />
          )}
          <AnalyticsBreakdownList items={orderedStages} onSelect={openWorkflowCategory} />
        </ChartCard>

        {/* SLA distribution */}
        <ChartCard title="SLA Distribution" description="Time pending items have spent in current stage">
          {data.sla_distribution?.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={data.sla_distribution} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                <YAxis {...COUNT_AXIS_PROPS} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Items" radius={[6, 6, 0, 0]}>
                  {data.sla_distribution.map((_, i) => {
                    const colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#991b1b"];
                    return <Cell key={i} fill={colors[i] || "#6b7280"} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="No pending items for SLA analysis" />
          )}
        </ChartCard>
      </div>

      {/* Workflow funnel */}
      <ChartCard title="Workflow Funnel" description="Visual pipeline of profile stages">
        <div className="flex flex-col gap-2 py-4">
          {orderedStages.map((stage) => {
            const maxVal = Math.max(...orderedStages.map((s) => s.value), 1);
            const pct = Math.max((stage.value / maxVal) * 100, 4);
            const shareOfProfiles = workflowTotal > 0 ? Math.round((stage.value / workflowTotal) * 100) : 0;
            return (
              <div key={stage.name} className="flex items-center gap-3">
                <span className="text-xs font-medium w-24 text-right truncate" title={stage.tooltipLabel || stage.name}>
                  {stage.name}
                </span>
                <div className="flex-1 h-8 bg-slate-100 rounded-md overflow-hidden">
                  <div
                    className="h-full rounded-md flex items-center px-3 text-xs font-semibold text-white transition-all"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: STATUS_COLORS[stage.rawName] || "#6b7280",
                    }}
                  >
                    {stage.value}
                  </div>
                </div>
                <span className="w-20 text-right text-xs font-medium text-slate-600">{shareOfProfiles}% of profiles</span>
              </div>
            );
          })}
        </div>
      </ChartCard>
    </div>
  );
};

/* ─── Service Book Records Panel ───────────────────────────────────────── */

export const ServiceEventsPanel = ({ data, openDrilldown }) => {
  if (!data) return <EmptyChart message="Service events data unavailable" />;

  const openEventType = (item) => openDrilldown({
    section: "serviceEvents",
    dimension: "type",
    values: getAnalyticsItemRawValues(item),
    label: `Service event type: ${item.tooltipLabel || item.name}`,
    description: `Service events recorded as ${item.tooltipLabel || item.name}.`,
  });

  return (
    <div className="space-y-6">
      {/* Monthly trend */}
      <ChartCard title="Service Book Records - Monthly Trend" description="Records created over the last 12 months">
        {data.monthly_trend?.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.monthly_trend} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis {...COUNT_AXIS_PROPS} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="events"
                name="Events"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={{ r: 4, fill: "#8b5cf6" }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart message="No event trend data" />
        )}
        <AnalyticsTrendQuickList
          items={data.monthly_trend}
          metricKey="events"
          metricLabel="events"
          onSelect={(item) => openDrilldown({
            section: "serviceEvents",
            dimension: "month",
            value: item.monthKey,
            label: `Service events in ${item.month}`,
            description: `Service events recorded during ${item.month}.`,
          })}
        />
      </ChartCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* By Type */}
        <ChartCard title="Events by Type" description="Service event type distribution">
          {data.by_type?.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={Math.max(data.by_type.length * 42, 240)}>
                <BarChart data={data.by_type} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 210 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis type="number" {...COUNT_AXIS_PROPS} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={<AnalyticsCategoryTick />}
                    width={200}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" name="Events" fill="#8b5cf6" radius={[0, 6, 6, 0]} onClick={openEventType} />
                </BarChart>
              </ResponsiveContainer>
              <AnalyticsBreakdownList items={data.by_type} onSelect={openEventType} />
            </>
          ) : (
            <EmptyChart />
          )}
        </ChartCard>

        {/* Recent events table */}
        <ChartCard title="Recent Service Book Records" description="Most recently recorded events">
          {data.recent_events?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-2 font-medium text-muted-foreground">Event Type</th>
                    <th className="pb-2 font-medium text-muted-foreground">Employee</th>
                    <th className="pb-2 font-medium text-muted-foreground">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_events.map((evt, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-2">
                        <Badge variant="outline" className="text-xs">
                          {evt.event_type_label || evt.event_type}
                        </Badge>
                      </td>
                      <td className="py-2">
                        {(() => {
                          const employeeDisplay = getAnalyticsEmployeeDisplay(evt);
                          return (
                        <div className="max-w-[18rem] min-w-0">
                          <p className="truncate text-sm font-medium text-slate-900">
                            {employeeDisplay.primary}
                          </p>
                          {employeeDisplay.secondary && (
                            <p className="truncate text-xs font-mono text-muted-foreground" title={evt.employee_id || evt.employee_code || ""}>
                              {employeeDisplay.secondary}
                            </p>
                          )}
                        </div>
                          );
                        })()}
                      </td>
                      <td className="py-2 text-xs text-muted-foreground">
                        {evt.created_at
                          ? new Date(evt.created_at).toLocaleDateString()
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyChart message="No recent events" />
          )}
        </ChartCard>
      </div>
    </div>
  );
};


