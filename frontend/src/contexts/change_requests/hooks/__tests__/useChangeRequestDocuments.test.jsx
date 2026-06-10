import React, { useState } from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import {
  getDocumentFilterOptions,
  useChangeRequestDocuments,
} from "@/contexts/change_requests/hooks/useChangeRequestDocuments";
import { documentsAPI } from "@/contexts/documents/api/documentsApi";

const mockRemove = jest.fn();
const mockUpload = jest.fn();
const mockToastError = jest.fn();
const mockToastSuccess = jest.fn();

function createDeferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

jest.mock("@/contexts/documents/api/documentsApi", () => ({
  __esModule: true,
  documentsAPI: {
    list: jest.fn(),
    remove: (...args) => mockRemove(...args),
    upload: (...args) => mockUpload(...args),
  },
}));

jest.mock("sonner", () => ({
  toast: {
    error: (...args) => mockToastError(...args),
    success: (...args) => mockToastSuccess(...args),
    info: jest.fn(),
  },
}));

function Harness() {
  const [formAttachments, setFormAttachments] = useState([{ filename: "locked.pdf" }]);
  const docs = useChangeRequestDocuments({ open: true });
  const file = new File(["%PDF-1.4"], "supporting-proof.pdf", { type: "application/pdf" });

  return (
    <div>
      <div data-testid="attachment-count">{formAttachments.length}</div>
      <div data-testid="document-count">{docs.documents.length}</div>
      <div data-testid="document-total">{docs.documentsTotal}</div>
      <div data-testid="has-more">{docs.hasMoreDocuments ? "yes" : "no"}</div>
      <div data-testid="type-options">{docs.documentTypeOptions.join(",")}</div>
      <div data-testid="source-options">{docs.sourceContextOptions.join(",")}</div>
      <div data-testid="document-names">{docs.documents.map((item) => item.filename).join(",")}</div>
      <input
        aria-label="Document query"
        value={docs.documentQuery}
        onChange={(event) => docs.setDocumentQuery(event.target.value)}
      />
      <button type="button" onClick={() => docs.setDocumentTypeFilter("CERTIFICATE")}>
        Filter Type
      </button>
      <button
        type="button"
        onClick={() => docs.setSourceContextFilter("change_requests.upload")}
      >
        Filter Source
      </button>
      <button
        type="button"
        onClick={() => docs.handleDeleteDocument("locked.pdf", { setFormAttachments })}
      >
        Delete
      </button>
      <button
        type="button"
        onClick={() => docs.uploadFile(file, { setFormAttachments })}
      >
        Upload
      </button>
      <button type="button" onClick={() => docs.loadMoreDocuments()}>
        Load More
      </button>
    </div>
  );
}

describe("useChangeRequestDocuments", () => {
  afterEach(() => {
    jest.useRealTimers();
  });

  beforeEach(() => {
    jest.clearAllMocks();
    documentsAPI.list.mockResolvedValue({
      data: {
        items: [],
        total: 0,
        available_filters: {
          document_types: [],
          source_contexts: [],
        },
      },
    });
  });

  test("debounces filename search before reloading documents", async () => {
    jest.useFakeTimers();

    render(<Harness />);

    await waitFor(() => {
      expect(documentsAPI.list).toHaveBeenCalledTimes(1);
    });

    documentsAPI.list.mockClear();

    await act(async () => {
      fireEvent.change(screen.getByRole("textbox", { name: "Document query" }), {
        target: { value: "certificate" },
      });
    });

    await act(async () => {
      jest.advanceTimersByTime(299);
    });
    expect(documentsAPI.list).not.toHaveBeenCalled();

    await act(async () => {
      jest.advanceTimersByTime(1);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(documentsAPI.list).toHaveBeenCalledWith({
        query: "certificate",
        document_type: undefined,
        source_context: undefined,
        limit: 50,
        offset: 0,
      });
    });
  });

  test("collects sorted document filter options from metadata-bearing documents", () => {
    expect(
      getDocumentFilterOptions(
        [
          { document_type: "CERTIFICATE" },
          { document_type: "ORDER" },
          { document_type: "CERTIFICATE" },
          { document_type: "" },
        ],
        "document_type"
      )
    ).toEqual(["CERTIFICATE", "ORDER"]);
  });

  test("requests server-backed document filters when classification changes", async () => {
    render(<Harness />);

    await waitFor(() => {
      expect(documentsAPI.list).toHaveBeenCalledWith({
        query: undefined,
        document_type: undefined,
        source_context: undefined,
        limit: 50,
        offset: 0,
      });
    });

    fireEvent.click(screen.getByRole("button", { name: "Filter Type" }));

    await waitFor(() => {
      expect(documentsAPI.list).toHaveBeenCalledWith({
        query: undefined,
        document_type: "CERTIFICATE",
        source_context: undefined,
        limit: 50,
        offset: 0,
      });
    });

    fireEvent.click(screen.getByRole("button", { name: "Filter Source" }));

    await waitFor(() => {
      expect(documentsAPI.list).toHaveBeenCalledWith({
        query: undefined,
        document_type: "CERTIFICATE",
        source_context: "change_requests.upload",
        limit: 50,
        offset: 0,
      });
    });
  });

  test("ignores stale document list responses after a newer filter request completes", async () => {
    const initialRequest = createDeferred();
    const filteredRequest = createDeferred();

    documentsAPI.list
      .mockImplementationOnce(() => initialRequest.promise)
      .mockImplementationOnce(() => filteredRequest.promise);

    render(<Harness />);

    await waitFor(() => {
      expect(documentsAPI.list).toHaveBeenCalledWith({
        query: undefined,
        document_type: undefined,
        source_context: undefined,
        limit: 50,
        offset: 0,
      });
    });

    fireEvent.click(screen.getByRole("button", { name: "Filter Type" }));

    await waitFor(() => {
      expect(documentsAPI.list).toHaveBeenLastCalledWith({
        query: undefined,
        document_type: "CERTIFICATE",
        source_context: undefined,
        limit: 50,
        offset: 0,
      });
    });

    await act(async () => {
      filteredRequest.resolve({
        data: {
          items: [{ filename: "filtered.pdf", document_type: "CERTIFICATE" }],
          total: 1,
          available_filters: {
            document_types: ["CERTIFICATE"],
            source_contexts: [],
          },
        },
      });
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId("document-names")).toHaveTextContent("filtered.pdf");
    });

    await act(async () => {
      initialRequest.resolve({
        data: {
          items: [{ filename: "stale.pdf" }],
          total: 1,
          available_filters: {
            document_types: [],
            source_contexts: [],
          },
        },
      });
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId("document-names")).toHaveTextContent("filtered.pdf");
      expect(screen.getByTestId("document-names")).not.toHaveTextContent("stale.pdf");
    });
  });

  test("prefers server-provided filter options over the loaded page metadata", async () => {
    documentsAPI.list.mockResolvedValueOnce({
      data: {
        items: [
          { filename: "page-item.pdf", document_type: "CERTIFICATE", source_context: "change_requests.upload" },
        ],
        total: 1,
        available_filters: {
          document_types: ["CERTIFICATE", "ORDER"],
          source_contexts: ["change_requests.upload", "service_book.part_iia"],
        },
      },
    });

    render(<Harness />);

    await waitFor(() => {
      expect(screen.getByTestId("type-options")).toHaveTextContent("CERTIFICATE,ORDER");
      expect(screen.getByTestId("source-options")).toHaveTextContent(
        "change_requests.upload,service_book.part_iia"
      );
    });
  });

  test("loads the next document page when more results are available", async () => {
    documentsAPI.list
      .mockResolvedValueOnce({
        data: {
          items: Array.from({ length: 50 }, (_, index) => ({ filename: `doc-${index + 1}.pdf` })),
          total: 75,
        },
      })
      .mockResolvedValueOnce({
        data: {
          items: Array.from({ length: 25 }, (_, index) => ({ filename: `doc-${index + 51}.pdf` })),
          total: 75,
        },
      });

    render(<Harness />);

    await waitFor(() => {
      expect(screen.getByTestId("document-count")).toHaveTextContent("50");
      expect(screen.getByTestId("document-total")).toHaveTextContent("75");
      expect(screen.getByTestId("has-more")).toHaveTextContent("yes");
    });

    fireEvent.click(screen.getByRole("button", { name: "Load More" }));

    await waitFor(() => {
      expect(documentsAPI.list).toHaveBeenLastCalledWith({
        query: undefined,
        document_type: undefined,
        source_context: undefined,
        limit: 50,
        offset: 50,
      });
      expect(screen.getByTestId("document-count")).toHaveTextContent("75");
      expect(screen.getByTestId("has-more")).toHaveTextContent("no");
    });
  });

  test("uses the structured DOCUMENT_LOCKED error instead of parsing message text", async () => {
    mockRemove.mockRejectedValue({
      response: {
        data: {
          detail: {
            error_code: "DOCUMENT_LOCKED",
            message: "Locked documents are immutable and cannot be deleted",
            lock_reason: "APPROVED_CHANGE_REQUEST",
            locked_by_request_id: "CR-100",
            locked_status: "APPROVED",
          },
        },
      },
    });

    render(<Harness />);

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalledWith("Approved document cannot be deleted");
    });

    expect(screen.getByTestId("attachment-count")).toHaveTextContent("1");
  });

  test("uploads change-request documents with source context metadata", async () => {
    mockUpload.mockResolvedValue({
      data: {
        success: true,
        url: "/api/documents/files/supporting-proof.pdf",
        filename: "supporting-proof.pdf",
        original_name: "supporting-proof.pdf",
        file_size: 128,
        content_type: "application/pdf",
      },
    });

    render(<Harness />);

    fireEvent.click(screen.getByRole("button", { name: "Upload" }));

    await waitFor(() => {
      expect(mockUpload).toHaveBeenCalledWith(
        expect.any(File),
        {
          source_context: "change_requests.upload",
        }
      );
    });
  });
});