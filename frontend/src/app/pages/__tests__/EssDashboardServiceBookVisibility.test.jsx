import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import EssDashboard from '@/portals/ess/pages/EssDashboardPage';

jest.mock('@/app/layout/Layout', () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

jest.mock('@/app/pages/system-admin/AccessDeniedPage', () => ({
  __esModule: true,
  default: ({ title, description }) => (
    <div data-testid="access-denied">
      <div>{title}</div>
      <div>{description}</div>
    </div>
  ),
}));

jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
  },
}));

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

const mockUseAuth = jest.fn();

jest.mock('@/contexts/identity_access/model/authContext', () => ({
  __esModule: true,
  useAuth: () => mockUseAuth(),
}));

const mockGetDashboard = jest.fn();
const mockGetMyProfile = jest.fn();
const mockGetMyLeaveBalances = jest.fn();
const mockGetMyServiceBook = jest.fn();
const mockListMyLeaves = jest.fn();
const mockGetMyProfileAuditTrail = jest.fn();

jest.mock('@/contexts/identity_access/model/rbac', () => ({
  __esModule: true,
  Permissions: {
    PROFILE_UPDATE_OWN_LIMITED: 'PROFILE_UPDATE_OWN_LIMITED',
    PROFILE_UPDATE_ALL: 'PROFILE_UPDATE_ALL',
    LEAVE_APPLY_OWN: 'LEAVE_APPLY_OWN',
    LEAVE_READ_OWN: 'LEAVE_READ_OWN',
  },
}));

jest.mock('@/contexts/ess/api/essApi', () => ({
  __esModule: true,
  essAPI: {
    getDashboard: (...args) => mockGetDashboard(...args),
    getMyProfile: (...args) => mockGetMyProfile(...args),
    getMyLeaveBalances: (...args) => mockGetMyLeaveBalances(...args),
    getMyServiceBook: (...args) => mockGetMyServiceBook(...args),
  },
}));

jest.mock('@/contexts/leave_attendance/api/leaveApi', () => ({
  __esModule: true,
  leaveAPI: {
    listMy: (...args) => mockListMyLeaves(...args),
  },
}));

jest.mock('@/contexts/ess/model/essProfileGateway', () => ({
  __esModule: true,
  getMyProfileAuditTrail: (...args) => mockGetMyProfileAuditTrail(...args),
  normalizeEssProfile: (profile) => profile,
}));

describe('EssDashboard service book visibility', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: { employee_id: 'EMP-1', name: 'Employee', authorities: ['EMPLOYEE'] },
      can: () => true,
    });
    mockGetDashboard.mockResolvedValue({ data: { service_book_entries: 0 } });
    mockListMyLeaves.mockResolvedValue({ data: [] });
    mockGetMyLeaveBalances.mockResolvedValue({ data: { balances: {} } });
    mockGetMyServiceBook.mockResolvedValue({ data: { available_parts: [], parts: {} } });
    mockGetMyProfileAuditTrail.mockResolvedValue([]);
  });

  test('hides Service Book action for non-regular employee', async () => {
    mockUseAuth.mockReturnValue({
      user: { employee_id: 'EMP-OUT-1', name: 'Employee', authorities: ['EMPLOYEE'] },
      can: () => true,
    });
    mockGetMyProfile.mockResolvedValue({
      data: {
        employee_id: 'EMP-OUT-1',
        full_name: 'Outsourced Employee',
        employment_type: 'OUTSOURCED',
        workflow_status: 'DRAFT',
      },
    });

    render(<EssDashboard />);

    await waitFor(() => {
      expect(screen.getByTestId('ess-dashboard')).toBeInTheDocument();
    });

    expect(screen.queryByRole('button', { name: /service book/i })).not.toBeInTheDocument();
    expect(mockGetMyServiceBook).not.toHaveBeenCalled();
  });

  test('shows Service Book stats from ESS contracts for regular employee', async () => {
    mockGetMyProfile.mockResolvedValue({
      data: {
        employee_id: 'EMP-1',
        full_name: 'Regular Employee',
        employment_type: 'REGULAR',
        workflow_status: 'DRAFT',
      },
    });
    mockGetDashboard.mockResolvedValue({
      data: {
        service_book_entries: 13,
      },
    });
    mockGetMyServiceBook.mockResolvedValue({
      data: {
        available_parts: ['I', 'II-A', 'II-B'],
        parts: {},
      },
    });

    render(<EssDashboard />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /service book/i })).toBeInTheDocument();
    });

    expect(screen.getByText(/^13$/)).toBeInTheDocument();
    expect(screen.getByText(/3 parts available/i)).toBeInTheDocument();
    expect(mockGetMyServiceBook).toHaveBeenCalledTimes(1);
  });

  test('humanizes recent profile audit action labels', async () => {
    mockGetMyProfile.mockResolvedValue({
      data: {
        employee_id: 'EMP-1',
        full_name: 'Regular Employee',
        employment_type: 'REGULAR',
        workflow_status: 'APPROVED',
      },
    });
    mockGetMyProfileAuditTrail.mockResolvedValue([
      {
        id: 'audit-1',
        action: 'update_profile_extension',
        timestamp: '2026-03-24T23:28:11.000Z',
      },
      {
        id: 'audit-2',
        action: 'approve',
        timestamp: '2026-03-24T23:30:11.000Z',
      },
    ]);

    render(<EssDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/profile updated profile extension/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/profile approved/i)).toBeInTheDocument();
    expect(screen.queryByText(/profile update_profile_extension/i)).not.toBeInTheDocument();
  });

  test('shows dashboard unavailable state when profile lookup fails', async () => {
    mockGetMyProfile.mockRejectedValue(new Error('profile unavailable'));

    render(<EssDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/dashboard unavailable/i)).toBeInTheDocument();
    });

    expect(mockGetMyServiceBook).not.toHaveBeenCalled();
  });

  test('shows access denied when the signed-in user is not linked to an employee account', async () => {
    mockUseAuth.mockReturnValue({
      user: { employee_id: '', name: 'System Administrator', authorities: ['SYSTEM_ADMIN'] },
      can: () => true,
    });

    render(<EssDashboard />);

    await waitFor(() => {
      expect(screen.getByTestId('access-denied')).toBeInTheDocument();
    });

    expect(mockGetMyProfile).not.toHaveBeenCalled();
  });
});

