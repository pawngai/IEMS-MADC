/**
 * CompletionTracker - Profile completion widgets for ESS and Data Entry dashboards.
 *
 * Two exports:
 *   <ProfileCompletionCard />  - single-profile view (ESS dashboard)
 *   <BulkCompletionCard />     - aggregate view   (Data Entry dashboard)
 */
import { useEffect, useState, useCallback } from "react";
import { employeeProfileApi } from "@/modules/employee_master/api/employeeProfileApi";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Skeleton } from "@/shared/ui/skeleton";
import {
  CheckCircle2,
  AlertCircle,
  BarChart3,
  User,
  Users,
  Heart,
  IdCard,
  MapPin,
  Briefcase,
} from "lucide-react";

/* helpers */

const SECTION_META = {
  personal:     { label: "Personal Info",    icon: User,      color: "blue"   },
  nominees:     { label: "Family & Nominees", icon: Heart,     color: "pink"   },
  id_documents: { label: "ID Documents",     icon: IdCard,    color: "amber"  },
  address:      { label: "Address & Contact", icon: MapPin,   color: "green"  },
  core:         { label: "Core Employment",  icon: Briefcase, color: "purple" },
};

const colorMap = {
  blue:   { bg: "bg-blue-100",   fill: "bg-blue-600",   text: "text-blue-700"   },
  pink:   { bg: "bg-pink-100",   fill: "bg-pink-500",   text: "text-pink-700"   },
  amber:  { bg: "bg-amber-100",  fill: "bg-amber-500",  text: "text-amber-700"  },
  green:  { bg: "bg-green-100",  fill: "bg-green-600",  text: "text-green-700"  },
  purple: { bg: "bg-purple-100", fill: "bg-purple-600", text: "text-purple-700" },
};

const ProgressBar = ({ percent, color = "blue", className = "" }) => {
  const c = colorMap[color] || colorMap.blue;
  return (
    <div className={`h-2 rounded-full ${c.bg} overflow-hidden ${className}`}>
      <div
        className={`h-full rounded-full ${c.fill} transition-all duration-500`}
        style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
      />
    </div>
  );
};

const CompletionCardSkeleton = ({ compact = false }) => (
  <Card className={compact ? "col-span-full" : undefined}>
    <CardContent className={compact ? "pt-6" : "pt-6"}>
      <div className={compact ? "grid grid-cols-2 gap-4 sm:grid-cols-4" : "space-y-4"}>
        {compact ? (
          Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="space-y-2">
              <Skeleton className="h-3 w-24 rounded" />
              <Skeleton className="h-6 w-20 rounded" />
            </div>
          ))
        ) : (
          <>
            <div className="flex items-center gap-4">
              <Skeleton className="h-20 w-20 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-44 rounded" />
                <div className="flex flex-wrap gap-2">
                  <Skeleton className="h-6 w-28 rounded-full" />
                  <Skeleton className="h-6 w-32 rounded-full" />
                </div>
              </div>
            </div>
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, index) => (
                <div key={index}>
                  <div className="mb-1 flex items-center justify-between">
                    <Skeleton className="h-3 w-28 rounded" />
                    <Skeleton className="h-3 w-20 rounded" />
                  </div>
                  <Skeleton className="h-2 w-full rounded-full" />
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </CardContent>
  </Card>
);

const RingProgress = ({ percent, size = 80, stroke = 7 }) => {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (circ * Math.min(100, Math.max(0, percent))) / 100;
  const ringColor = percent >= 80 ? "#16a34a" : percent >= 50 ? "#d97706" : "#dc2626";

  return (
    <svg width={size} height={size} className="flex-shrink-0">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="#e2e8f0"
        strokeWidth={stroke}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={ringColor}
        strokeWidth={stroke}
        strokeDasharray={circ}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        className="transition-all duration-700"
      />
      <text
        x="50%"
        y="50%"
        dominantBaseline="central"
        textAnchor="middle"
        className="text-sm font-bold fill-slate-800"
      >
        {Math.round(percent)}%
      </text>
    </svg>
  );
};

/* ProfileCompletionCard (ESS) */

export const ProfileCompletionCard = ({ employeeId }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!employeeId) return;
    setLoading(true);
    try {
      const res = await employeeProfileApi.getCompletion(employeeId);
      setData(res.data);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [employeeId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <CompletionCardSkeleton />;
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="pt-6 text-sm text-slate-500">
          Unable to load profile completion data.
        </CardContent>
      </Card>
    );
  }

  const overall = data.overall_percent ?? 0;
  const sections = data.sections || {};
  const essDone = !!data.employee_section_completed;
  const deDone = !!data.data_entry_section_completed;

  return (
    <Card data-testid="profile-completion-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Profile Completion
        </CardTitle>
        <CardDescription>
          Fill every section to unlock submission.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <RingProgress percent={overall} />
          <div className="space-y-1">
            <p className="text-sm font-medium text-slate-700">
              Overall {Math.round(overall)}% complete
            </p>
            <div className="flex flex-wrap gap-2">
              <Badge className={essDone ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-600"}>
                {essDone ? <CheckCircle2 className="w-3 h-3 mr-1" /> : <AlertCircle className="w-3 h-3 mr-1" />}
                My Section {essDone ? "Done" : "Pending"}
              </Badge>
              <Badge className={deDone ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-600"}>
                {deDone ? <CheckCircle2 className="w-3 h-3 mr-1" /> : <AlertCircle className="w-3 h-3 mr-1" />}
                Data Entry {deDone ? "Done" : "Pending"}
              </Badge>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          {Object.entries(sections).map(([key, sec]) => {
            const meta = SECTION_META[key] || { label: key, icon: User, color: "blue" };
            const Icon = meta.icon;
            const pct = sec.percent ?? 0;
            return (
              <div key={key}>
                <div className="flex items-center justify-between mb-1">
                  <span className="flex items-center gap-1.5 text-xs font-medium text-slate-700">
                    <Icon className="w-3.5 h-3.5" />
                    {meta.label}
                  </span>
                  <span className="text-xs text-slate-500">
                    {sec.filled}/{sec.total} fields
                  </span>
                </div>
                <ProgressBar percent={pct} color={meta.color} />
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

/* BulkCompletionCard (Data Entry) */

export const BulkCompletionCard = ({ refreshTrigger }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await employeeProfileApi.getBulkCompletion();
      setData(res.data);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshTrigger]);

  if (loading) {
    return <CompletionCardSkeleton compact />;
  }

  if (!data?.summary) {
    return null; // silently hide if endpoint unavailable
  }

  const s = data.summary;
  const avg = s.average_completion ?? 0;

  const metrics = [
    {
      label: "Avg. Completion",
      value: `${Math.round(avg)}%`,
      color: avg >= 70 ? "text-green-700" : avg >= 40 ? "text-amber-700" : "text-red-600",
    },
    {
      label: "Employee Section Done",
      value: `${s.employee_section_complete ?? 0}/${s.total_profiles ?? 0}`,
      color: "text-blue-700",
    },
    {
      label: "Data Entry Section Done",
      value: `${s.data_entry_section_complete ?? 0}/${s.total_profiles ?? 0}`,
      color: "text-purple-700",
    },
    {
      label: "Both Sections Complete",
      value: `${s.both_sections_complete ?? 0}`,
      color: "text-green-700",
    },
  ];

  return (
    <Card className="col-span-full" data-testid="bulk-completion-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <BarChart3 className="w-4 h-4" />
          Profile Completion Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-6 flex-wrap">
          <RingProgress percent={avg} size={64} stroke={6} />
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-8 gap-y-2">
            {metrics.map((m) => (
              <div key={m.label}>
                <p className={`text-lg font-bold ${m.color}`}>{m.value}</p>
                <p className="text-xs text-slate-500">{m.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Micro bar showing ready-to-submit ratio */}
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Ready to submit (both sections)</span>
            <span>
              {s.both_sections_complete ?? 0} of {s.total_profiles ?? 0}
            </span>
          </div>
          <ProgressBar
            percent={s.total_profiles ? ((s.both_sections_complete ?? 0) / s.total_profiles) * 100 : 0}
            color="green"
          />
        </div>
      </CardContent>
    </Card>
  );
};

export default { ProfileCompletionCard, BulkCompletionCard };

