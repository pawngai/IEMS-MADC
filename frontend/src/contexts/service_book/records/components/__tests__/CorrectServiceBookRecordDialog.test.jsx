import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import CorrectServiceBookRecordDialog from "@/contexts/service_book/records/components/CorrectServiceBookRecordDialog";

const mockCorrectEvent = vi.fn();
const mockToastError = vi.fn();

vi.mock("@/contexts/service_book/records/api/serviceBookRecordsApi", () => ({
  __esModule: true,
  serviceBookRecordsAPI: {
    correctEvent: (...args) => mockCorrectEvent(...args),
  },
}));

vi.mock("sonner", () => ({
  __esModule: true,
  toast: {
    error: (...args) => mockToastError(...args),
  },
}));

vi.mock("@/shared/ui/sheet", () => ({
  __esModule: true,
  Sheet: ({ children }) => <div>{children}</div>,
  SheetContent: ({ children }) => <div>{children}</div>,
  SheetHeader: ({ children }) => <div>{children}</div>,
  SheetTitle: ({ children }) => <h2>{children}</h2>,
  SheetDescription: ({ children }) => <p>{children}</p>,
  SheetFooter: ({ children }) => <div>{children}</div>,
}));

describe("CorrectServiceBookRecordDialog", () => {
  test("submits nested CPC payload sections as objects instead of JSON strings", async () => {
    mockCorrectEvent.mockResolvedValueOnce({});

    render(
      <CorrectServiceBookRecordDialog
        event={{
          id: "evt-1",
          event_type: "CPC_PAY_FIXATION",
          payload: {
            pre_revised_pay: {
              pay_scale: "975-25-1150-30-1660",
              basic_pay: "975",
            },
          },
        }}
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    const objectEditor = screen.getByLabelText("Corrected value for Pre Revised Pay");
    expect(objectEditor.tagName).toBe("TEXTAREA");

    fireEvent.change(objectEditor, {
      target: {
        value: JSON.stringify({ pay_scale: "3200-85-4900", basic_pay: "3200" }, null, 2),
      },
    });
    fireEvent.change(screen.getByLabelText("Reason for Correction *"), {
      target: { value: "Fix mapped CPC pay scale" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply Correction" }));

    await waitFor(() => {
      expect(mockCorrectEvent).toHaveBeenCalledWith(
        "evt-1",
        expect.objectContaining({
          corrected_payload: {
            pre_revised_pay: {
              pay_scale: "3200-85-4900",
              basic_pay: "3200",
            },
          },
        }),
      );
    });
  });

  test("uses a readable event label instead of exposing the raw event id", () => {
    render(
      <CorrectServiceBookRecordDialog
        event={{
          id: "c35c6d40-5d5e-4e60-80c2-5dc8559f5472",
          event_type: "PROMOTION",
          payload: { promotion_type: "regular" },
        }}
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByText("Correct the data for the promotion event. Provide the corrected values and a reason for the correction."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Corrected field")).toHaveDisplayValue("Promotion Type");
    expect(screen.getByLabelText("Corrected value for Promotion Type")).toHaveDisplayValue("Regular");
    expect(screen.getByRole("option", { name: "Ad Hoc" })).toBeInTheDocument();
    expect(screen.queryByDisplayValue("promotion_type")).not.toBeInTheDocument();
    expect(screen.queryByText(/c35c6d40-5d5e-4e60-80c2-5dc8559f5472/i)).not.toBeInTheDocument();
  });

  test("treats known CPC pay fields as typed fields instead of custom text", () => {
    render(
      <CorrectServiceBookRecordDialog
        event={{
          id: "c35c6d40-5d5e-4e60-80c2-5dc8559f5472",
          event_type: "INCREMENT",
          payload: {
            cpc: "7TH_CPC",
            to_pay_level: "Level 4",
          },
        }}
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getAllByLabelText("Corrected field")[0]).toHaveDisplayValue("Pay Commission (CPC)");
    expect(screen.getByLabelText("Corrected value for Pay Commission (CPC)")).toHaveDisplayValue("7th CPC (2016)");
    expect(screen.getAllByLabelText("Corrected field")[1]).toHaveDisplayValue("To Pay Level");
    expect(screen.getByLabelText("Corrected value for To Pay Level")).toHaveDisplayValue("Level 4");
    expect(screen.queryByDisplayValue("cpc")).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue("to_pay_level")).not.toBeInTheDocument();
  });
});