import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import LoginPage from "@/contexts/identity/ui/LoginPage";

const mockNavigate = vi.fn();
const mockLogin = vi.fn();
const mockUseAuth = vi.fn();

vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock("@/contexts/identity/model/authContext", () => ({
  __esModule: true,
  useAuth: () => mockUseAuth(),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      user: null,
    });
    sessionStorage.clear();
  });

  test("shows inline required-field errors and does not submit empty credentials", () => {
    render(<LoginPage />);

    fireEvent.click(screen.getByTestId("login-submit-btn"));

    expect(screen.getByText("Email is required")).toBeInTheDocument();
    expect(screen.getByText("Password is required")).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  test("shows inline validation for malformed email addresses", () => {
    render(<LoginPage />);

    fireEvent.change(screen.getByTestId("login-email-input"), {
      target: { value: "abc" },
    });
    fireEvent.change(screen.getByTestId("login-password-input"), {
      target: { value: "password123" },
    });

    fireEvent.click(screen.getByTestId("login-submit-btn"));

    expect(screen.getByText("Enter a valid email address")).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  test("shows a visible auth error when sign-in fails and clears it after editing", async () => {
    mockLogin.mockRejectedValueOnce(new Error("Invalid credentials"));

    render(<LoginPage />);

    fireEvent.change(screen.getByTestId("login-email-input"), {
      target: { value: "global.dataentry@madc.gov.in" },
    });
    fireEvent.change(screen.getByTestId("login-password-input"), {
      target: { value: "wrongpass" },
    });

    fireEvent.click(screen.getByTestId("login-submit-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("login-auth-error")).toHaveTextContent("Invalid credentials");
    });

    fireEvent.change(screen.getByTestId("login-password-input"), {
      target: { value: "wrongpass1" },
    });

    expect(screen.queryByTestId("login-auth-error")).not.toBeInTheDocument();
  });
});