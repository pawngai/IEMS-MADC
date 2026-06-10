import { analyticsAPI } from "@/contexts/analytics/api/analyticsApi";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import {
  AlertTriangle,
  ArrowUpRight,
  Loader2,
  MousePointerClick,
} from "lucide-react";
import {
  getAnalyticsItemRawValues,
  wrapChartTick,
} from "@/contexts/analytics/model/analyticsDashboardModel";

export const AnalyticsCategoryTick = ({ x = 0, y = 0, payload }) => {
  const label = String(payload?.value ?? "").trim();
  const lines = wrapChartTick(label);
  const startDy = lines.length > 1 ? -((lines.length - 1) * 7) / 2 : 4;

  return (
    <g transform={`translate(${x},${y})`}>
      <title>{label}</title>
      <text textAnchor="end" fill="#475569" fontSize="11">
        {lines.map((line, index) => (
          <tspan key={`${label}-${index}`} x={0} dy={index === 0 ? startDy : 14}>
            {index < lines.length - 1 ? `${line} ` : line}
          </tspan>
        ))}
      </text>
    </g>
  );
};

export const KpiCard = ({
  icon: Icon,
  label,
  value,
  subtitle,
  color = "text-blue-600",
  bg = "bg-blue-50",
  onClick,
}) => {
  const isInteractive = typeof onClick === "function";

  return (
    <Card className={isInteractive ? "transition-shadow hover:shadow-md" : ""}>
      <CardContent className="pt-6">
        <button
          type="button"
          onClick={onClick}
          disabled={!isInteractive}
          className={`flex w-full items-center gap-4 text-left ${isInteractive ? "cursor-pointer" : "cursor-default"}`}
        >
          <div className={`rounded-xl p-3 ${bg}`}>
            <Icon className={`h-6 w-6 ${color}`} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm text-muted-foreground">{label}</p>
                <p className="text-2xl font-bold tabular-nums text-slate-950">{value ?? "-"}</p>
              </div>
              {isInteractive && <ArrowUpRight className="mt-1 h-4 w-4 shrink-0 text-slate-400" />}
            </div>
            {subtitle && <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>}
          </div>
        </button>
      </CardContent>
    </Card>
  );
};

export const ChartCard = ({ title, description, children, className = "" }) => (
  <Card className={className}>
    <CardHeader className="pb-2">
      <CardTitle className="text-base">{title}</CardTitle>
      {description && <CardDescription>{description}</CardDescription>}
    </CardHeader>
    <CardContent>{children}</CardContent>
  </Card>
);

export const EmptyChart = ({ message = "No data available" }) => (
  <div className="flex items-center justify-center h-48 text-sm text-muted-foreground">
    {message}
  </div>
);

export const AnalyticsBreakdownList = ({ items, onSelect }) => {
  if (!items?.length) return null;

  return (
    <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
      {items.map((item) => {
        const label = item.tooltipLabel || item.name;
        const key = `${getAnalyticsItemRawValues(item).join("|")}::${item.name}::${item.value}`;
        const content = (
          <>
            <span className="truncate text-slate-700" title={label}>{label}</span>
            <span className="flex items-center gap-2 font-semibold tabular-nums text-slate-900">
              {item.value}
              {onSelect && <ArrowUpRight className="h-3.5 w-3.5 text-slate-400" />}
            </span>
          </>
        );

        if (typeof onSelect === "function") {
          return (
            <button
              key={key}
              type="button"
              onClick={() => onSelect(item)}
              className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm transition-colors hover:border-sky-200 hover:bg-sky-50"
            >
              {content}
            </button>
          );
        }

        return (
          <div
            key={key}
            className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm"
          >
            {content}
          </div>
        );
      })}
    </div>
  );
};

export const AnalyticsTrendQuickList = ({ items, metricKey, metricLabel, onSelect }) => {
  if (!items?.length || typeof onSelect !== "function") return null;

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {items.map((item) => (
        <button
          key={item.monthKey || item.month}
          type="button"
          onClick={() => onSelect(item)}
          className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:border-sky-200 hover:bg-sky-50 hover:text-sky-700"
        >
          {item.month}: {item[metricKey]} {metricLabel}
        </button>
      ))}
    </div>
  );
};

export const AnalyticsInteractionHint = () => (
  <div className="flex items-start gap-3 rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
    <MousePointerClick className="mt-0.5 h-4 w-4 shrink-0 text-sky-600" />
    <div>
      <p className="font-medium">Interactive analytics</p>
      <p className="mt-1 text-sky-800">Click KPI cards, chart segments, or breakdown rows to inspect the matching records.</p>
    </div>
  </div>
);

export const AnalyticsDataNotice = ({ failedSections }) => {
  if (!failedSections.length) return null;

  return (
    <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
      <div>
        <p className="font-medium">Some analytics sections are unavailable.</p>
        <p className="mt-1 text-amber-800">
          Missing data: {failedSections.join(", ")}. Refresh to try again.
        </p>
      </div>
    </div>
  );
};

export const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const tooltipLabel = payload[0]?.payload?.tooltipLabel || label;

  return (
    <div className="bg-white border rounded-lg shadow-lg p-3 text-sm">
      {tooltipLabel && <p className="font-medium mb-1">{tooltipLabel}</p>}
      {payload.map((entry, index) => (
        <p key={index} style={{ color: entry.color }}>
          {entry.name}: <span className="font-semibold">{entry.value}</span>
        </p>
      ))}
    </div>
  );
};

export const AnalyticsSectionLoader = ({ message = "Loading analytics..." }) => (
  <Card>
    <CardContent className="flex h-48 items-center justify-center gap-3 text-sm text-muted-foreground">
      <Loader2 className="h-5 w-5 animate-spin" />
      <span>{message}</span>
    </CardContent>
  </Card>
);

export const ANALYTICS_SECTION_CONFIG = {
  overview: {
    label: "Overview",
    request: analyticsAPI.getOverview,
  },
  workforce: {
    label: "Workforce",
    request: analyticsAPI.getWorkforce,
  },
  leave: {
    label: "Leave",
    request: analyticsAPI.getLeave,
  },
  workflow: {
    label: "Workflow",
    request: analyticsAPI.getWorkflow,
  },
  serviceEvents: {
    label: "Service Book Records",
    request: analyticsAPI.getServiceEvents,
  },
};
