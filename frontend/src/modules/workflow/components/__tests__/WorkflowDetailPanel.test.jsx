import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

import WorkflowDetailPanel from "@/modules/workflow/components/WorkflowDetailPanel";

const mockGetIdentity = vi.fn();
const mockGetEmployeeProfileSummary = vi.fn();

vi.mock("@/modules/workflow/model/workQueueGateway", () => ({
  getEmployeeIdentitySummary: (...args) => mockGetIdentity(...args),
  getEmployeeProfileSummary: (...args) => mockGetEmployeeProfileSummary(...args),
}));

vi.mock("@/shared/ui/badge", () => ({
  Badge: ({ children }) => <span>{children}</span>,
}));

vi.mock("@/shared/ui/button", () => ({
  Button: ({ children, onClick, ...props }) => (
    <button type="button" onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock("@/shared/ui/separator", () => ({
  Separator: () => <hr />,
}));

vi.mock("@/shared/ui/sheet", () => ({
  SheetHeader: ({ children }) => <div>{children}</div>,
  SheetTitle: ({ children }) => <div>{children}</div>,
}));

vi.mock("@/shared/ui/skeleton", () => ({
  Skeleton: () => <div />,
}));

vi.mock("@/shared/ui/textarea", () => ({
  Textarea: (props) => <textarea {...props} />,
}));

vi.mock("@/modules/workflow/components/workflowQueuePrimitives", () => ({
  SlaDot: () => <span>SLA</span>,
}));

describe("WorkflowDetailPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetIdentity.mockResolvedValue(null);
    mockGetEmployeeProfileSummary.mockResolvedValue(null);
  });

  test("keeps edit, profile, and service book actions visible together for draft profiles", () => {
    render(
      <WorkflowDetailPanel
        item={{
          type: "profile",
          title: "Onboard Employee 001",
          statusLabel: "DRAFT",
          sla: "RED",
          ageHours: 72,
          raw: {
            employee_code: "ONB-EMP-001",
            employment_type: "REGULAR",
            current_department_id: "GEN",
            current_designation_id: "LDC",
          },
        }}
        actions={[]}
        remarks=""
        setRemarks={() => {}}
        onAction={() => {}}
        actionBusy={false}
        auditTrail={[]}
        auditLoading={false}
        showActions
        onEditPrimary={() => {}}
        onOpenPrimary={() => {}}
        onOpenSecondary={() => {}}
        editPrimaryLabel="Edit / Complete Profile"
        primaryOpenLabel="Profile"
        secondaryOpenLabel="View Service Book"
      />,
    );

    expect(screen.getByRole("button", { name: /^Edit \/ Complete Profile$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Profile$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^View Service Book$/i })).toBeInTheDocument();
  });

  test("loads and renders complete employee identity details in identity panel", async () => {
    mockGetIdentity.mockResolvedValue({
      employee_id: "EMP-IDENTITY-001",
      employee_code: "MADC-2024-R0005",
      full_name: "Complete Identity User",
      gender: "Female",
      date_of_birth: "1991-02-03",
      aadhaar_number: "123456789012",
      employment_type: "REGULAR",
      date_of_initial_engagement: "2024-04-01",
      current_department_id: "FIN",
      current_designation_id: "ASO",
      current_office_id: "HQ",
      reporting_officer_id: "EMP-HOD-1",
      employee_status: "ACTIVE",
      status_effective_date: "2024-04-01",
      status_remarks: "Activated after approval",
      workflow_status: "VERIFIED",
      created_at: "2026-05-01T10:00:00Z",
      created_by: "user-create",
      updated_at: "2026-05-02T10:00:00Z",
      updated_by: "user-update",
      version: 3,
    });

    render(
      <WorkflowDetailPanel
        item={{
          type: "identity",
          title: "Complete Identity User",
          statusLabel: "VERIFIED",
          stage: "VERIFIED",
          sla: "GREEN",
          ageHours: 2,
          employeeId: "EMP-IDENTITY-001",
          raw: {
            employee_id: "EMP-IDENTITY-001",
            employee_code: "MADC-2024-R0005",
            full_name: "Complete Identity User",
          },
        }}
        actions={[]}
        remarks=""
        setRemarks={() => {}}
        onAction={() => {}}
        actionBusy={false}
        auditTrail={[]}
        auditLoading={false}
        showActions={false}
      />,
    );

    await waitFor(() => expect(mockGetIdentity).toHaveBeenCalledWith("EMP-IDENTITY-001"));
    expect(await screen.findByTestId("identity-details-complete")).toBeInTheDocument();
    expect(screen.getByText("Full Name")).toBeInTheDocument();
    expect(screen.getAllByText("Complete Identity User").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Aadhaar")).toBeInTheDocument();
    expect(screen.getByText("XXXX XXXX 9012")).toBeInTheDocument();
    expect(screen.queryByText("Office")).not.toBeInTheDocument();
    expect(screen.queryByText("Reporting Officer")).not.toBeInTheDocument();
    expect(screen.queryByText("EMP-HOD-1")).not.toBeInTheDocument();
    expect(screen.queryByText("Status")).not.toBeInTheDocument();
    expect(screen.queryByText("Identity Workflow")).not.toBeInTheDocument();
    expect(screen.queryByText("Status Effective Date")).not.toBeInTheDocument();
    expect(screen.queryByText("Status Remarks")).not.toBeInTheDocument();
    expect(screen.queryByText("Activated after approval")).not.toBeInTheDocument();
    expect(screen.queryByText("Employee ID")).not.toBeInTheDocument();
    expect(screen.queryByText("Employee Status")).not.toBeInTheDocument();
    expect(screen.queryByText("Record Metadata")).not.toBeInTheDocument();
    expect(screen.queryByText("user-update")).not.toBeInTheDocument();
  });

  test("loads and renders completed profile extension fields in profile panel", async () => {
    mockGetEmployeeProfileSummary.mockResolvedValue({
      employee_id: "EMP-PROFILE-001",
      employee_code: "MADC-2024-R0003",
      full_name: "Submitted Profile User",
      employment_type: "REGULAR",
      current_department_id: "GAD",
      current_designation_id: "ES",
      employee_section_completed: true,
      data_entry_section_completed: true,
      father_name: "Profile Father",
      mother_name: "Profile Mother",
      contact: {
        mobile_primary: "9862000003",
        mobile_alternate: "9862000093",
        email_personal: "r0003.personal@example.com",
        address_line1: "House No. 3, Council Road",
        address_line2: "Near Secretariat",
        city: "Siaha",
        district: "Siaha",
        state: "Mizoram",
        pincode: "796901",
        present_address_line1: "House No. 3, Council Road",
        present_city: "Siaha",
        present_state: "Mizoram",
        present_pincode: "796901",
        emergency_name: "R0003 Emergency Contact",
        emergency_phone: "9862000193",
        emergency_relation: "Brother",
      },
      photo_url: "/api/documents/photos/profile-photo.png",
      signature_url: "/api/documents/signatures/profile-signature.png",
    });

    render(
      <WorkflowDetailPanel
        item={{
          type: "profile",
          title: "Submitted Profile User",
          statusLabel: "SUBMITTED",
          sla: "GREEN",
          ageHours: 1,
          employeeId: "EMP-PROFILE-001",
          raw: {
            employee_id: "EMP-PROFILE-001",
            employee_code: "MADC-2024-R0003",
            full_name: "Submitted Profile User",
            employment_type: "REGULAR",
          },
        }}
        actions={[]}
        remarks=""
        setRemarks={() => {}}
        onAction={() => {}}
        actionBusy={false}
        auditTrail={[]}
        auditLoading={false}
        showActions={false}
      />,
    );

    await waitFor(() => expect(mockGetEmployeeProfileSummary).toHaveBeenCalledWith("EMP-PROFILE-001"));
    expect(await screen.findByTestId("profile-extension-details-complete")).toBeInTheDocument();
    expect(screen.getByText("Personal Profile")).toBeInTheDocument();
    expect(screen.getByText("Profile Father")).toBeInTheDocument();
    expect(screen.getByText("Contact")).toBeInTheDocument();
    expect(screen.getByText("9862000003")).toBeInTheDocument();
    expect(screen.getByText("Permanent Address")).toBeInTheDocument();
    expect(screen.getAllByText("House No. 3, Council Road").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Emergency Contact")).toBeInTheDocument();
    expect(screen.getByText("R0003 Emergency Contact")).toBeInTheDocument();
    expect(screen.getByText("Media")).toBeInTheDocument();
    expect(screen.getByText("/api/documents/photos/profile-photo.png")).toBeInTheDocument();
    expect(screen.getByText("Employee Section")).toBeInTheDocument();
    expect(screen.getByText("Data Entry Section")).toBeInTheDocument();
  });
});