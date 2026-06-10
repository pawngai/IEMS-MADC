import { Check, Send } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { cn } from "@/shared/lib/utils";
import {
  ACTION_ICONS,
  formatAge,
  SLA_STYLE,
  STATUS_STYLE,
  TYPE_META,
} from "@/contexts/workflow/model/workQueue.constants";

const SlaDot = ({ sla, size = "w-3 h-3" }) => {
  const style = SLA_STYLE[sla] || SLA_STYLE.NONE;
  return <span className={cn("inline-block rounded-full flex-shrink-0", size, style.bg)} title={`SLA: ${style.label}`} />;
};

const WorkflowQueueTable = ({
  items,
  selectedId,
  batchSelected,
  onSelect,
  onToggleBatch,
  onSelectAll,
  getActions,
  onQuickAction,
  actionBusy,
}) => {
  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden" data-testid="work-queue-table">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-slate-50/80">
              <th className="w-10 px-3 py-2.5">
                <button
                  onClick={onSelectAll}
                  className="w-4 h-4 rounded border border-slate-300 hover:border-blue-400 flex items-center justify-center"
                  title="Select all"
                >
                  {batchSelected.size === items.length && items.length > 0 && <Check className="w-2.5 h-2.5 text-blue-600" />}
                </button>
              </th>
              <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">SLA</th>
              <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Type</th>
              <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Name</th>
              <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
              <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Age</th>
              <th className="px-3 py-2.5 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const meta = TYPE_META[item.type] || TYPE_META.profile;
              const Icon = meta.icon;
              const isSelected = item.id === selectedId;
              const isBatchSelected = batchSelected.has(item.id);
              const itemActions = getActions(item);
              const primaryAction = itemActions.find((action) => action.variant !== "destructive" && !action.disabled);
              const ActionIcon = primaryAction ? ACTION_ICONS[primaryAction.id] || Send : null;

              return (
                <tr
                  key={item.id}
                  onClick={() => onSelect(item.id)}
                  className={cn(
                    "border-b cursor-pointer transition-colors",
                    isSelected ? "bg-blue-50" : "hover:bg-slate-50",
                    isBatchSelected && "bg-blue-50/60"
                  )}
                >
                  <td className="px-3 py-2">
                    <button
                      onClick={(event) => {
                        event.stopPropagation();
                        onToggleBatch(item.id);
                      }}
                      className={cn(
                        "w-4 h-4 rounded border flex items-center justify-center",
                        isBatchSelected ? "bg-blue-600 border-blue-600 text-white" : "border-slate-300"
                      )}
                    >
                      {isBatchSelected && <Check className="w-2.5 h-2.5" />}
                    </button>
                  </td>
                  <td className="px-3 py-2"><SlaDot sla={item.sla} /></td>
                  <td className="px-3 py-2">
                    <Badge className={cn("text-[10px] gap-1", meta.badge)}>
                      <Icon className="w-3 h-3" />
                      {meta.label}
                    </Badge>
                  </td>
                  <td className="px-3 py-2">
                    <p className="font-medium text-slate-900 truncate max-w-[200px]">{item.title}</p>
                    <p className="text-xs text-slate-500 truncate max-w-[200px]">
                      {item.subtitle}
                      {item.id && item.type === "service" && (
                        <span className="ml-1 text-slate-400 font-mono">#{item.id.split(":").pop().slice(-6)}</span>
                      )}
                    </p>
                  </td>
                  <td className="px-3 py-2">
                    <Badge className={cn("text-[10px] border", STATUS_STYLE[item.statusLabel] || "bg-slate-100 text-slate-700 border-slate-200")}>
                      {item.statusLabel}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-500">{formatAge(item.ageHours)}</td>
                  <td className="px-3 py-2 text-right">
                    {primaryAction ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs gap-1"
                        onClick={(event) => {
                          event.stopPropagation();
                          onQuickAction(item, primaryAction.id);
                        }}
                        disabled={actionBusy || primaryAction.disabled}
                      >
                        {ActionIcon && <ActionIcon className="w-3 h-3" />}
                        {primaryAction.label}
                      </Button>
                    ) : (
                      <span className="text-xs text-slate-400">View</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default WorkflowQueueTable;
