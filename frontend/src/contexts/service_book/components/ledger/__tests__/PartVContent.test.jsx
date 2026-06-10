import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import PartVContent from '@/contexts/service_book/components/ledger/PartVContent';

describe('PartVContent', () => {
  test('formats verification dates and uppercase service labels for display', () => {
    render(
      <PartVContent
        data={{
          verification_entries: [
            {
              period_from: '2025-01-01',
              period_to: '2025-01-01',
              post_held: 'PAY',
              purpose_of_qualification: 'FOREIGN SERVICE / DEPUTATION',
              verified: false,
              certification_date: '2025-02-01',
              remarks: 'Annual increment for FY 2025-26',
              _meta: { status: 'DRAFT', workflow_state: 'DRAFT' },
            },
          ],
        }}
        employeeId="EMP-100"
        onReload={vi.fn()}
        canWrite={false}
        onWorkflowAction={vi.fn()}
        can={() => false}
        Permissions={{}}
      />,
    );

    expect(screen.getAllByText('Pay').length).toBeGreaterThan(0);
    expect(screen.getByText('Foreign Service / Deputation')).toBeInTheDocument();
    expect(screen.getAllByText('1 Jan 2025').length).toBeGreaterThan(0);
    expect(screen.getByText('1 Feb 2025')).toBeInTheDocument();
    expect(screen.queryByText('PAY')).not.toBeInTheDocument();
    expect(screen.queryByText('FOREIGN SERVICE / DEPUTATION')).not.toBeInTheDocument();
    expect(screen.queryByText('2025-02-01')).not.toBeInTheDocument();
  });
});