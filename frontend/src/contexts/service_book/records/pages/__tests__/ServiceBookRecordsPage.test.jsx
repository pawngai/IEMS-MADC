import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import ServiceBookRecordsPage from "@/contexts/service_book/records/pages/ServiceBookRecordsPage";

const { timelineAttachEvent } = vi.hoisted(() => ({
  timelineAttachEvent: {
    id: "SE-ATTACH-1",
    service_event_id: "SE-ATTACH-1",
    event_type: "PROMOTION",
    payload: { order_no: "MADC/HR/2026/001" },
  },
}));

const mockCan = vi.fn();
const mockGetEventStream = vi.fn();
const mockGetIdentity = vi.fn();

vi.mock("react-router-dom", () => ({
  __esModule: true,
  useParams: () => ({ employeeId: "MADC-2020-0001" }),
  Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a>,
}));

vi.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

vi.mock("@/contexts/identity_access/model/authContext", () => ({
  __esModule: true,
  useAuth: () => ({
    user: { name: "Global Data Entry" },
    can: (...args) => mockCan(...args),
  }),
}));

vi.mock("@/contexts/service_book/records/api/serviceBookRecordsApi", () => ({
  __esModule: true,
  serviceBookRecordsAPI: {
    getEventStream: (...args) => mockGetEventStream(...args),
    getEmployeeIdentity: (...args) => mockGetIdentity(...args),
  },
}));

vi.mock("@/contexts/service_book/records/components/ServiceRecordTimeline", () => ({
  __esModule: true,
  default: ({ onAttach }) => (
    <div data-testid="service-record-timeline">
      <button type="button" onClick={() => onAttach?.(timelineAttachEvent)}>
        Open Attach Dialog
      </button>
    </div>
  ),
}));

vi.mock("@/contexts/service_book/records/components/RecordServiceBookRecordDialog", () => ({
  __esModule: true,
  default: () => null,
}));

vi.mock("@/contexts/service_book/records/components/CorrectServiceBookRecordDialog", () => ({
  __esModule: true,
  default: () => null,
}));

vi.mock("@/contexts/service_book/records/components/VoidServiceBookRecordDialog", () => ({
  __esModule: true,
  default: () => null,
}));

vi.mock("@/contexts/service_book/records/components/AttachDocumentDialog", () => ({
  __esModule: true,
  default: ({ event }) => (
    <div data-testid="attach-document-dialog">
      Attach dialog for {event?.id || event?.service_event_id}
    </div>
  ),
}));

vi.mock("sonner", () => ({
  __esModule: true,
  toast: {
    success: vi.fn(),
  },
}));

describe("ServiceBookRecordsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCan.mockReturnValue(true);
    mockGetEventStream.mockResolvedValue({ data: [] });
    mockGetIdentity.mockResolvedValue({
      data: {
        full_name: "Demo Employee",
        employee_code: "MADC-2020-0001",
        employment_type: "REGULAR",
      },
    });
  });

  test("renders employee identity in the header when identity data is available", async () => {
    render(<ServiceBookRecordsPage />);

    expect(await screen.findByText("Demo Employee")).toBeInTheDocument();
    expect(screen.getByText("MADC-2020-0001")).toBeInTheDocument();
    expect(screen.queryByText("Employee: MADC-2020-0001")).not.toBeInTheDocument();

    await waitFor(() => {
      expect(mockGetIdentity).toHaveBeenCalledWith("MADC-2020-0001");
    });
  });

  test("renders not-applicable state for non-regular employees", async () => {
    mockGetIdentity.mockResolvedValue({
      data: {
        full_name: "Contract Worker",
        employee_code: "MADC-2020-0002",
        employment_type: "CONTRACTUAL",
      },
    });
    mockGetEventStream.mockRejectedValue({
      response: {
        data: {
          detail: {
            message: "Service Book records are only maintained for REGULAR employees.",
          },
        },
      },
    });

    render(<ServiceBookRecordsPage />);

    expect(await screen.findByTestId("service-records-not-applicable")).toBeInTheDocument();
    expect(screen.getByText("Service Book records are only maintained for REGULAR employees.")).toBeInTheDocument();
    expect(screen.queryByTestId("record-service-record-btn")).not.toBeInTheDocument();
  });

  test("opens the attach dialog with the selected event from the timeline", async () => {
    mockGetEventStream.mockResolvedValue({
      data: [
        {
          id: timelineAttachEvent.id,
          service_event_id: timelineAttachEvent.service_event_id,
          event_type: timelineAttachEvent.event_type,
          payload: timelineAttachEvent.payload,
          recorded_at: "2026-04-10T09:00:00Z",
        },
      ],
    });

    render(<ServiceBookRecordsPage />);

    expect(await screen.findByTestId("service-record-timeline")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open Attach Dialog" }));

    expect(await screen.findByTestId("attach-document-dialog")).toHaveTextContent(
      "Attach dialog for SE-ATTACH-1"
    );
  });
});