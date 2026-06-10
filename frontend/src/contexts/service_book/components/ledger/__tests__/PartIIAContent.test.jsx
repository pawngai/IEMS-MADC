import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import PartIIAContent from '@/contexts/service_book/components/ledger/PartIIAContent';

describe('PartIIAContent', () => {
  test('uses read-only empty-state copy', () => {
    render(
      <PartIIAContent
        data={null}
      />,
    );

    expect(screen.getByText(/no certificates have been finalized yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/add data/i)).not.toBeInTheDocument();
  });

  test('formats read-only certificate dates for display', () => {
    render(
      <PartIIAContent
        data={{
          medical_fitness_certificate: true,
          medical_exam_date: '2026-01-10',
          medical_officer_name: 'Civil Surgeon',
          supporting_documents: [
            {
              filename: 'medical.pdf',
              original_name: 'medical.pdf',
              field_key: 'medical_fitness_certificate',
            },
          ],
          character_verification_done: true,
          character_verification_date: '2026-01-15',
        }}
      />,
    );

    expect(screen.getByText('10 Jan 2026')).toBeInTheDocument();
    expect(screen.getByText('15 Jan 2026')).toBeInTheDocument();
    expect(screen.getByText('Civil Surgeon')).toBeInTheDocument();
    expect(screen.getByText('medical.pdf')).toBeInTheDocument();
    expect(screen.queryByText('2026-01-10')).not.toBeInTheDocument();
    expect(screen.queryByText('2026-01-15')).not.toBeInTheDocument();
  });

  test('shows legacy documents separately when they are not field tagged', () => {
    render(
      <PartIIAContent
        data={{
          supporting_documents: [
            {
              filename: 'legacy-proof.pdf',
              original_name: 'legacy-proof.pdf',
            },
          ],
        }}
      />,
    );

    expect(screen.getByText(/legacy supporting documents/i)).toBeInTheDocument();
    expect(screen.getByText('legacy-proof.pdf')).toBeInTheDocument();
  });
});