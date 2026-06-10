import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import PartIIBContent from '@/contexts/service_book/components/ledger/PartIIBContent';

describe('PartIIBContent', () => {
  test('renders the improved summary in read-only mode', () => {
    render(
      <PartIIBContent
        data={{
          bank_account_number: '222233334444',
          bank_name: 'State Cooperative Bank',
          bank_ifsc: 'STCB0002200',
          family_members: [{ name: 'Nominee Person', relationship: 'Spouse', date_of_birth: '1992-03-01' }],
          family_declaration_date: '2026-03-01',
        }}
      />,
    );

    expect(screen.getByText('Records Snapshot')).toBeInTheDocument();
    expect(screen.getByText('Nomination Categories')).toBeInTheDocument();
    expect(screen.getByText('Declared on 1 Mar 2026')).toBeInTheDocument();
    expect(screen.getByText('1 Mar 1992')).toBeInTheDocument();
    expect(screen.queryByText('2026-03-01')).not.toBeInTheDocument();
    expect(screen.queryByText('1992-03-01')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /PCF Nomination/i })).not.toBeInTheDocument();
  });

  test('renders nomination cards with nominee details', () => {
    render(
      <PartIIBContent
        data={{
          pcf_nomination: [
            {
              pcf_account_number: 'PCF-001',
              pcf_nomination_date: '2026-03-16',
              pcf_nomination: [{ name: 'Primary Nominee', relationship: 'Spouse', share_percent: 100 }],
              _meta: { id: 'nom-1', status: 'DRAFT', workflow_state: 'DRAFT' },
            },
          ],
        }}
      />,
    );

    expect(screen.getByText('Primary Nominee')).toBeInTheDocument();
    expect(screen.getByText('Share 100%')).toBeInTheDocument();
    expect(screen.getByText('PCF PCF-001')).toBeInTheDocument();
    expect(screen.getByText('16 Mar 2026')).toBeInTheDocument();
    expect(screen.queryByText('2026-03-16')).not.toBeInTheDocument();
  });
});