/**
 * ErrorBoundary component tests.
 *
 * Validates the React error boundary catches render errors
 * and displays the fallback UI with a refresh button.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import ErrorBoundary from '@/app/layout/ErrorBoundary';

// Suppress noisy React error-boundary console.error output
let consoleErrorSpy;
let suppressExpectedBoundaryError;

beforeEach(() => {
  consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  suppressExpectedBoundaryError = (event) => {
    if (event.error?.message === 'Test kaboom') {
      event.preventDefault();
    }
  };
  window.addEventListener('error', suppressExpectedBoundaryError);
});

afterEach(() => {
  window.removeEventListener('error', suppressExpectedBoundaryError);
  consoleErrorSpy?.mockRestore();
});

function ThrowingChild() {
  throw new Error('Test kaboom');
}

function GoodChild() {
  return <div>All is well</div>;
}

describe('ErrorBoundary', () => {
  test('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <GoodChild />
      </ErrorBoundary>,
    );
    expect(screen.getByText('All is well')).toBeInTheDocument();
  });

  test('renders fallback UI when a child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>,
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
  });

  test('does not render children after catching an error', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>,
    );
    expect(screen.queryByText('All is well')).not.toBeInTheDocument();
  });
});
