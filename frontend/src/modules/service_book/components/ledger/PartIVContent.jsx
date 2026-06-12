import React from 'react';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { formatDisplayDate } from '@/modules/service_book/components/serviceBookPartHelpers';
import { WorkflowStatusBadge } from '@/modules/service_book/components/serviceBookWorkflowUi';
import {
  EmptyPartPlaceholder,
} from '@/modules/service_book/components/serviceBookLedgerPrimitives';

const formatEventTypeLabel = (value) => {
  const normalized = String(value || '').trim();
  if (!normalized) return 'Service Event';
  if (/[a-z]/.test(normalized)) return normalized;
  return normalized
    .toLowerCase()
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

const formatClassificationLine = (entry) => {
  const parts = [
    entry?.service ? `Service: ${entry.service}` : null,
    entry?.service_group ? `Group: ${entry.service_group}` : null,
    entry?.grade ? `Grade: ${entry.grade}` : null,
  ].filter(Boolean);

  return parts.join(' | ');
};

const PartIVContent = ({
  data,
  employeeId,
  can,
  Permissions,
}) => {
  const canOpenRecords = Boolean(
    employeeId
      && typeof can === 'function'
      && Permissions?.SERVICE_BOOK_READ_ALL
      && can(Permissions.SERVICE_BOOK_READ_ALL)
  );
  const recordsPath = employeeId ? `/service-book/records/${encodeURIComponent(employeeId)}` : '/service-book/records';

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h4 className="font-medium text-gray-700">Service History Entries</h4>
        {canOpenRecords && (
          <Button asChild variant="outline" size="sm">
            <a href={recordsPath} data-testid="service-book-open-records-link">Open Service Book Records</a>
          </Button>
        )}
      </div>
      <div className="text-xs text-gray-500">
        Service history is projected from Service Book records. Record, review, and workflow actions happen there; this Service Book view remains read-only.
      </div>

      {data?.entries?.length > 0 ? (
        <div className="space-y-2">
          {data.entries.map((entry, idx) => (
            <div key={entry._meta?.id || entry.id || idx} className={`p-3 rounded-lg border ${entry._meta?.status === 'DRAFT' || entry._meta?.workflow_state === 'DRAFT' ? 'bg-amber-50 border-amber-200' : 'bg-gray-50'}`}>
              {formatClassificationLine(entry) && (
                <div className="mb-2 text-xs font-medium text-gray-600">{formatClassificationLine(entry)}</div>
              )}
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-medium text-gray-900">{entry.post_held || formatEventTypeLabel(entry.event_type)}</div>
                  <div className="text-sm text-gray-600">{entry.office_station || entry.reason || 'Projected from Service Book records'}</div>
                </div>
                <div className="flex items-center gap-1.5">
                  <Badge variant="outline">{formatEventTypeLabel(entry.event_type)}</Badge>
                  {entry._meta && <WorkflowStatusBadge status={entry._meta.workflow_state || entry._meta.status} />}
                </div>
              </div>
              <div className="mt-2 text-sm text-gray-500 flex gap-4">
                <span>{formatDisplayDate(entry.period_from)} - {entry.period_to ? formatDisplayDate(entry.period_to) : 'Present'}</span>
                {entry.basic_pay && <span>Rs. {Number(entry.basic_pay).toLocaleString('en-IN')}</span>}
                {entry.suspension_date && <span>Suspension: {formatDisplayDate(entry.suspension_date)}</span>}
              </div>
              {entry.event_order_number && (
                <div className="mt-1 text-xs text-gray-400">
                  Order: {entry.event_order_number}
                  {entry.event_order_date ? ` (${formatDisplayDate(entry.event_order_date)})` : ''}
                </div>
              )}
              {entry.remarks && (
                <div className="mt-1 text-xs text-gray-500">Remarks: {entry.remarks}</div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyPartPlaceholder message="No service history entries yet." />
      )}
    </div>
  );
};

export default PartIVContent;
