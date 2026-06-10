import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import ServiceBookEntryDetails from "@/contexts/service_book/components/ServiceBookEntryDetails";

const renderPartContent = vi.fn(() => <div data-testid="part-content" />);

vi.mock("@/contexts/service_book/components/partContentFactory", () => ({
  __esModule: true,
  default: (props) => renderPartContent(props),
}));

describe("ServiceBookEntryDetails", () => {
  const baseProps = {
    partInfo: { name: "Bio-Data", description: "Basic personal information" },
    employeeId: "EMP-100",
    onSave: vi.fn(),
    isSaving: false,
    onReload: vi.fn(),
    canWrite: true,
    canAddAuditComment: false,
    masterOptions: {},
    onWorkflowAction: vi.fn(),
    can: () => true,
    Permissions: {},
    forceReadOnly: false,
  };

  test("keeps Part I read-only on the projection screen", () => {
    render(<ServiceBookEntryDetails {...baseProps} partKey="I" partData={null} />);

    expect(screen.queryByRole("button", { name: /add data/i })).not.toBeInTheDocument();
    expect(screen.getByText("Read-only")).toBeInTheDocument();
  });

  test("keeps Part II-A read-only on the projection screen", () => {
    render(<ServiceBookEntryDetails {...baseProps} partKey="II-A" partData={null} />);

    expect(screen.queryByRole("button", { name: /add data/i })).not.toBeInTheDocument();
  });

  test("keeps Part II-B read-only on the projection screen", () => {
    render(<ServiceBookEntryDetails {...baseProps} partKey="II-B" partData={null} />);

    expect(screen.queryByRole("button", { name: /add data/i })).not.toBeInTheDocument();
  });

  test("does not pass write or workflow actions through for Part III", () => {
    renderPartContent.mockClear();

    render(<ServiceBookEntryDetails {...baseProps} partKey="III" partData={null} />);

    expect(renderPartContent).toHaveBeenCalled();
    expect(renderPartContent.mock.lastCall[0]).toMatchObject({
      partKey: "III",
      canWrite: false,
      onWorkflowAction: undefined,
    });
  });

  test("shows workflow metadata as timestamps only", () => {
    render(
      <ServiceBookEntryDetails
        {...baseProps}
        partKey="II-A"
        partData={{
          _meta: {
            created_by: "user-created",
            created_at: "2026-03-16T10:00:00Z",
            submitted_by: "user-submitted",
            submitted_at: "2026-03-16T11:00:00Z",
            verified_by: "user-verified",
            verified_at: "2026-03-16T12:00:00Z",
            approved_by: "user-approved",
            approved_at: "2026-03-16T13:00:00Z",
            locked_by: "user-locked",
            locked_at: "2026-03-16T14:00:00Z",
            workflow_state: "LOCKED",
            status: "LOCKED",
          },
        }}
      />,
    );

    expect(screen.getByText(/Created:.*16 Mar 2026/)).toBeInTheDocument();
    expect(screen.getByText(/Submitted:.*16 Mar 2026/)).toBeInTheDocument();
    expect(screen.getByText(/Verified:.*16 Mar 2026/)).toBeInTheDocument();
    expect(screen.getByText(/Approved:.*16 Mar 2026/)).toBeInTheDocument();
    expect(screen.getByText(/Locked:.*16 Mar 2026/)).toBeInTheDocument();
    expect(screen.queryByText(/user-created|user-submitted|user-verified|user-approved|user-locked/i)).not.toBeInTheDocument();
  });

  test("renders readable workflow badge labels", () => {
    render(
      <ServiceBookEntryDetails
        {...baseProps}
        partKey="II-A"
        partData={{
          _meta: {
            workflow_state: "DRAFT",
            status: "DRAFT",
          },
        }}
      />,
    );

    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.queryByText("DRAFT")).not.toBeInTheDocument();
  });
});