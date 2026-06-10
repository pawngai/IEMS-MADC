import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/shared/ui/tooltip";
import { SLA_STYLE } from "@/contexts/workflow/model/workQueue.constants";

/* Mini stat card */
export const MiniStat = ({ label, value, icon: Icon, tone = "text-slate-900" }) => (
  <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 flex items-center gap-3">
    <div className={cn("w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center", tone)}>
      <Icon className="w-4 h-4" />
    </div>
    <div>
      <p className={cn("text-lg font-semibold leading-none", tone)}>{value}</p>
      <p className="text-[11px] text-slate-500 mt-0.5">{label}</p>
    </div>
  </div>
);

/* SLA dot */
export const SlaDot = ({ sla, size = "w-2.5 h-2.5" }) => {
  const s = SLA_STYLE[sla] || SLA_STYLE.NONE;
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={cn("inline-block rounded-full flex-shrink-0", size, s.bg)} />
      </TooltipTrigger>
      <TooltipContent side="top" className="text-xs">
        SLA: {s.label}
      </TooltipContent>
    </Tooltip>
  );
};
