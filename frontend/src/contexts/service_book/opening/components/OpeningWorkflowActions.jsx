import { Save, Send, ShieldCheck, Stamp } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";

const OpeningWorkflowActions = ({
  completion,
  permissions,
  saving,
  acting,
  remarks,
  onRemarksChange,
  onSave,
  onSubmit,
  onVerify,
  onApprove,
}) => {
  return (
    <div className="rounded-md border bg-white p-4 space-y-3" data-testid="opening-workflow-actions">
      <Textarea
        value={remarks}
        onChange={(event) => onRemarksChange(event.target.value)}
        placeholder="Workflow remarks"
        aria-label="Workflow remarks"
        disabled={Boolean(acting)}
      />
      <div className="flex flex-wrap items-center gap-2">
        {permissions.canUpdate && (
          <Button variant="outline" className="gap-2" onClick={onSave} disabled={saving}>
            <Save className="w-4 h-4" />
            {saving ? "Saving..." : "Save Draft"}
          </Button>
        )}
        {permissions.canSubmit && (
          <Button
            className="gap-2"
            onClick={onSubmit}
            disabled={!completion.complete || Boolean(acting)}
            data-testid="opening-submit-btn"
          >
            <Send className="w-4 h-4" />
            Submit
          </Button>
        )}
        {permissions.canVerify && (
          <Button className="gap-2" onClick={onVerify} disabled={Boolean(acting)} data-testid="opening-verify-btn">
            <ShieldCheck className="w-4 h-4" />
            Verify
          </Button>
        )}
        {permissions.canApprove && (
          <Button className="gap-2" onClick={onApprove} disabled={Boolean(acting)} data-testid="opening-approve-btn">
            <Stamp className="w-4 h-4" />
            Approve
          </Button>
        )}
      </div>
      {!completion.complete && permissions.canSubmit && (
        <p className="text-xs text-slate-500">Submit is enabled after all required opening parts are complete.</p>
      )}
    </div>
  );
};

export default OpeningWorkflowActions;
