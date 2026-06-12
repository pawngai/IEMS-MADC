import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import EssProfilePage from "@/contexts/employee_master/pages/EmployeeProfilePage";

const mockNavigate = vi.fn();
const mockUseAuth = vi.fn();
const mockGetMyProfile = vi.fn();
const mockGetComplete = vi.fn();
const mockUpdateMyContact = vi.fn();
const mockUpdateProfile = vi.fn();
const mockSubmitProfile = vi.fn();
const mockToastSuccess = vi.fn();
const mockToastError = vi.fn();

jest.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout-shell">{children}</div>,
}));

jest.mock("@/contexts/employee_master/components/EmployeeProfileSummary", () => ({
  __esModule: true,
  default: ({ profile, serviceBook }) => (
    <div data-testid="profile-summary">{profile?.full_name}-{serviceBook ? "servicebook" : "profile-only"}</div>
  ),
}));

jest.mock("@/contexts/service_book/api/serviceBookApi", () => ({
  __esModule: true,
  serviceBookAPI: {
    getComplete: (...args) => mockGetComplete(...args),
  },
}));

jest.mock("@/contexts/employee_master/components/EmployeeProfileExtensionEditor", () => ({
  __esModule: true,
  default: ({ onCancel, submitAction }) => (
    <div data-testid="profile-editor">
      <button type="button" onClick={() => submitAction({ mobile_primary: "9862000003" })}>Save Editor</button>
      <button type="button" onClick={onCancel}>Close Editor</button>
    </div>
  ),
}));

jest.mock("@/contexts/employee_master/api/employeeProfileApi", () => ({
  __esModule: true,
  employeeProfileApi: {
    update: (...args) => mockUpdateProfile(...args),
    submit: (...args) => mockSubmitProfile(...args),
  },
}));

jest.mock("@/contexts/ess/api/essApi", () => ({
  __esModule: true,
  essAPI: {
    getMyProfile: (...args) => mockGetMyProfile(...args),
    updateMyContact: (...args) => mockUpdateMyContact(...args),
  },
}));

jest.mock("@/contexts/identity_access/model/authContext", () => ({
  __esModule: true,
  useAuth: () => mockUseAuth(),
}));

jest.mock("sonner", () => ({
  __esModule: true,
  toast: {
    success: (...args) => mockToastSuccess(...args),
    error: (...args) => mockToastError(...args),
  },
}));

describe("EmployeeProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      can: () => true,
    });
    mockUpdateMyContact.mockResolvedValue({ data: {} });
    mockUpdateProfile.mockResolvedValue({ data: { success: true } });
    mockSubmitProfile.mockResolvedValue({ data: { success: true } });
    mockGetComplete.mockResolvedValue({ data: { part_iv: { entries: [] } } });
    mockGetMyProfile.mockResolvedValue({
      data: {
        employee_id: "EMP-1",
        full_name: "Draft Employee",
        employment_type: "REGULAR",
        workflow_status: "DRAFT",
        employee_section_completed: true,
        data_entry_section_completed: true,
      },
    });
  });

  test("allows draft employee to edit and submit once both sections are complete", async () => {
    render(<EssProfilePage />);

    await screen.findByText("My Profile");

    await waitFor(() => {
      expect(mockGetComplete).toHaveBeenCalledWith("EMP-1");
    });

    expect(screen.getByRole("button", { name: "Edit Profile" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Submit for Review/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Edit Profile" }));
    expect(screen.getByTestId("profile-editor")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Save Editor" }));

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith("EMP-1", { mobile_primary: "9862000003" });
    });
    expect(mockUpdateMyContact).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Close Editor" }));

    fireEvent.click(screen.getByRole("button", { name: /Submit for Review/i }));

    await waitFor(() => {
      expect(mockSubmitProfile).toHaveBeenCalledWith("EMP-1");
    });

    expect(mockToastSuccess).toHaveBeenCalledWith("Profile submitted for verification");
  });

  test("shows profile as view-only when employee lacks update permission", async () => {
    mockUseAuth.mockReturnValue({
      can: (permission) => permission === "PROFILE_READ_OWN",
    });

    render(<EssProfilePage />);

    await screen.findByText("My Profile");

    expect(screen.getByTestId("profile-summary")).toBeInTheDocument();
    expect(mockGetComplete).not.toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: "Edit Profile" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Submit for Review/i })).not.toBeInTheDocument();
    expect(
      screen.getByText(/Your profile is view-only in the employee portal/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Open Change Requests" })
    ).toBeInTheDocument();
  });
});