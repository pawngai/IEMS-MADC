import React from 'react';
import { Card, CardContent } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { WorkflowStatusBadge } from '@/contexts/service_book/components/serviceBookWorkflowUi';
import {
  EmptyPartPlaceholder,
} from '@/contexts/service_book/components/serviceBookLedgerPrimitives';

const PartVIContent = ({ data, employeeId, can, Permissions }) => {
  const canOpenLeave = Boolean(
    employeeId
      && typeof can === 'function'
      && Permissions?.LEAVE_READ_ALL
      && can(Permissions.LEAVE_READ_ALL)
  );
  const leavePath = employeeId ? `/leave?employee_id=${encodeURIComponent(employeeId)}` : '/leave';

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{data?.earned_leave_balance || 0}</div>
            <div className="text-sm text-gray-500">Earned Leave</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold text-amber-600">{data?.half_pay_leave_balance || 0}</div>
            <div className="text-sm text-gray-500">Half Pay Leave</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold text-green-600">{data?.commuted_leave_balance || 0}</div>
            <div className="text-sm text-gray-500">Commuted Leave</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold text-cyan-600">{data?.leave_not_due_balance || 0}</div>
            <div className="text-sm text-gray-500">Leave Not Due</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold text-gray-600">{data?.transactions?.length || 0}</div>
            <div className="text-sm text-gray-500">Transactions</div>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h4 className="font-medium text-gray-700">Leave Transactions</h4>
        {canOpenLeave && (
          <Button asChild variant="outline" size="sm">
            <a href={leavePath} data-testid="service-book-open-leave-link">Open Leave Management</a>
          </Button>
        )}
      </div>
      <div className="text-xs text-gray-500">
        Leave balances and transactions are projected from Leave. Manage sanctions and ledger changes there; this Service Book view remains read-only.
      </div>

      {data?.transactions?.length > 0 ? (
        <div className="space-y-2">
          {[...data.transactions]
            .sort((a, b) => {
              const dateA = a.transaction_date || '';
              const dateB = b.transaction_date || '';
              return dateB.localeCompare(dateA);
            })
            .map((txn, idx) => (
            <div key={txn._meta?.id || txn.id || idx} className={`p-3 rounded-lg border ${txn._meta?.status === 'DRAFT' || txn._meta?.workflow_state === 'DRAFT' ? 'bg-amber-50 border-amber-200' : 'bg-gray-50'}`}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900 flex items-center gap-1.5">
                    {txn.leave_type} - {txn.transaction_type}
                    {txn._meta && <WorkflowStatusBadge status={txn._meta.workflow_state || txn._meta.status} />}
                  </div>
                  <div className="text-sm text-gray-500">{txn.transaction_date}</div>
                  {txn.remarks && <div className="text-xs text-gray-400 mt-1">{txn.remarks}</div>}
                </div>
                <div className="text-right">
                  {txn.credit_days && <div className="text-green-600 font-medium">+{txn.credit_days}</div>}
                  {txn.days_availed && <div className="text-red-600 font-medium">-{txn.days_availed}</div>}
                  <div className="text-xs text-gray-400">Balance: {txn.closing_balance}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyPartPlaceholder message="No leave transactions recorded yet." />
      )}
    </div>
  );
};

export default PartVIContent;
