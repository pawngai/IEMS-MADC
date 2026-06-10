import React, { useState } from 'react';
import { DollarSign, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { WorkflowActions, WorkflowStatusBadge } from '@/contexts/service_book/components/serviceBookWorkflowUi';
import {
  DataField,
  EmptyPartPlaceholder,
} from '@/contexts/service_book/components/serviceBookLedgerPrimitives';
import PartVIIAddForm from '@/contexts/service_book/components/ledger/PartVIIAddForm';

const PartVIIContent = ({ data, employeeId, onReload, canWrite, onWorkflowAction, can, Permissions }) => {
  const [activeForm, setActiveForm] = useState(null);
  const [newEntry, setNewEntry] = useState({});
  const [isSaving, setIsSaving] = useState(false);

  const handleAdd = async () => {
    setIsSaving(false);
    toast.error('Financial benefit changes must be recorded through Service Book records.');
  };

  const toggleForm = (type) => {
    if (activeForm === type) {
      setActiveForm(null);
      setNewEntry({});
    } else {
      setActiveForm(type);
      setNewEntry({});
    }
  };

  return (
    <div className="space-y-6">
      {canWrite && (
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant={activeForm === 'ltc' ? 'default' : 'outline'} onClick={() => toggleForm('ltc')}><Plus className="h-4 w-4 mr-1" /> LTC</Button>
          <Button size="sm" variant={activeForm === 'hba' ? 'default' : 'outline'} onClick={() => toggleForm('hba')}><Plus className="h-4 w-4 mr-1" /> HBA</Button>
          <Button size="sm" variant={activeForm === 'vehicle' ? 'default' : 'outline'} onClick={() => toggleForm('vehicle')}><Plus className="h-4 w-4 mr-1" /> Vehicle</Button>
          <Button size="sm" variant={activeForm === 'festival' ? 'default' : 'outline'} onClick={() => toggleForm('festival')}><Plus className="h-4 w-4 mr-1" /> Festival</Button>
        </div>
      )}

      <PartVIIAddForm
        activeForm={activeForm}
        newEntry={newEntry}
        setNewEntry={setNewEntry}
        onAdd={handleAdd}
        onCancel={() => { setActiveForm(null); setNewEntry({}); }}
        isSaving={isSaving}
      />

      {data?.ltc_records?.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-700 mb-2 flex items-center gap-2"><DollarSign className="h-4 w-4" /> Leave Travel Concession (LTC)</h4>
          <div className="overflow-auto">
            <table className="min-w-full text-sm border">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Block Year</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Type</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Date</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">From &rarr; To</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Family</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Claimed</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Sanctioned</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Order No</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Status</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.ltc_records.map((r, i) => (
                  <tr key={r._meta?.id || r.id || i} className={`border-t ${r._meta?.status === 'DRAFT' || r._meta?.workflow_state === 'DRAFT' ? 'bg-amber-50' : ''}`}>
                    <td className="px-3 py-2 border">{r.block_year}</td>
                    <td className="px-3 py-2 border">{r.ltc_type}</td>
                    <td className="px-3 py-2 border">{r.availed_date}</td>
                    <td className="px-3 py-2 border">{r.journey_from} &rarr; {r.journey_to}</td>
                    <td className="px-3 py-2 border">{r.family_members_availed}</td>
                    <td className="px-3 py-2 border">Rs. {Number(r.amount_claimed).toLocaleString('en-IN')}</td>
                    <td className="px-3 py-2 border">Rs. {Number(r.amount_sanctioned).toLocaleString('en-IN')}</td>
                    <td className="px-3 py-2 border">{r.sanction_order_number || '-'}</td>
                    <td className="px-3 py-2 border">{r._meta && <WorkflowStatusBadge status={r._meta.workflow_state || r._meta.status} />}</td>
                    <td className="px-3 py-2 border">
                      {r._meta && onWorkflowAction && can && Permissions && (
                        <WorkflowActions meta={r._meta} onAction={onWorkflowAction} can={can} Permissions={Permissions} />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data?.hba_records?.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-700 mb-2">House Building Advance (HBA)</h4>
          <div className="space-y-2">
            {data.hba_records.map((r, i) => (
              <div key={r._meta?.id || r.id || i} className={`p-3 rounded-lg border ${r._meta?.status === 'DRAFT' || r._meta?.workflow_state === 'DRAFT' ? 'bg-amber-50 border-amber-200' : 'bg-gray-50'}`}>
                <div className="flex items-center justify-between mb-1">
                  <div className="font-medium text-gray-900">{r.purpose || 'HBA'}</div>
                  {r._meta && <WorkflowStatusBadge status={r._meta.workflow_state || r._meta.status} />}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                  <DataField label="Sanction Date" value={r.sanction_date} />
                  <DataField label="Amount" value={r.amount_sanctioned ? `Rs. ${Number(r.amount_sanctioned).toLocaleString('en-IN')}` : '-'} />
                  <DataField label="Purpose" value={r.purpose} />
                  <DataField label="Property" value={r.property_address} />
                </div>
                {r._meta && onWorkflowAction && can && Permissions && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <WorkflowActions meta={r._meta} onAction={onWorkflowAction} can={can} Permissions={Permissions} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {data?.festival_advance_records?.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-700 mb-2">Festival Advance</h4>
          <div className="space-y-2">
            {data.festival_advance_records.map((r, i) => (
              <div key={r._meta?.id || r.id || i} className={`p-3 rounded-lg border ${r._meta?.workflow_state === 'DRAFT' || r._meta?.status === 'DRAFT' ? 'bg-amber-50 border-amber-200' : 'bg-gray-50'}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium text-gray-900">{r.festival || 'Festival Advance'}</div>
                    <div className="text-sm text-gray-500">{r.advance_date} | Rs. {Number(r.amount).toLocaleString('en-IN')}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {r._meta && <WorkflowStatusBadge status={r._meta.workflow_state || r._meta.status} />}
                    <Badge variant="outline">{r.status || 'ACTIVE'}</Badge>
                  </div>
                </div>
                {r.order_number && <div className="mt-1 text-xs text-gray-400">Order: {r.order_number}</div>}
                {r._meta && onWorkflowAction && can && Permissions && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <WorkflowActions meta={r._meta} onAction={onWorkflowAction} can={can} Permissions={Permissions} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {data?.vehicle_advance_records?.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-700 mb-2">Vehicle Advance</h4>
          <div className="space-y-2">
            {data.vehicle_advance_records.map((r, i) => (
              <div key={r._meta?.id || r.id || i} className={`p-3 rounded-lg border text-sm ${r._meta?.workflow_state === 'DRAFT' || r._meta?.status === 'DRAFT' ? 'bg-amber-50 border-amber-200' : 'bg-gray-50'}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-gray-700">Vehicle Advance</span>
                  {r._meta && <WorkflowStatusBadge status={r._meta.workflow_state || r._meta.status} />}
                </div>
                {Object.entries(r).filter(([k]) => !['id', '_meta'].includes(k)).map(([k, v]) => (
                  <div key={k} className="inline-block mr-4"><span className="text-gray-500">{k.replace(/_/g, ' ')}: </span><span className="text-gray-900">{String(v)}</span></div>
                ))}
                {r._meta && onWorkflowAction && can && Permissions && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <WorkflowActions meta={r._meta} onAction={onWorkflowAction} can={can} Permissions={Permissions} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!data?.ltc_records?.length && !data?.hba_records?.length && !data?.festival_advance_records?.length && !data?.vehicle_advance_records?.length && (
        <EmptyPartPlaceholder message="No records in Part VII." />
      )}
    </div>
  );
};

export default PartVIIContent;
