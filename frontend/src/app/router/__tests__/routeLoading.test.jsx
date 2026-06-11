import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { resolveRouteLoadingVariant, RouteShellFallback } from "@/app/router/routeLoading";

const mockUseAuth = jest.fn();
const mockUseLocation = jest.fn();

jest.mock("@/contexts/identity_access/model/authContext", () => ({
  __esModule: true,
  useAuth: () => mockUseAuth(),
}));

jest.mock("react-router-dom", () => ({
  __esModule: true,
  useLocation: () => mockUseLocation(),
}));

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

describe("routeLoading", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({ user: { id: "u-1" }, loading: false });
    mockUseLocation.mockReturnValue({ pathname: "/employees" });
  });

  test("maps key paths to shell loading variants", () => {
    expect(resolveRouteLoadingVariant("/employees")).toBe("employees");
    expect(resolveRouteLoadingVariant("/work")).toBe("work");
    expect(resolveRouteLoadingVariant("/admin")).toBe("dashboard");
    expect(resolveRouteLoadingVariant("/service-book/MADC-1")).toBe("detail");
    expect(resolveRouteLoadingVariant("/unknown")).toBe("generic");
  });

  test("renders the app shell fallback for authenticated routes", () => {
    render(<RouteShellFallback />);

    expect(screen.getByTestId("layout")).toBeInTheDocument();
    expect(screen.getByTestId("route-shell-fallback")).toBeInTheDocument();
  });

  test("falls back to the full-page loader before auth is available", () => {
    mockUseAuth.mockReturnValue({ user: null, loading: true });

    render(<RouteShellFallback />);

    expect(screen.queryByTestId("layout")).not.toBeInTheDocument();
    expect(screen.getByTestId("boot-loader")).toBeInTheDocument();
    expect(screen.getByText("Preparing your workspace")).toBeInTheDocument();
    expect(screen.getByTestId("route-shell-fallback")).toBeInTheDocument();
  });
});