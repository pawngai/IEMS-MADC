import React from 'react';
import { Building } from 'lucide-react';
import { Card, CardContent } from '@/shared/ui/card';
import { formatDisplayDate } from '@/contexts/service_book/components/serviceBookPartHelpers';
import { WorkflowStatusBadge } from '@/contexts/service_book/components/serviceBookWorkflowUi';
import {
  DataField,
  EmptyPartPlaceholder,
} from '@/contexts/service_book/components/serviceBookLedgerPrimitives';

const PartIIIContent = ({ data }) => {
  const svc = data?.total_previous_qualifying_service || {};
  return (
    <div className="space-y-6">
      <div>
        <div className="flex justify-between items-center mb-2">
          <h4 className="font-medium text-gray-700 flex items-center gap-2"><Building className="h-4 w-4" /> Previous Qualifying Service</h4>
        </div>

        {data?.previous_services?.length > 0 ? (
          <>
            <div className="overflow-auto">
              <table className="min-w-full text-sm border">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">From</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">To</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Post Held</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Organization</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Purpose</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Qualifying Period</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Certified By</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Status</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.previous_services.map((s, i) => (
                    <tr key={s._meta?.id || i} className={`border-t ${s._meta?.status === 'DRAFT' || s._meta?.workflow_state === 'DRAFT' ? 'bg-amber-50' : ''}`}>
                      <td className="px-3 py-2 border">{formatDisplayDate(s.service_from)}</td>
                      <td className="px-3 py-2 border">{formatDisplayDate(s.service_to)}</td>
                      <td className="px-3 py-2 border">{s.post_held}</td>
                      <td className="px-3 py-2 border">{s.organization}</td>
                      <td className="px-3 py-2 border">{s.purpose_of_qualification}</td>
                      <td className="px-3 py-2 border">{s.qualifying_service_years}y {s.qualifying_service_months}m {s.qualifying_service_days}d</td>
                      <td className="px-3 py-2 border">{s.certified_by || '-'}</td>
                      <td className="px-3 py-2 border">{s._meta && <WorkflowStatusBadge status={s._meta.workflow_state || s._meta.status} />}</td>
                      <td className="px-3 py-2 border text-gray-500">Read-only</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-2 text-sm text-gray-600">Total Qualifying Service: {svc.years || 0}y {svc.months || 0}m {svc.days || 0}d</div>
          </>
        ) : (
          <EmptyPartPlaceholder message="No previous qualifying service records." />
        )}
      </div>

      <div>
        <div className="flex justify-between items-center mb-2">
          <h4 className="font-medium text-gray-700">Foreign Service / Deputation</h4>
        </div>

        {data?.foreign_services?.length > 0 ? (
          <div className="overflow-auto">
            <table className="min-w-full text-sm border">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">From</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">To</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Post</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Employer</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Remarks</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Status</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 border">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.foreign_services.map((s, i) => (
                  <tr key={s._meta?.id || i} className={`border-t ${s._meta?.status === 'DRAFT' || s._meta?.workflow_state === 'DRAFT' ? 'bg-amber-50' : ''}`}>
                    <td className="px-3 py-2 border">{formatDisplayDate(s.service_from)}</td>
                    <td className="px-3 py-2 border">{formatDisplayDate(s.service_to)}</td>
                    <td className="px-3 py-2 border">{s.post_held}</td>
                    <td className="px-3 py-2 border">{s.employer}</td>
                    <td className="px-3 py-2 border">{s.remarks || '-'}</td>
                    <td className="px-3 py-2 border">{s._meta && <WorkflowStatusBadge status={s._meta.workflow_state || s._meta.status} />}</td>
                    <td className="px-3 py-2 border text-gray-500">Read-only</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyPartPlaceholder message="No foreign service records." />
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm pt-2 border-t">
        <DataField label="Verified" value={data?.verified ? 'Yes' : 'No'} />
        <DataField label="Verified By" value={data?.verified_by} />
        <DataField label="Verification Date" value={data?.verification_date ? formatDisplayDate(data.verification_date) : null} />
      </div>
    </div>
  );
};

export default PartIIIContent;
