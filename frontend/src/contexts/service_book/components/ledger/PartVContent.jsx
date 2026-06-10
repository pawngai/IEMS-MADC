import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/shared/ui/button';
import { Card, CardContent } from '@/shared/ui/card';
import { formatDisplayDate } from '@/contexts/service_book/components/serviceBookPartHelpers';
import { WorkflowActions, WorkflowStatusBadge } from '@/contexts/service_book/components/serviceBookWorkflowUi';
import {
  CheckboxField,
  EmptyPartPlaceholder,
  FormField,
} from '@/contexts/service_book/components/serviceBookLedgerPrimitives';

const formatPurposeLabel = (value) => {
  const normalized = String(value || '').trim();
  if (!normalized) return '-';
  if (/[a-z]/.test(normalized)) return normalized;
  return normalized
    .toLowerCase()
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

const PartVContent = ({ data, employeeId, onReload, canWrite, onWorkflowAction, can, Permissions }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newEntry, setNewEntry] = useState({});
  const [isSaving, setIsSaving] = useState(false);

  const handleAddVerification = async () => {
    setIsSaving(false);
    toast.error('Service verification changes must be recorded through Service Book records.');
  };

  const total = data?.total_verified_service || {};

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h4 className="font-medium text-gray-700">Service Verification Entries</h4>
        {canWrite && (
          <Button size="sm" onClick={() => setShowAddForm(!showAddForm)}>
            <Plus className="h-4 w-4 mr-1" /> Add Verification
          </Button>
        )}
      </div>

      {showAddForm && (
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField label="Period From" type="date" value={newEntry.period_from} onChange={(v) => setNewEntry({ ...newEntry, period_from: v })} />
              <FormField label="Period To" type="date" value={newEntry.period_to} onChange={(v) => setNewEntry({ ...newEntry, period_to: v })} />
              <FormField label="Post Held" value={newEntry.post_held} onChange={(v) => setNewEntry({ ...newEntry, post_held: v })} />
              <FormField label="Purpose of Qualification" value={newEntry.purpose_of_qualification} onChange={(v) => setNewEntry({ ...newEntry, purpose_of_qualification: v })} />
              <CheckboxField label="Verified" checked={newEntry.verified} onChange={(v) => setNewEntry({ ...newEntry, verified: v })} />
              <FormField label="Certifying Officer" value={newEntry.certifying_officer} onChange={(v) => setNewEntry({ ...newEntry, certifying_officer: v })} />
              <FormField label="Certification Date" type="date" value={newEntry.certification_date} onChange={(v) => setNewEntry({ ...newEntry, certification_date: v })} />
            </div>
            <FormField label="Remarks" value={newEntry.remarks} onChange={(v) => setNewEntry({ ...newEntry, remarks: v })} />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAddForm(false)}>Cancel</Button>
              <Button onClick={handleAddVerification} disabled={isSaving}>
                {isSaving ? 'Adding...' : 'Add Verification'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {data?.verification_entries?.length > 0 ? (
        <>
          <div className="overflow-auto">
            <table className="min-w-full text-sm border">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">S.No.</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">From</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">To</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Post Held</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Purpose</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Verified</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Certifying Officer</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Cert. Date</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Remarks</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Status</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.verification_entries.map((v, i) => (
                  <tr key={v._meta?.id || i} className={`border-t ${v._meta?.status === 'DRAFT' || v._meta?.workflow_state === 'DRAFT' ? 'bg-amber-50' : ''}`}>
                    <td className="px-3 py-2 border">{i + 1}</td>
                    <td className="px-3 py-2 border">{formatDisplayDate(v.period_from)}</td>
                    <td className="px-3 py-2 border">{v.period_to ? formatDisplayDate(v.period_to) : '-'}</td>
                    <td className="px-3 py-2 border">{formatPurposeLabel(v.post_held)}</td>
                    <td className="px-3 py-2 border">{formatPurposeLabel(v.purpose_of_qualification)}</td>
                    <td className="px-3 py-2 border">{v.verified ? 'Yes' : 'No'}</td>
                    <td className="px-3 py-2 border">{v.certifying_officer || '-'}</td>
                    <td className="px-3 py-2 border">{v.certification_date ? formatDisplayDate(v.certification_date) : '-'}</td>
                    <td className="px-3 py-2 border max-w-[200px] truncate" title={v.remarks || '-'}>{v.remarks || '-'}</td>
                    <td className="px-3 py-2 border">{v._meta && <WorkflowStatusBadge status={v._meta.workflow_state || v._meta.status} />}</td>
                    <td className="px-3 py-2 border">
                      {v._meta && onWorkflowAction && can && Permissions && (
                        <WorkflowActions meta={v._meta} onAction={onWorkflowAction} can={can} Permissions={Permissions} />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="text-sm text-gray-600">Total Verified Service: {total.years || 0}y {total.months || 0}m {total.days || 0}d</div>
        </>
      ) : (
        <EmptyPartPlaceholder message="No verification entries yet." />
      )}
    </div>
  );
};

export default PartVContent;
