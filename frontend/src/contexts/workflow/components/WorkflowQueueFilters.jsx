import { Search } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { Input } from "@/shared/ui/input";
import { SLA_STYLE } from "@/contexts/workflow/model/workQueue.constants";

const SLA_FILTER_OPTIONS = [
  { tier: "ALL", label: "All", description: "All SLA statuses" },
  { tier: "RED", label: "Overdue", description: "Overdue items, more than 72 hours old" },
  { tier: "YELLOW", label: "Aging", description: "Aging items, between 24 and 72 hours old" },
  { tier: "GREEN", label: "On Time", description: "On-time items, less than 24 hours old" },
];

const FilterPill = ({ active, onClick, label, color = "bg-slate-100 text-slate-700" }) => (
  <button
    type="button"
    onClick={onClick}
    aria-pressed={active}
    className={cn(
      "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-all border",
      active ? "ring-2 ring-offset-1 ring-blue-400 border-blue-300 bg-blue-50 text-blue-800" : `border-slate-200 hover:bg-slate-50 ${color}`
    )}
  >
    {label}
  </button>
);

const WorkflowQueueFilters = ({
  query,
  onQueryChange,
  typeFilter,
  onTypeFilterChange,
  slaFilter,
  onSlaFilterChange,
  typeOptions,
}) => {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
      <div className="relative w-full lg:max-w-md lg:flex-1">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <Input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search queue items"
          aria-label="Search work queue items"
          className="pl-9 h-9"
          data-testid="work-queue-search"
        />
      </div>

      <div className="flex w-full gap-1.5 flex-wrap lg:w-auto" role="group" aria-label="Work item type filters">
        {typeOptions.map(({ value, label, color }) => (
          <FilterPill
            key={value}
            active={typeFilter === value}
            onClick={() => onTypeFilterChange(value)}
            label={label}
            color={color}
          />
        ))}
      </div>

      <div className="flex w-full gap-1.5 flex-wrap lg:w-auto" role="group" aria-label="SLA status filters">
        {SLA_FILTER_OPTIONS.map(({ tier, label, description }) => (
          <button
            key={tier}
            type="button"
            onClick={() => onSlaFilterChange(tier)}
            aria-label={description}
            aria-pressed={slaFilter === tier}
            className={cn(
              "inline-flex h-8 items-center gap-1.5 rounded-full border px-3 text-xs font-medium transition-all",
              slaFilter === tier ? "ring-2 ring-offset-1 ring-slate-400 border-slate-300 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
              tier === "ALL"
                ? ""
                : `${SLA_STYLE[tier].border}`
            )}
            title={description}
          >
            {tier === "ALL" ? (
              <span className="text-[11px] font-semibold">All</span>
            ) : (
              <>
                <span
                  aria-hidden="true"
                  className={cn(
                    "h-2.5 w-2.5 rounded-full",
                    SLA_STYLE[tier].bg,
                  )}
                />
                <span>{label}</span>
              </>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export default WorkflowQueueFilters;
