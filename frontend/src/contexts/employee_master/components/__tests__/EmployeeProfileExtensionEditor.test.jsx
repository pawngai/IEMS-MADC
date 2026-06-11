import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import EmployeeProfileExtensionEditor from "@/contexts/employee_master/components/EmployeeProfileExtensionEditor";

const mockGetEmploymentTypes = jest.fn();
const mockGetDepartments = jest.fn();
const mockGetDesignations = jest.fn();
const mockGetPayLevels = jest.fn();
const mockUploadDocument = jest.fn();
const mockGetFileUrl = jest.fn();
const mockUploadPhoto = jest.fn();
const mockUploadSignature = jest.fn();
const mockToastSuccess = jest.fn();
const mockToastError = jest.fn();

jest.mock("@/contexts/organization_master/api/mastersApi", () => ({
  __esModule: true,
  mastersAPI: {
    getEmploymentTypes: (...args) => mockGetEmploymentTypes(...args),
    getDepartments: (...args) => mockGetDepartments(...args),
    getDesignations: (...args) => mockGetDesignations(...args),
    getPayLevels: (...args) => mockGetPayLevels(...args),
  },
}));

jest.mock("@/contexts/documents/api/documentsApi", () => ({
  __esModule: true,
  documentsAPI: {
    upload: (...args) => mockUploadDocument(...args),
    getFileUrl: (...args) => mockGetFileUrl(...args),
  },
}));

jest.mock("@/contexts/employee_master/api/employeeProfileApi", () => ({
  __esModule: true,
  employeeProfileApi: {
    uploadPhoto: (...args) => mockUploadPhoto(...args),
    uploadSignature: (...args) => mockUploadSignature(...args),
  },
}));

jest.mock("@/shared/ui/searchable-select", () => ({
  __esModule: true,
  SearchableSelect: ({ value, onValueChange, options = [], placeholder }) => (
    <select
      data-testid={placeholder || "searchable-select"}
      value={value || ""}
      onChange={(event) => onValueChange(event.target.value)}
    >
      <option value="">Select</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  ),
}));

jest.mock("@/shared/ui/select", () => ({
  __esModule: true,
  Select: ({ value, onValueChange, children, disabled }) => (
    <select
      data-testid="mock-select"
      value={value || ""}
      onChange={(event) => onValueChange(event.target.value)}
      disabled={disabled}
    >
      {children}
    </select>
  ),
  SelectTrigger: ({ children }) => <>{children}</>,
  SelectValue: ({ placeholder }) => <option value="">{placeholder}</option>,
  SelectContent: ({ children }) => <>{children}</>,
  SelectItem: ({ value, children }) => <option value={value}>{children}</option>,
}));

jest.mock("sonner", () => ({
  __esModule: true,
  toast: {
    success: (...args) => mockToastSuccess(...args),
    error: (...args) => mockToastError(...args),
  },
}));

describe("EmployeeProfileExtensionEditor", () => {
  beforeEach(() => {
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
    jest.clearAllMocks();
    mockGetEmploymentTypes.mockResolvedValue({ data: [] });
    mockGetDepartments.mockResolvedValue({ data: [] });
    mockGetDesignations.mockResolvedValue({ data: [] });
    mockGetPayLevels.mockResolvedValue({ data: [] });
    mockUploadDocument.mockResolvedValue({ data: { document_id: "DOC-1", filename: "doc-1.pdf", original_name: "doc-1.pdf" } });
    mockGetFileUrl.mockImplementation((filename) => `/files/${filename}`);
    mockUploadPhoto.mockResolvedValue({ data: { photo_url: "/api/documents/photos/profile-photo.png" } });
    mockUploadSignature.mockResolvedValue({ data: { signature_url: "/api/documents/signatures/profile-signature.png" } });
  });

  test("submits profile-extension payload through the standalone admin editor", async () => {
    const submitAction = jest.fn().mockResolvedValue({});
    const onSuccess = jest.fn();

    render(
      <EmployeeProfileExtensionEditor
        profile={{
          employee_id: "EMP-1",
          employment_type: "REGULAR",
          mobile_primary: "9876543210",
          email_personal: "person@example.com",
          email_official: "official@example.com",
          address_line1: "123 Main Street",
          city: "Mumbai",
          state: "MH",
          pincode: "400001",
          present_address_line1: "123 Main Street",
          present_city: "Mumbai",
          present_state: "MH",
          present_pincode: "400001",
          emergency_name: "Contact Person",
          emergency_phone: "9999999999",
          emergency_relation: "Sibling",
        }}
        submitAction={submitAction}
        onSuccess={onSuccess}
      />
    );

    fireEvent.click(await screen.findByRole("button", { name: "Save Profile" }));

    await waitFor(() => {
        expect(submitAction).toHaveBeenCalledWith(
          expect.objectContaining({
            mobile_primary: "9876543210",
            email_official: "official@example.com",
        })
      );
    });

    const payload = submitAction.mock.calls[0][0];
    expect(payload.employee_section_completed).toBeUndefined();
    expect(payload.data_entry_section_completed).toBeUndefined();
    expect(onSuccess).toHaveBeenCalled();
  });

  test("maps ESS profile updates to the ESS contact payload contract", async () => {
    const submitAction = jest.fn().mockResolvedValue({});
    const onSuccess = jest.fn();

    render(
      <EmployeeProfileExtensionEditor
        essMode
        profile={{
          employee_id: "EMP-2",
          employment_type: "REGULAR",
          mobile_primary: "9123456789",
          mobile_alternate: "9988776655",
          email_personal: "employee@example.com",
          email_official: "should-not-send@example.com",
          address_line1: "44 Lake Road",
          city: "Pune",
          state: "MH",
          pincode: "411001",
          present_address_line1: "44 Lake Road",
          present_city: "Pune",
          present_state: "MH",
          present_pincode: "411001",
          emergency_name: "Emergency Contact",
          emergency_phone: "9988776655",
          emergency_relation: "Sibling",
        }}
        submitAction={submitAction}
        onSuccess={onSuccess}
      />
    );

    fireEvent.click(await screen.findByRole("button", { name: "Save Profile" }));

    await waitFor(() => {
      expect(submitAction).toHaveBeenCalledWith(
        expect.objectContaining({
          mobile_primary: "9123456789",
          mobile_alternate: "9988776655",
          email_personal: "employee@example.com",
          address_line1: "44 Lake Road",
          city: "Pune",
          state: "MH",
        })
      );
    });

    const payload = submitAction.mock.calls[0][0];
    expect(payload.employee_section_completed).toBeUndefined();
    expect(payload.email_official).toBeUndefined();
    expect(payload.data_entry_section_completed).toBeUndefined();
    expect(onSuccess).toHaveBeenCalled();
  });

  test("uploads photo and signature through the profile extension payload", async () => {
    const submitAction = jest.fn().mockResolvedValue({});

    render(
      <EmployeeProfileExtensionEditor
        profile={{
          employee_id: "EMP-6",
          employment_type: "REGULAR",
          mobile_primary: "9123456789",
        }}
        submitAction={submitAction}
      />
    );

    fireEvent.change(document.getElementById("profile-extension-photo-upload"), {
      target: { files: [new File(["photo"], "photo.png", { type: "image/png" })] },
    });
    fireEvent.change(document.getElementById("profile-extension-signature-upload"), {
      target: { files: [new File(["signature"], "signature.png", { type: "image/png" })] },
    });

    await waitFor(() => {
      expect(mockUploadPhoto).toHaveBeenCalled();
      expect(mockUploadSignature).toHaveBeenCalled();
    });

    fireEvent.click(await screen.findByRole("button", { name: "Save Profile" }));

    await waitFor(() => {
      expect(submitAction).toHaveBeenCalledWith(
        expect.objectContaining({
          photo_url: "/api/documents/photos/profile-photo.png",
          signature_url: "/api/documents/signatures/profile-signature.png",
        })
      );
    });
    expect(mockToastSuccess).toHaveBeenCalledWith("Photo uploaded. Save profile to apply it.");
    expect(mockToastSuccess).toHaveBeenCalledWith("Signature uploaded. Save profile to apply it.");
  });

  test("does not render manual workflow completion toggles", async () => {
    render(
      <EmployeeProfileExtensionEditor
        profile={{ employee_id: "EMP-3", employment_type: "REGULAR" }}
        submitAction={jest.fn().mockResolvedValue({})}
      />
    );

    await waitFor(() => {
      expect(mockGetPayLevels).toHaveBeenCalled();
    });

    expect(screen.queryByText("Workflow Controls")).not.toBeInTheDocument();
    expect(screen.queryByText("Employee Section Completed")).not.toBeInTheDocument();
    expect(screen.queryByText("Data Entry Section Completed")).not.toBeInTheDocument();
  });

  test("hides shared profile-extension fields and omits them from submits for non-regular employees", async () => {
    const submitAction = jest.fn().mockResolvedValue({});

    render(
      <EmployeeProfileExtensionEditor
        profile={{
          employee_id: "EMP-4",
          employment_type: "CONTRACTUAL",
          contract_order_no: "CON/2026/001",
          contract_start_date: "2026-04-01",
          contract_end_date: "2027-03-31",
          consolidated_pay: 50000,
          contract_authority: "Director HR",
          vendor_agency: "Legacy Agency",
          renewal_allowed: "YES",
        }}
        submitAction={submitAction}
      />
    );

    expect(screen.queryByText("Profile Extension")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Vendor/Agency (if applicable)")).not.toBeInTheDocument();

    fireEvent.click(await screen.findByRole("button", { name: "Save Profile" }));

    await waitFor(() => {
      expect(submitAction).toHaveBeenCalledWith(
        expect.objectContaining({
          contract_order_no: "CON/2026/001",
          contract_start_date: "2026-04-01",
          contract_end_date: "2027-03-31",
          consolidated_pay: 50000,
          contract_authority: "Director HR",
          renewal_allowed: "YES",
        })
      );
    });

    expect(submitAction.mock.calls[0][0].vendor_agency).toBeUndefined();
  });

  test("renders non-regular demographic fields and submits them through the profile extension payload", async () => {
    mockGetEmploymentTypes.mockResolvedValue({
      data: [
        {
          employment_type_code: "FIXED_PAY",
          name: "Fixed Pay",
          employment_class: "NON_REGULAR",
          eligible_for_service_book: false,
          eligible_for_wages: false,
          eligible_for_fixed_remuneration: true,
          requires_engagement_order: true,
        },
      ],
    });
    mockGetDepartments.mockResolvedValue({ data: [{ department_id: "GAD", department_name: "General Administration & Control" }] });
    mockGetDesignations.mockResolvedValue({ data: [{ designation_id: "ES", designation_name: "Executive Secretary" }] });

    const submitAction = jest.fn().mockResolvedValue({});

    render(
      <EmployeeProfileExtensionEditor
        profile={{
          employee_id: "EMP-7",
          employment_type: "FIXED_PAY",
          blood_group: "O+",
          marital_status: "MARRIED",
          spouse_name: "Spouse Name",
          mobile_primary: "9876543210",
        }}
        submitAction={submitAction}
      />
    );

    expect(await screen.findByText("Personal Profile")).toBeInTheDocument();
    expect(screen.getByLabelText("Father's Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Mother's Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Nationality")).toBeInTheDocument();
    expect(screen.getByLabelText("Category")).toBeInTheDocument();
    expect(screen.getByLabelText("Religion")).toBeInTheDocument();
    expect(screen.getByText("Blood Group")).toBeInTheDocument();
    expect(screen.getByText("Marital Status")).toBeInTheDocument();

    fireEvent.change(screen.getByTestId("Select department"), { target: { value: "GAD" } });
    fireEvent.change(screen.getByTestId("Select designation"), { target: { value: "ES" } });
    fireEvent.change(screen.getByLabelText("Engagement Order No"), { target: { value: "ENG/2025/001" } });
    fireEvent.change(screen.getByLabelText("Engagement Start Date"), { target: { value: "2025-05-12" } });
    fireEvent.change(screen.getByLabelText("Monthly Remuneration"), { target: { value: "25000" } });
    fireEvent.change(screen.getByLabelText("Father's Name"), { target: { value: "L. Surname" } });
    fireEvent.change(screen.getByLabelText("Mother's Name"), { target: { value: "M. Surname" } });
    fireEvent.change(screen.getByLabelText("Nationality"), { target: { value: "Indian" } });
    fireEvent.change(screen.getByLabelText("Category"), { target: { value: "GENERAL" } });
    fireEvent.change(screen.getByLabelText("Religion"), { target: { value: "Christian" } });

    expect(screen.getByLabelText("Spouse Name")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Save Profile" }));

    await waitFor(() => {
      expect(submitAction).toHaveBeenCalledWith(
        expect.objectContaining({
          father_name: "L. Surname",
          mother_name: "M. Surname",
          nationality: "Indian",
          category: "GENERAL",
          religion: "Christian",
          blood_group: "O+",
          marital_status: "MARRIED",
          spouse_name: "Spouse Name",
        })
      );
    });
  });

  test("does not render family eligibility fields", async () => {
    render(
      <EmployeeProfileExtensionEditor
        profile={{ employee_id: "EMP-5", employment_type: "REGULAR" }}
        submitAction={jest.fn().mockResolvedValue({})}
      />
    );

    await waitFor(() => {
      expect(mockGetPayLevels).toHaveBeenCalled();
    });

    expect(screen.queryByLabelText("Surviving Children Count")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Single Mother Exception")).not.toBeInTheDocument();
    expect(screen.queryByText("Family Eligibility")).not.toBeInTheDocument();
    expect(screen.queryByText("Leave-policy family context used for CCS child-care and related eligibility checks.")).not.toBeInTheDocument();
  });

  test("defaults a blank admin profile to REGULAR when masters omit a regular option", async () => {
    const submitAction = jest.fn().mockResolvedValue({});

    mockGetEmploymentTypes.mockResolvedValue({
      data: [
        {
          employment_type_code: "CONTRACT",
          name: "Contract",
          employment_class: "NON_REGULAR",
          eligible_for_service_book: false,
        },
      ],
    });

    render(
      <EmployeeProfileExtensionEditor
        profile={{ employee_id: "EMP-REG-1", mobile_primary: "9876543210" }}
        submitAction={submitAction}
      />
    );

    fireEvent.click(await screen.findByRole("button", { name: "Save Profile" }));

    await waitFor(() => {
      expect(submitAction).toHaveBeenCalledWith(
        expect.objectContaining({
          employment_type: "REGULAR",
          mobile_primary: "9876543210",
        })
      );
    });
  });

  test("captures non-regular profile details in the shared profile editor", async () => {
    const submitAction = jest.fn().mockResolvedValue({});

    mockGetEmploymentTypes.mockResolvedValue({
      data: [
        {
          employment_type_code: "CONTRACT",
          name: "Contract",
          employment_class: "NON_REGULAR",
          eligible_for_service_book: false,
          requires_engagement_order: true,
          requires_contract_period: true,
          eligible_for_wages: false,
          eligible_for_fixed_remuneration: true,
        },
      ],
    });
    mockGetDepartments.mockResolvedValue({ data: [{ department_id: "DEP-1", department_name: "Finance" }] });
    mockGetDesignations.mockResolvedValue({ data: [{ designation_id: "DES-1", designation_name: "Consultant" }] });

    render(
      <EmployeeProfileExtensionEditor
        profile={{ employee_id: "EMP-7" }}
        nonRegular
        submitAction={submitAction}
      />
    );

    fireEvent.click(await screen.findByRole("radio", { name: /Contract/i }));
    fireEvent.change(screen.getByTestId("Select department"), { target: { value: "DEP-1" } });
    fireEvent.change(screen.getByTestId("Select designation"), { target: { value: "DES-1" } });
    fireEvent.change(screen.getByLabelText("Engagement Order No"), { target: { value: "CON/2026/001" } });
    fireEvent.change(screen.getByLabelText("Engagement Start Date"), { target: { value: "2026-04-01" } });
    fireEvent.change(screen.getByLabelText("Engagement End Date"), { target: { value: "2027-03-31" } });
    fireEvent.change(screen.getByLabelText("Monthly Remuneration"), { target: { value: "50000" } });

    fireEvent.click(screen.getByRole("button", { name: "Save Profile" }));

    await waitFor(() => {
      expect(submitAction).toHaveBeenCalledWith(
        expect.objectContaining({
          employment_type: "CONTRACT",
          current_department_id: "DEP-1",
          current_designation_id: "DES-1",
          engagement_order_no: "CON/2026/001",
          date_of_initial_engagement: "2026-04-01",
          engagement_end_date: "2027-03-31",
          fixed_monthly_amount: 50000,
        })
      );
    });

    const payload = submitAction.mock.calls[0][0];
    expect(payload.pending_non_regular_setup).toBeUndefined();
  });

  test("preserves existing non-regular engagement values while masters are loading", async () => {
    let resolveEmploymentTypes;
    const submitAction = jest.fn().mockResolvedValue({});

    mockGetEmploymentTypes.mockReturnValue(
      new Promise((resolve) => {
        resolveEmploymentTypes = resolve;
      })
    );
    mockGetDepartments.mockResolvedValue({ data: [{ department_id: "DEP-1", department_name: "Finance" }] });
    mockGetDesignations.mockResolvedValue({ data: [{ designation_id: "DES-1", designation_name: "Consultant" }] });

    render(
      <EmployeeProfileExtensionEditor
        profile={{
          employee_id: "EMP-8",
          employment_type: "FIXED_PAY",
          current_department_id: "DEP-1",
          current_designation_id: "DES-1",
          engagement_order_no: "FP/2026/009",
          engagement_order_date: "2026-04-12",
          date_of_initial_engagement: "2026-04-01",
          fixed_monthly_amount: 42000,
          mobile_primary: "9876543210",
        }}
        submitAction={submitAction}
      />
    );

    resolveEmploymentTypes({
      data: [
        {
          employment_type_code: "FIXED_PAY",
          name: "Fixed Pay",
          employment_class: "NON_REGULAR",
          eligible_for_service_book: false,
          requires_engagement_order: true,
          requires_contract_period: false,
          eligible_for_wages: false,
          eligible_for_fixed_remuneration: true,
        },
      ],
    });

    await waitFor(() => {
      expect(screen.getByLabelText("Engagement Order No")).toHaveValue("FP/2026/009");
      expect(screen.getByLabelText("Engagement Order Date")).toHaveValue("2026-04-12");
      expect(screen.getByLabelText("Engagement Start Date")).toHaveValue("2026-04-01");
      expect(screen.getByLabelText("Monthly Remuneration")).toHaveValue(42000);
    });
  });
});
