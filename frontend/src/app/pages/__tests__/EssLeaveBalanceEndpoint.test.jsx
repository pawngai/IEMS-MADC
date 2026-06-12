import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import EssLeavePage from '@/modules/leave_attendance/pages/EssLeavePage';

jest.mock('@/app/layout/Layout', () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

const mockUseAuth = jest.fn();

jest.mock('@/modules/identity_access/model/authContext', () => ({
  __esModule: true,
  useAuth: () => mockUseAuth(),
}));

const mockGetMyProfile = jest.fn();
const mockGetMyLeaveBalances = jest.fn();

jest.mock('@/modules/ess/api/essApi', () => ({
  __esModule: true,
  essAPI: {
    getMyProfile: (...args) => mockGetMyProfile(...args),
    getMyLeaveBalances: (...args) => mockGetMyLeaveBalances(...args),
  },
}));

const mockListMy = jest.fn();
const mockApply = jest.fn();
const mockCancel = jest.fn();
const mockLegacyGetBalances = jest.fn();

jest.mock('@/modules/leave_attendance/api/leaveApi', () => ({
  __esModule: true,
  leaveAPI: {
    listMy: (...args) => mockListMy(...args),
    apply: (...args) => mockApply(...args),
    cancel: (...args) => mockCancel(...args),
    getBalances: (...args) => mockLegacyGetBalances(...args),
  },
}));

describe('EssLeavePage balance endpoint source', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: { employee_id: 'EMP-1', name: 'Employee 1' },
      can: () => true,
    });
    mockGetMyProfile.mockResolvedValue({
      data: {
        employee_id: 'EMP-1',
        full_name: 'Employee 1',
        employment_type: 'REGULAR',
      },
    });
    mockGetMyLeaveBalances.mockResolvedValue({
      data: {
        balances: {
          EL: { leave_code: 'EL', description: 'Earned Leave', available_days: 10 },
        },
      },
    });
    mockListMy.mockResolvedValue({ data: [] });
  });

  test('uses ESS leave-balance endpoint and not legacy leave balance endpoint', async () => {
    render(<EssLeavePage />);

    await waitFor(() => {
      expect(mockGetMyLeaveBalances).toHaveBeenCalledTimes(1);
    });

    expect(mockLegacyGetBalances).not.toHaveBeenCalled();
  });

  test('hides apply form for role users even when apply permission is present', async () => {
    mockUseAuth.mockReturnValue({
      user: {
        employee_id: 'EST-001',
        name: 'Approving Authority',
        authorities: ['APPROVING_AUTHORITY'],
      },
      can: () => true,
    });

    render(<EssLeavePage />);

    await waitFor(() => {
      expect(mockGetMyLeaveBalances).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByText(/employee self-service only/i)).toBeInTheDocument();
    expect(screen.getByText(/leave can only be applied from an employee self-service account/i)).toBeInTheDocument();
    expect(screen.queryByText(/^Leave Type \*$/i)).not.toBeInTheDocument();
  });
});
