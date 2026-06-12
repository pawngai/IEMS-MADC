import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import PartIContent from '@/modules/service_book/components/ledger/PartIContent';

describe('PartIContent', () => {
  test('uses read-only empty-state copy', () => {
    render(
      <PartIContent
        data={null}
        casteCategoryOptions={[]}
      />,
    );

    expect(screen.getByText(/no bio-data has been finalized yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/add data/i)).not.toBeInTheDocument();
  });

  test('shows profile-synced signature and thumb sections in read-only biodata', () => {
    render(
      <PartIContent
        data={{
          signature_url: 'https://example.test/signature.png',
          thumb_impression_url: 'https://example.test/thumb.png',
          attesting_officer_name: 'Approving Officer',
        }}
        casteCategoryOptions={[]}
      />,
    );

    expect(screen.getByText('Signature')).toBeInTheDocument();
    expect(screen.getByText('On file')).toBeInTheDocument();
    expect(screen.getByText('Approving Officer')).toBeInTheDocument();
  });

  test('formats read-only biodata values into readable labels', () => {
    render(
      <PartIContent
        data={{
          name_in_block_letters: 'RAHUL SHARMA',
          employee_code: 'EMP-2026-R0363',
          parent_name: 'RAJESH KUMAR SHARMA',
          spouse_name: 'ANITA SHARMA',
          marital_status: 'MARRIED',
          nationality: 'Indian',
          caste_category: 'GEN',
          date_of_birth_christian: '1990-05-15',
        }}
        casteCategoryOptions={[
          { value: 'GEN', label: 'General' },
        ]}
      />,
    );

    expect(screen.getByText('Rahul Sharma')).toBeInTheDocument();
    expect(screen.getByText('Rajesh Kumar Sharma')).toBeInTheDocument();
    expect(screen.getByText('Anita Sharma')).toBeInTheDocument();
    expect(screen.getByText('Married')).toBeInTheDocument();
    expect(screen.getByText('General')).toBeInTheDocument();
    expect(screen.getByText('15 May 1990')).toBeInTheDocument();
    expect(screen.queryByText('RAHUL SHARMA')).not.toBeInTheDocument();
    expect(screen.queryByText('GEN')).not.toBeInTheDocument();
    expect(screen.queryByText('1990-05-15')).not.toBeInTheDocument();
  });
});