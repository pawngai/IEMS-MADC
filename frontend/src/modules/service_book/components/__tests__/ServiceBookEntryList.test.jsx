import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import ServiceBookEntryList from '@/modules/service_book/components/ServiceBookEntryList';

describe('ServiceBookEntryList', () => {
  test('renders expanded readable labels for certificate parts', () => {
    render(
      <ServiceBookEntryList
        partKeys={['II-A', 'II-B']}
        activePart="II-A"
        onSelectPart={vi.fn()}
        serviceBook={{ parts_completed: [] }}
        partsInfo={{}}
        getPartData={() => null}
        completionPct={0}
      />,
    );

    expect(screen.getByRole('tab', { name: 'Part II-A: Immutable Certificates' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Part II-B: Mutable Certificates' })).toBeInTheDocument();
    expect(screen.getByText('Immutable Certificates')).toBeInTheDocument();
    expect(screen.getByText('Mutable Certificates')).toBeInTheDocument();
    expect(screen.queryByText('Immutable Certs')).not.toBeInTheDocument();
    expect(screen.queryByText('Mutable Certs')).not.toBeInTheDocument();
  });
});