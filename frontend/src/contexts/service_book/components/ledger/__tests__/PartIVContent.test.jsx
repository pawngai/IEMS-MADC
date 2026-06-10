import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import PartIVContent from '@/contexts/service_book/components/ledger/PartIVContent';

describe('PartIVContent', () => {
  test('formats event labels and dates for read-only service history entries', () => {
    render(
      <PartIVContent
        employeeId="MADC-0012"
        data={{
          entries: [
            {
              event_type: 'PROMOTION',
              period_from: '2024-06-15',
              period_to: null,
              service: 'Mizoram District Council Service',
              service_group: 'Group A',
              grade: 'Selection Grade',
              event_order_number: 'MADC/EST/2024/3456',
              event_order_date: '2024-06-15',
              remarks: 'Promoted after regular service',
              _meta: { status: 'DRAFT', workflow_state: 'DRAFT' },
            },
          ],
        }}
        can={(permission) => permission === 'SERVICE_BOOK_READ_ALL'}
        Permissions={{ SERVICE_BOOK_READ_ALL: 'SERVICE_BOOK_READ_ALL' }}
      />,
    );

    expect(screen.getAllByText('Promotion').length).toBeGreaterThan(0);
    expect(screen.getByText('Service: Mizoram District Council Service | Group: Group A | Grade: Selection Grade')).toBeInTheDocument();
    expect(screen.getByText('15 Jun 2024 - Present')).toBeInTheDocument();
    expect(screen.getByText(/MADC\/EST\/2024\/3456 \(15 Jun 2024\)/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open Service Book Records' })).toHaveAttribute('href', '/service-book/records/MADC-0012');
    expect(screen.queryByText('PROMOTION')).not.toBeInTheDocument();
    expect(screen.queryByText('2024-06-15 - Present')).not.toBeInTheDocument();
  });
});