import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import PartIIIContent from '@/modules/service_book/components/ledger/PartIIIContent';

describe('PartIIIContent', () => {
  test('formats previous and foreign service dates for display', () => {
    render(
      <PartIIIContent
        data={{
          previous_services: [
            {
              service_from: '2014-07-01',
              service_to: '2020-12-31',
              post_held: 'Lower Division Clerk',
              organization: 'Ministry of Finance',
              purpose_of_qualification: 'Qualifying service for pension',
              qualifying_service_years: 6,
              qualifying_service_months: 6,
              qualifying_service_days: 0,
              certified_by: 'Officer',
              _meta: { status: 'DRAFT', workflow_state: 'DRAFT' },
            },
          ],
          foreign_services: [
            {
              service_from: '2021-01-15',
              service_to: '2025-06-30',
              post_held: 'Upper Division Clerk',
              employer: 'NIPFP',
              _meta: { status: 'DRAFT', workflow_state: 'DRAFT' },
            },
          ],
          verification_date: '2026-03-05',
        }}
      />,
    );

    expect(screen.getByText('1 Jul 2014')).toBeInTheDocument();
    expect(screen.getByText('31 Dec 2020')).toBeInTheDocument();
    expect(screen.getByText('15 Jan 2021')).toBeInTheDocument();
    expect(screen.getByText('30 Jun 2025')).toBeInTheDocument();
    expect(screen.getByText('5 Mar 2026')).toBeInTheDocument();
    expect(screen.getAllByText('Read-only').length).toBeGreaterThan(0);
    expect(screen.queryByText('2014-07-01')).not.toBeInTheDocument();
    expect(screen.queryByText('2025-06-30')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /add previous service/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /add foreign service/i })).not.toBeInTheDocument();
  });
});