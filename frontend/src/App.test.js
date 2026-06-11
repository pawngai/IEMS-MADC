/**
 * App.js smoke test — verifies the app module can be imported and
 * the top-level component renders without crashing.
 *
 * react-router-dom is auto-mocked via src/__mocks__/react-router-dom.js
 * because v7 ships as ESM which Jest cannot resolve natively.
 */
import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('@/platform/api/httpClient', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } } },
  apiClient: { get: jest.fn(), post: jest.fn(), interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } } },
  getToken: () => null,
  getRefresh: () => null,
  getUser: () => null,
  setTokens: jest.fn(),
  clearTokens: jest.fn(),
}));

jest.mock('@/contexts/identity_access/api/authApi', () => ({
  __esModule: true,
  authAPI: { getMe: jest.fn().mockRejectedValue(new Error('no token')), getModuleAccess: jest.fn(), login: jest.fn() },
}));

jest.mock('@/contexts/ess/api/essApi', () => ({
  __esModule: true,
  essAPI: { getDashboard: jest.fn(), getMyProfile: jest.fn() },
}));

jest.mock('@/platform/permissions', () => ({
  __esModule: true,
  Permissions: {},
  Authorities: {},
  DEPARTMENT_SCOPED_AUTHORITIES: ['DEPT_DATA_ENTRY', 'HOD'],
  GLOBAL_IDENTITY_DATA_ENTRY_AUTHORITIES: ['GLOBAL_DATA_ENTRY', 'DEALING_ASSISTANT'],
  DEPARTMENT_IDENTITY_DATA_ENTRY_AUTHORITIES: ['DEPT_DATA_ENTRY'],
  hasPermission: () => false,
  hasAuthority: () => false,
  hasAnyPermission: () => false,
  hasAnyAuthority: () => false,
  normalizeWorkflowStage: (stage) => stage,
}));

// Mock auth context
jest.mock('@/contexts/identity_access', () => ({
  __esModule: true,
  AuthProvider: ({ children }) => <div>{children}</div>,
  useAuth: () => ({
    user: null,
    loading: false,
    login: jest.fn(),
    logout: jest.fn(),
    hasPermission: () => false,
    hasAuthority: () => false,
    hasAnyPermission: () => false,
    hasAnyAuthority: () => false,
    moduleAccess: { mode: 'allow_all', allowed_modules: null },
  }),
  usePermissions: () => ({
    can: () => false,
    canAny: () => false,
    canAll: () => false,
    isAny: () => false,
    canAccessModule: () => true,
    canAccessEssPortal: () => false,
    getPrimaryAuthority: () => null,
    getAuthorityDisplayName: () => '',
  }),
}));

describe('App', () => {
  test('renders without crashing', async () => {
    const { default: App } = await import('./App');
    const { container } = render(<App />);
    expect(container).toBeTruthy();
  });
});
