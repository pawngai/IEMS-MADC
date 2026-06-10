import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  ACTION_ICONS,
  SLA_STYLE,
  STATUS_STYLE,
  TYPE_META,
  formatAge,
  formatWorkflowStatusLabel,
  getWorkflowStageMeta,
} from "@/contexts/workflow/model/workQueue.constants";
import { SlaDot } from "@/contexts/workflow/components/workflowQueuePrimitives";
import { ArrowUpRight, Check, Send } from "lucide-react";

/* Kanban card */
const KanbanCard = ({ item, isSelected, isBatch, onSelect, onToggleBatch, actions, onQuickAction, actionBusy }) => {
  const meta = TYPE_META[item.type] || TYPE_META.profile;
  const Icon = meta.icon;
  const primaryAction = actions.find((a) => a.variant !== "destructive" && !a.disabled);

  return (
    <div
      onClick={() => onSelect(item.id)}
      className={cn(
        "group relative rounded-xl border bg-white p-3 cursor-pointer transition-all hover:shadow-md",
        isSelected ? "border-blue-400 shadow-blue-100 shadow-md" : "border-slate-200 hover:border-slate-300",
        isBatch && "ring-2 ring-blue-400 ring-offset-1"
      )}
    >
      {/* SLA top bar */}
      <div className={cn("absolute top-0 left-3 right-3 h-0.5 rounded-b", SLA_STYLE[item.sla]?.bg || "bg-slate-200")} />

      <div className="flex items-start gap-2.5 mt-1">
        {/* Batch checkbox */}
        <button
          onClick={(e) => { e.stopPropagation(); onToggleBatch(item.id); }}
          className={cn(
            "w-4 h-4 rounded border flex-shrink-0 mt-0.5 flex items-center justify-center transition-colors",
            isBatch ? "bg-blue-600 border-blue-600 text-white" : "border-slate-300 hover:border-blue-400"
          )}
        >
          {isBatch && <Check className="w-2.5 h-2.5" />}
        </button>

        {/* Type icon */}
        <div className={cn("w-7 h-7 rounded-lg flex items-center justify-center text-white flex-shrink-0", meta.color)}>
          <Icon className="w-3.5 h-3.5" />
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-900 truncate">{item.title}</p>
          <p className="text-xs text-slate-500 truncate">{item.subtitle}</p>

          <div className="flex items-center gap-1.5 mt-2 flex-wrap">
            <Badge className={cn("text-[10px] px-1.5 py-0 border", STATUS_STYLE[item.statusLabel] || "bg-slate-100 text-slate-700 border-slate-200")}>
              {formatWorkflowStatusLabel(item.statusLabel)}
            </Badge>
            <SlaDot sla={item.sla} />
            {item.ageHours != null && (
              <span className="text-[10px] text-slate-400">{formatAge(item.ageHours)}</span>
            )}
          </div>
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between gap-2">
        <Button
          size="sm"
          variant="ghost"
          className="h-6 px-2 text-[11px] font-medium text-slate-500 gap-1"
          onClick={(e) => { e.stopPropagation(); onSelect(item.id); }}
          aria-label={`Open details for ${item.title}`}
        >
          <ArrowUpRight className="w-3 h-3" />
          Open details
        </Button>
        {primaryAction ? (
          <Button
            size="sm"
            className="h-6 text-xs px-2.5 gap-1"
            onClick={(e) => { e.stopPropagation(); onQuickAction(item, primaryAction.id); }}
            disabled={actionBusy || primaryAction.disabled}
          >
            {(() => { const AI = ACTION_ICONS[primaryAction.id]; return AI ? <AI className="w-3 h-3" /> : null; })()}
            {primaryAction.label}
          </Button>
        ) : null}
      </div>
    </div>
  );
};

/* Kanban view */
const WorkflowKanbanView = ({ columns, selectedId, batchSelected, onSelect, onToggleBatch, getActions, onQuickAction, actionBusy }) => (
  <div className="flex gap-4 overflow-x-auto pb-4 -mx-2 px-2" data-testid="work-queue-kanban">
    {columns.map(([stage, stageItems]) => (
      <div key={stage} className="flex-shrink-0 w-72 xl:w-80">
        {/* Column header */}
        <div className="flex items-start justify-between mb-3 px-1 gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
            <div className={cn("w-2 h-2 rounded-full", STATUS_STYLE[stage]?.split(" ")[0] || "bg-slate-300")} />
              <h3 className="text-sm font-semibold text-slate-700">{getWorkflowStageMeta(stage).label}</h3>
            </div>
            {getWorkflowStageMeta(stage).description ? (
              <p className="mt-1 text-[11px] text-slate-500">{getWorkflowStageMeta(stage).description}</p>
            ) : null}
          </div>
          <Badge variant="secondary" className="text-[10px]">
            {stageItems.length}
          </Badge>
        </div>

        {/* Column body */}
        <div className="space-y-2.5 max-h-[calc(100vh-340px)] overflow-y-auto pr-1">
          {stageItems.length === 0 ? (
            <div className="rounded-xl border-2 border-dashed border-slate-200 py-8 text-center text-xs text-slate-400">
              No items
            </div>
          ) : (
            stageItems.map((item) => (
              <KanbanCard
                key={item.id}
                item={item}
                isSelected={item.id === selectedId}
                isBatch={batchSelected.has(item.id)}
                onSelect={onSelect}
                onToggleBatch={onToggleBatch}
                actions={getActions(item)}
                onQuickAction={onQuickAction}
                actionBusy={actionBusy}
              />
            ))
          )}
        </div>
      </div>
    ))}
  </div>
);

export default WorkflowKanbanView;
