import { Check, CheckCircle2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Separator } from "@/shared/ui/separator";

const WorkflowQueueBulkActions = ({ selectedCount, actionableCount, actionLabel, actionBusy, onClear, onRun }) => {
  if (!selectedCount) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-1.5 text-xs text-blue-800">
      <Check className="w-3.5 h-3.5" />
      {selectedCount} selected
      {actionableCount < selectedCount && (
        <span className="text-blue-700/80">{actionableCount} ready</span>
      )}
      <Button size="sm" variant="ghost" className="h-6 text-xs px-2" onClick={onClear}>
        Clear
      </Button>
      <Separator orientation="vertical" className="h-4" />
      <Button size="sm" className="h-6 text-xs px-2 gap-1" onClick={onRun} disabled={actionBusy || actionableCount === 0}>
        <CheckCircle2 className="w-3 h-3" />
        {actionBusy ? "Processing..." : actionLabel}
      </Button>
    </div>
  );
};

export default WorkflowQueueBulkActions;
