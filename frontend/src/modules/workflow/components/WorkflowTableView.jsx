import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  ACTION_ICONS,
  STATUS_STYLE,
  TYPE_META,
  formatAge,
  formatWorkflowStatusLabel,
} from "@/modules/workflow/model/workQueue.constants";
import { SlaDot } from "@/modules/workflow/components/workflowQueuePrimitives";
import { ArrowUpRight, Check, Minus, Send } from "lucide-react";

/* Table view */
const WorkflowTableView = ({ items, selectedId, batchSelected, onSelect, onToggleBatch, onSelectAll, getActions, onQuickAction, actionBusy }) => {
  const allSelected = items.length > 0 && items.every((item) => batchSelected.has(item.id));
  const partiallySelected = !allSelected && items.some((item) => batchSelected.has(item.id));

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden" data-testid="work-queue-table">
      <div className="max-w-full overflow-x-auto overscroll-x-contain" data-testid="work-queue-table-scroll">
        <table className="w-full min-w-[960px] text-sm">
          <thead>
            <tr className="border-b bg-slate-50/80">
              <th className="w-10 px-3 py-2.5">
                <button
                  onClick={onSelectAll}
                  className={cn(
                    "w-4 h-4 rounded border flex items-center justify-center transition-colors",
                    allSelected || partiallySelected
                      ? "border-blue-600 bg-blue-600 text-white"
                      : "border-slate-300 hover:border-blue-400"
                  )}
                  title={allSelected ? "Deselect visible items" : "Select visible items"}
                  aria-label={allSelected ? "Deselect visible items" : "Select visible items"}
                >
                  {allSelected ? (
                    <Check className="w-2.5 h-2.5" />
                  ) : partiallySelected ? (
                    <Minus className="w-2.5 h-2.5" />
                  ) : null}
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
              const isSel = item.id === selectedId;
              const isBatch = batchSelected.has(item.id);
              const itemActions = getActions(item);
              const primary = itemActions.find((a) => a.variant !== "destructive" && !a.disabled);
              const ActionIcon = primary ? (ACTION_ICONS[primary.id] || Send) : null;

              return (
                <tr
                  key={item.id}
                  onClick={() => onSelect(item.id)}
                  className={cn(
                    "border-b cursor-pointer transition-colors",
                    isSel ? "bg-blue-50" : "hover:bg-slate-50",
                    isBatch && "bg-blue-50/60"
                  )}
                >
                  <td className="px-3 py-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); onToggleBatch(item.id); }}
                      className={cn(
                        "w-4 h-4 rounded border flex items-center justify-center transition-colors",
                        isBatch ? "bg-blue-600 border-blue-600 text-white" : "border-slate-300 hover:border-blue-400"
                      )}
                      title={isBatch ? `Deselect ${item.title}` : `Select ${item.title}`}
                      aria-label={isBatch ? `Deselect ${item.title}` : `Select ${item.title}`}
                    >
                      {isBatch && <Check className="w-2.5 h-2.5" />}
                    </button>
                  </td>
                  <td className="px-3 py-2"><SlaDot sla={item.sla} size="w-3 h-3" /></td>
                  <td className="px-3 py-2">
                    <Badge className={cn("text-[10px] gap-1", meta.badge)}>
                      <Icon className="w-3 h-3" />
                      {meta.label}
                    </Badge>
                  </td>
                  <td className="px-3 py-2">
                    <p className="font-medium text-slate-900 truncate max-w-[200px]">{item.title}</p>
                    <p className="text-xs text-slate-500 truncate max-w-[200px]">{item.subtitle}</p>
                  </td>
                  <td className="px-3 py-2">
                    <Badge className={cn("text-[10px] border", STATUS_STYLE[item.statusLabel] || "bg-slate-100 text-slate-700 border-slate-200")}>
                      {formatWorkflowStatusLabel(item.statusLabel)}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-500">{formatAge(item.ageHours)}</td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 text-xs gap-1 text-slate-600"
                        onClick={(e) => { e.stopPropagation(); onSelect(item.id); }}
                        aria-label={`Open details for ${item.title}`}
                      >
                        <ArrowUpRight className="w-3 h-3" />
                        Details
                      </Button>
                      {primary ? (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs gap-1"
                          onClick={(e) => { e.stopPropagation(); onQuickAction(item, primary.id); }}
                          disabled={actionBusy || primary.disabled}
                        >
                          {ActionIcon && <ActionIcon className="w-3 h-3" />}
                          {primary.label}
                        </Button>
                      ) : null}
                    </div>
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

export default WorkflowTableView;
