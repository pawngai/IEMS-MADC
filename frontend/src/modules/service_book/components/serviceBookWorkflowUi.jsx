import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { CheckCircle, Lock, Send, ShieldCheck } from 'lucide-react';
import { WorkflowState } from '@/modules/service_book/model/serviceBookModel';
import { WORKFLOW_STATUS_STYLES } from '@/modules/service_book/components/serviceBookLedger.constants';

const WORKFLOW_STATUS_LABELS = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  VERIFIED: 'Verified',
  APPROVED: 'Approved',
  LOCKED: 'Locked',
  REJECTED: 'Rejected',
  SUPERSEDED: 'Superseded',
};

const formatWorkflowStatusLabel = (status) => {
  const normalized = String(status || '').trim().toUpperCase();
  if (!normalized) return '';
  return WORKFLOW_STATUS_LABELS[normalized] || normalized
    .toLowerCase()
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

export function WorkflowStatusBadge({ status }) {
  if (!status) return null;
  const style = WORKFLOW_STATUS_STYLES[status] || 'bg-gray-100 text-gray-600';
  return (
    <Badge variant="outline" className={`text-xs ${style}`}>
      {formatWorkflowStatusLabel(status)}
    </Badge>
  );
}

export function WorkflowActions({ meta, onAction, disabled, can, Permissions }) {
  if (!meta?.id || !meta?.status) return null;
  const state = meta.workflow_state || meta.status;
  const buttons = [];

  if ((state === WorkflowState.DRAFT || state === WorkflowState.REJECTED) && can(Permissions.SERVICE_BOOK_ENTRY_SUBMIT)) {
    buttons.push({ label: 'Submit', action: 'submit', icon: Send, variant: 'default' });
  }
  if (state === WorkflowState.SUBMITTED && can(Permissions.SERVICE_BOOK_ENTRY_VERIFY)) {
    buttons.push({ label: 'Verify', action: 'verify', icon: ShieldCheck, variant: 'default' });
  }
  if (state === WorkflowState.VERIFIED && can(Permissions.SERVICE_BOOK_ENTRY_APPROVE)) {
    buttons.push({ label: 'Approve', action: 'approve', icon: CheckCircle, variant: 'default' });
  }
  if (state === WorkflowState.APPROVED && can(Permissions.SERVICE_BOOK_ENTRY_APPROVE)) {
    buttons.push({ label: 'Lock', action: 'lock', icon: Lock, variant: 'outline' });
  }

  if (buttons.length === 0) return null;

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {buttons.map(({ label, action, icon: Icon, variant }) => (
        <Button
          key={action}
          size="sm"
          variant={variant}
          disabled={disabled}
          onClick={() => onAction(meta.id, action)}
          className="gap-1 text-xs h-7"
        >
          <Icon className="h-3.5 w-3.5" />
          {label}
        </Button>
      ))}
    </div>
  );
}
