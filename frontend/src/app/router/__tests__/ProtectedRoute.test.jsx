import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { ProtectedRoute } from "@/app/router/guards";

const mockUseAuth = jest.fn();

jest.mock("@/contexts/identity/model/authContext", () => ({
  __esModule: true,
  useAuth: () => mockUseAuth(),
}));

jest.mock("@/app/pages/system-admin/AccessDeniedPage", () => ({
  __esModule: true,
  default: ({ title, description }) => (
    <div data-testid="access-denied">
      <div>{title}</div>
      <div>{description}</div>
    </div>
  ),
}));

jest.mock("react-router-dom", () => ({
  __esModule: true,
  Navigate: ({ to }) => <div data-testid="navigate">redirect:{to}</div>,
}));

describe("ProtectedRoute strict auth options", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: { id: "u-1", authorities: ["SYSTEM_ADMIN"] },
      loading: false,
      canAny: (permissions) => permissions.some((p) => p === "ALLOW" || p === "ALLOW2"),
      isAny: (authorities) => authorities.some((a) => a === "SYSTEM_ADMIN"),
      canAccessModule: () => true,
    });
  });

  test("enforces all permissions when requireAllPermissions is true", () => {
    render(
      <ProtectedRoute requiredPermissions={["ALLOW", "DENY"]} requireAllPermissions>
        <div data-testid="ok">ok</div>
      </ProtectedRoute>
    );

    expect(screen.queryByTestId("ok")).not.toBeInTheDocument();
    expect(screen.getByTestId("access-denied")).toHaveTextContent(
      "You do not have the required permissions for this page."
    );
  });

  test("enforces required authority", () => {
    mockUseAuth.mockReturnValue({
      user: { id: "u-2", authorities: ["EMPLOYEE"] },
      loading: false,
      canAny: (permissions) => permissions.includes("ALLOW"),
      isAny: () => false,
      canAccessModule: () => true,
    });

    render(
      <ProtectedRoute requiredPermissions={["ALLOW"]} requiredAuthorities={["SYSTEM_ADMIN"]}>
        <div data-testid="ok">ok</div>
      </ProtectedRoute>
    );

    expect(screen.queryByTestId("ok")).not.toBeInTheDocument();
    expect(screen.getByTestId("access-denied")).toHaveTextContent(
      "Your current role does not allow access to this page."
    );
  });

  test("allows access when strict requirements are satisfied", () => {
    mockUseAuth.mockReturnValue({
      user: { id: "u-3", authorities: ["SYSTEM_ADMIN"] },
      loading: false,
      canAny: (permissions) => permissions.includes("ALLOW") || permissions.includes("ALLOW2"),
      isAny: (authorities) => authorities.includes("SYSTEM_ADMIN"),
      canAccessModule: () => true,
    });

    render(
      <ProtectedRoute
        requiredPermissions={["ALLOW", "ALLOW2"]}
        requireAllPermissions
        requiredAuthorities={["SYSTEM_ADMIN"]}
        moduleId="admin_console"
      >
        <div data-testid="ok">ok</div>
      </ProtectedRoute>
    );

    expect(screen.getByTestId("ok")).toBeInTheDocument();
    expect(screen.queryByTestId("navigate")).not.toBeInTheDocument();
  });
});
