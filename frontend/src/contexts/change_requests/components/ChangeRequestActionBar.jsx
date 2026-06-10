import { Button } from "@/shared/ui/button";
import { Send } from "lucide-react";
import { cn } from "@/shared/lib/utils";

const ChangeRequestActionBar = ({ submitHint, canSubmit, submitting, onCancel, onSubmit }) => {
  return (
    <div className="mt-4 flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <p className={cn("text-xs", canSubmit ? "text-green-600" : "text-muted-foreground")}>{submitHint}</p>
      <div className="flex items-center gap-2 mt-2 sm:mt-0">
        <Button variant="outline" onClick={onCancel}>Cancel</Button>
        <Button onClick={onSubmit} disabled={!canSubmit}>
          {submitting ? "Submitting" : <><Send className="mr-2 h-4 w-4" />Submit Request</>}
        </Button>
      </div>
    </div>
  );
};

export default ChangeRequestActionBar;
