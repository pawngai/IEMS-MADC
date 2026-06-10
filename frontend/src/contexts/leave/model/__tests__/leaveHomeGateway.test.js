import { describe, expect, test, vi } from 'vitest';

const mockGetPendingActions = vi.fn();

vi.mock('@/contexts/leave/api/leaveApi', () => ({
  leaveAPI: {
    getPendingActions: (...args) => mockGetPendingActions(...args),
    listMy: vi.fn(),
  },
}));

import { fetchPendingLeaveActions } from '@/contexts/leave/model/leaveHomeGateway';

describe('fetchPendingLeaveActions', () => {
  test('requests submitted and recommended statuses for full leave workflow access', async () => {
    mockGetPendingActions.mockResolvedValue({ data: [] });

    await fetchPendingLeaveActions({ canRecommend: true, canSanction: true });

    expect(mockGetPendingActions).toHaveBeenCalledWith({ statuses: ['SUBMITTED', 'RECOMMENDED'] });
  });

  test('requests only submitted status for recommend-only access', async () => {
    mockGetPendingActions.mockResolvedValue({ data: [] });

    await fetchPendingLeaveActions({ canRecommend: true, canSanction: false });

    expect(mockGetPendingActions).toHaveBeenCalledWith({ statuses: ['SUBMITTED'] });
  });

  test('requests no statuses when the user has no leave workflow permissions', async () => {
    mockGetPendingActions.mockResolvedValue({ data: [] });

    await fetchPendingLeaveActions({ canRecommend: false, canSanction: false });

    expect(mockGetPendingActions).toHaveBeenCalledWith({ statuses: [] });
  });
});