import { mapServerAction } from '@/contexts/notifications/pages/EssNotificationsPage';

describe('EssNotificationsPage server action mapping', () => {
  test('maps backend action_url for leave route to current frontend route', () => {
    expect(mapServerAction({ action_url: '/ess/my-leaves' })).toEqual({
      label: 'Open Leave',
      to: '/ess/leave',
    });
  });

  test('keeps explicit action object from backend', () => {
    expect(mapServerAction({ action: { label: 'Open Profile', to: '/ess/profile' } })).toEqual({
      label: 'Open Profile',
      to: '/ess/profile',
    });
  });

  test('returns null when no action payload is present', () => {
    expect(mapServerAction({})).toBeNull();
  });
});
