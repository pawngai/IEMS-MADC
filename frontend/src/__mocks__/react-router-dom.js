/**
 * Manual Jest mock for react-router-dom v7 (ESM).
 *
 * react-router-dom v7 ships only as ESM (.mjs) which Jest's default
 * resolver cannot import.  This file is auto-discovered by Jest when
 * any test calls `jest.mock('react-router-dom')` or imports the package.
 */
const React = require('react');

module.exports = {
  BrowserRouter: ({ children }) => React.createElement('div', { 'data-testid': 'router' }, children),
  HashRouter: ({ children }) => React.createElement('div', null, children),
  Routes: ({ children }) => React.createElement('div', null, children),
  Route: () => null,
  Navigate: () => null,
  Link: ({ children, to }) => React.createElement('a', { href: to }, children),
  NavLink: ({ children, to }) => React.createElement('a', { href: to }, children),
  Outlet: () => null,
  useNavigate: () => jest.fn(),
  useLocation: () => ({ pathname: '/', search: '', hash: '', state: null }),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), jest.fn()],
  useMatch: () => null,
  useRoutes: () => null,
  createBrowserRouter: jest.fn(),
  RouterProvider: ({ children }) => React.createElement('div', null, children),
};
