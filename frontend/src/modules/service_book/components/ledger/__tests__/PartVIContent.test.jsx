import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import PartVIContent from '@/modules/service_book/components/ledger/PartVIContent';

describe('PartVIContent', () => {
  test('shows the leave management handoff link for read-all users', () => {
    render(
      <PartVIContent
        employeeId="MADC-0012"
        data={{
          earned_leave_balance: 12,
          half_pay_leave_balance: 18,
          commuted_leave_balance: 4,
          leave_not_due_balance: 0,
          transactions: [],
        }}
        can={(permission) => permission === 'LEAVE_READ_ALL'}
        Permissions={{ LEAVE_READ_ALL: 'LEAVE_READ_ALL' }}
      />,
    );

    expect(screen.getByRole('link', { name: 'Open Leave Management' })).toHaveAttribute('href', '/leave?employee_id=MADC-0012');
    expect(screen.getByText(/leave balances and transactions are projected from leave/i)).toBeInTheDocument();
  });
});