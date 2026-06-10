import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import VoidServiceBookRecordDialog from "@/contexts/service_book/records/components/VoidServiceBookRecordDialog";

vi.mock("@/shared/ui/sheet", () => ({
  __esModule: true,
  Sheet: ({ children }) => <div>{children}</div>,
  SheetContent: ({ children }) => <div>{children}</div>,
  SheetHeader: ({ children }) => <div>{children}</div>,
  SheetTitle: ({ children }) => <h2>{children}</h2>,
  SheetDescription: ({ children }) => <p>{children}</p>,
  SheetFooter: ({ children }) => <div>{children}</div>,
}));

describe("VoidServiceBookRecordDialog", () => {
  test("uses a readable event label instead of exposing the raw event id", () => {
    render(
      <VoidServiceBookRecordDialog
        event={{
          id: "c35c6d40-5d5e-4e60-80c2-5dc8559f5472",
          event_type: "PAY",
          payload: { remarks: "Annual increment for FY 2025-26" },
        }}
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByText("This will permanently void the increment event. The event will remain in the record but will be marked as voided and will no longer affect the service book read model."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/c35c6d40-5d5e-4e60-80c2-5dc8559f5472/i)).not.toBeInTheDocument();
  });
});