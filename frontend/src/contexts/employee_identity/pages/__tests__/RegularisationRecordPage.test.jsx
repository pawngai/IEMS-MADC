import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import RegularisationRecordPage from "@/contexts/employee_identity/pages/RegularisationRecordPage";

const mockNavigate = vi.fn();
const mockGetProfile = vi.fn();
const mockGetServiceSummary = vi.fn();
const mockGetDepartments = vi.fn();
const mockGetOffices = vi.fn();
const mockGetDesignations = vi.fn();
const mockGetServices = vi.fn();
const mockCreateServiceRecord = vi.fn();
const mockUploadDocument = vi.fn();
const mockGetFileUrl = vi.fn();
const mockToastSuccess = vi.fn();
const mockToastError = vi.fn();

jest.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ pathname: "/employees/EMP-100/regularisation", state: null }),
    useParams: () => ({ employeeId: "EMP-100" }),
  };
});

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout-shell">{children}</div>,
}));

jest.mock("@/contexts/employee_profile", () => ({
  __esModule: true,
  employeeProfileApi: {
    get: (...args) => mockGetProfile(...args),
  },
}));

jest.mock("@/contexts/masters", () => ({
  __esModule: true,
  mastersAPI: {
    getDepartments: (...args) => mockGetDepartments(...args),
    getOffices: (...args) => mockGetOffices(...args),
    getDesignations: (...args) => mockGetDesignations(...args),
    getServices: (...args) => mockGetServices(...args),
  },
}));

jest.mock("@/contexts/service_book", () => ({
  __esModule: true,
  serviceRecordsApi: {
    getServiceSummary: (...args) => mockGetServiceSummary(...args),
    create: (...args) => mockCreateServiceRecord(...args),
  },
}));

jest.mock("@/contexts/documents", () => ({
  __esModule: true,
  documentsAPI: {
    upload: (...args) => mockUploadDocument(...args),
    getFileUrl: (...args) => mockGetFileUrl(...args),
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

jest.mock("sonner", () => ({
  __esModule: true,
  toast: {
    success: (...args) => mockToastSuccess(...args),
    error: (...args) => mockToastError(...args),
  },
}));

describe("RegularisationRecordPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetProfile.mockResolvedValue({ data: { full_name: "Demo Employee" } });
    mockGetServiceSummary.mockResolvedValue({
      data: {
        current_employment_type_code: "CONTRACT",
        current_department_id: "DEP-1",
        current_office_id: "OFF-1",
        current_designation_id: "DES-1",
        current_service_id: "SVC-1",
      },
    });
    mockGetDepartments.mockResolvedValue({ data: [{ id: "DEP-1", name: "Finance" }] });
    mockGetOffices.mockResolvedValue({ data: [{ id: "OFF-1", name: "HQ" }] });
    mockGetDesignations.mockResolvedValue({ data: [{ id: "DES-1", name: "Consultant" }] });
    mockGetServices.mockResolvedValue({ data: [{ id: "SVC-1", name: "Administrative" }] });
    mockCreateServiceRecord.mockResolvedValue({ data: { service_event_id: "SR-1" } });
    mockUploadDocument.mockResolvedValue({
      data: {
        document_id: "DOC-1",
        filename: "regularisation-order.pdf",
        original_name: "regularisation-order.pdf",
      },
    });
    mockGetFileUrl.mockImplementation((filename) => `/files/${filename}`);
  });

  test("does not render Sanctioned Post ID or Document IDs free-text inputs", async () => {
    render(<RegularisationRecordPage />);

    await screen.findByText("Regularisation Record");

    expect(screen.queryByText("Sanctioned Post ID")).not.toBeInTheDocument();
    expect(screen.queryByText("Document IDs")).not.toBeInTheDocument();
  });

  test("uploads a regularisation document and submits attached document_ids without sanctioned_post_id", async () => {
    render(<RegularisationRecordPage />);

    await screen.findByText("Regularisation Record");
    await waitFor(() => expect(mockGetServiceSummary).toHaveBeenCalled());

    fireEvent.change(screen.getByLabelText("Effective Date"), { target: { value: "2026-06-01" } });
    fireEvent.change(screen.getByLabelText("Regularisation Order No"), { target: { value: "REG/2026/001" } });
    fireEvent.change(screen.getByLabelText("Regularisation Order Date"), { target: { value: "2026-05-15" } });

    fireEvent.change(screen.getByTestId("regularisation-document-upload"), {
      target: { files: [new File(["pdf"], "regularisation-order.pdf", { type: "application/pdf" })] },
    });

    await waitFor(() => {
      expect(mockUploadDocument).toHaveBeenCalledWith(
        expect.any(File),
        expect.objectContaining({
          source_context: "service_book.records.regularisation",
          category: "REGULARISATION_ORDER",
          document_type: "ORDER",
        })
      );
    });

    expect(await screen.findByTestId("regularisation-attached-documents")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Create Regularisation Draft" }));

    await waitFor(() => {
      expect(mockCreateServiceRecord).toHaveBeenCalled();
    });
    const submitted = mockCreateServiceRecord.mock.calls[0][0];
    expect(submitted.document_ids).toEqual(["DOC-1"]);
    expect(submitted.payload).not.toHaveProperty("sanctioned_post_id");
    expect(submitted.payload.new_employment_type_code).toBe("REGULAR");
    expect(submitted.payload.regularisation_order_no).toBe("REG/2026/001");
  });

  test("submits without documents when none are attached", async () => {
    render(<RegularisationRecordPage />);

    await screen.findByText("Regularisation Record");
    await waitFor(() => expect(mockGetServiceSummary).toHaveBeenCalled());

    fireEvent.change(screen.getByLabelText("Effective Date"), { target: { value: "2026-06-01" } });
    fireEvent.change(screen.getByLabelText("Regularisation Order No"), { target: { value: "REG/2026/002" } });
    fireEvent.change(screen.getByLabelText("Regularisation Order Date"), { target: { value: "2026-05-15" } });

    fireEvent.click(screen.getByRole("button", { name: "Create Regularisation Draft" }));

    await waitFor(() => {
      expect(mockCreateServiceRecord).toHaveBeenCalled();
    });
    expect(mockCreateServiceRecord.mock.calls[0][0].document_ids).toEqual([]);
  });
});
