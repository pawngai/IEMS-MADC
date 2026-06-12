import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import DocumentManagementPage from "@/modules/documents/pages/DocumentManagementPage";

const mockDeleteDocument = vi.fn();
const mockUseDocumentsBrowser = vi.fn();

vi.mock("@/modules/documents/hooks/useDocumentsBrowser", () => ({
  __esModule: true,
  useDocumentsBrowser: (...args) => mockUseDocumentsBrowser(...args),
}));

vi.mock("@/modules/documents/api/documentsApi", () => ({
  __esModule: true,
  documentsAPI: {
    getFileUrl: (filename) => `/api/documents/files/${filename}`,
    getDownloadUrl: (filename) => `/api/documents/files/${filename}/download`,
    openDocument: vi.fn(),
    downloadDocument: vi.fn(),
  },
}));

vi.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

describe("DocumentManagementPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const mockSetLockStatusFilter = vi.fn();
    mockUseDocumentsBrowser.mockReturnValue({
      documents: [
        {
          filename: "doc-1.pdf",
          original_name: "Order.pdf",
          uploaded_at: "2026-04-10T00:00:00Z",
          file_size: 4096,
          document_type: "ORDER",
          source_context: "documents.management",
          uploaded_employee_code: "MADC-2024-0001",
          uploaded_employee_id: "EMP-001",
          subject_employee_code: "MADC-2024-0999",
          is_locked: false,
        },
      ],
      visibleDocuments: [
        {
          filename: "doc-1.pdf",
          original_name: "Order.pdf",
          uploaded_at: "2026-04-10T00:00:00Z",
          file_size: 4096,
          document_type: "ORDER",
          source_context: "documents.management",
          uploaded_employee_code: "MADC-2024-0001",
          uploaded_employee_id: "EMP-001",
          subject_employee_code: "MADC-2024-0999",
          is_locked: false,
        },
      ],
      documentsTotal: 1,
      documentsLoading: false,
      loadingMoreDocuments: false,
      hasMoreDocuments: false,
      documentQuery: "",
      setDocumentQuery: vi.fn(),
      uploaderQuery: "",
      setUploaderQuery: vi.fn(),
      documentTypeFilter: "",
      setDocumentTypeFilter: vi.fn(),
      documentTypeOptions: ["ORDER"],
      sourceContextFilter: "",
      setSourceContextFilter: vi.fn(),
      sourceContextOptions: ["documents.management"],
      lockStatusFilter: "ALL",
      setLockStatusFilter: mockSetLockStatusFilter,
      deletingDocument: null,
      loadDocuments: vi.fn(),
      loadMoreDocuments: vi.fn(),
      deleteDocument: mockDeleteDocument,
      formatSize: () => "4 KB",
      formatDate: () => "10/04/2026",
    });
  });

  test("renders document list with authenticated open and download actions", () => {
    render(<DocumentManagementPage />);

    expect(screen.getByTestId("document-management-page")).toBeInTheDocument();
    expect(screen.getByText("Document Management")).toBeInTheDocument();
    expect(screen.getByText("MADC-2024-0001")).toBeInTheDocument();
    expect(screen.getByText("MADC-2024-0999")).toBeInTheDocument();
    expect(screen.getByText("Belongs to")).toBeInTheDocument();
    // Open/Download are now buttons that stream the file through the
    // authenticated apiClient instead of plain <a href> navigation, which
    // would not attach the Bearer access token.
    const openButton = screen.getByRole("button", { name: "Open" });
    const downloadButton = screen.getByRole("button", { name: "Download" });
    expect(openButton).not.toHaveAttribute("href");
    expect(downloadButton).not.toHaveAttribute("href");
    expect(screen.queryByLabelText("Upload document")).not.toBeInTheDocument();
  });

  test("deletes unlocked documents from the management table", () => {
    render(<DocumentManagementPage />);

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(screen.getByText(/permanently removed/i)).toBeInTheDocument();

    const deleteButtons = screen.getAllByRole("button", { name: "Delete" });
    fireEvent.click(deleteButtons[deleteButtons.length - 1]);

    expect(mockDeleteDocument).toHaveBeenCalledWith("doc-1.pdf");
  });

  test("lets operators switch the lock-status filter", () => {
    render(<DocumentManagementPage />);

    fireEvent.click(screen.getByText("All statuses"));
    fireEvent.click(screen.getByText("Approved only"));

    expect(mockUseDocumentsBrowser.mock.results[0].value.setLockStatusFilter).toHaveBeenCalledWith("LOCKED");
  });

  test("lets operators filter by uploader", () => {
    render(<DocumentManagementPage />);

    fireEvent.change(screen.getByPlaceholderText("Filter by uploader code"), {
      target: { value: "MADC-2024-0001" },
    });

    expect(mockUseDocumentsBrowser.mock.results[0].value.setUploaderQuery).toHaveBeenCalledWith("MADC-2024-0001");
  });

  test("shows error state with retry button when document load fails", () => {
    mockUseDocumentsBrowser.mockReturnValue({
      ...mockUseDocumentsBrowser(),
      documents: [],
      visibleDocuments: [],
      documentsTotal: 0,
      documentsLoading: false,
      documentsError: "Server returned 503",
      loadDocuments: vi.fn(),
    });

    render(<DocumentManagementPage />);

    expect(screen.getByText("Failed to load documents")).toBeInTheDocument();
    expect(screen.getByText("Server returned 503")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  test("shows filter-aware empty state with clear-filters link when filters are active", () => {
    const mockSetDocumentQuery = vi.fn();
    mockUseDocumentsBrowser.mockReturnValue({
      ...mockUseDocumentsBrowser(),
      documents: [],
      visibleDocuments: [],
      documentsTotal: 0,
      documentsLoading: false,
      documentsError: null,
      documentQuery: "xyz",
      setDocumentQuery: mockSetDocumentQuery,
    });

    render(<DocumentManagementPage />);

    expect(screen.getByText("No documents match the current filters.")).toBeInTheDocument();
    const clearLink = screen.getByRole("button", { name: "Clear all filters" });
    expect(clearLink).toBeInTheDocument();
    fireEvent.click(clearLink);
    expect(mockSetDocumentQuery).toHaveBeenCalledWith("");
  });
});