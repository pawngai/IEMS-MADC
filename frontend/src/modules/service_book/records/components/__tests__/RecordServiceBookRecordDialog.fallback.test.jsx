import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, test, vi, beforeEach } from "vitest";

const mockGetRecordSchema = vi.fn();
const mockGetEventStream = vi.fn();
const mockRecordEvent = vi.fn();
const mockUploadLinkedDocument = vi.fn();
const mockAttachDocument = vi.fn();

vi.mock("@/modules/service_book/records/api/serviceBookRecordsApi", () => ({
  __esModule: true,
  serviceBookRecordsAPI: {
    getRecordSchema: (...args) => mockGetRecordSchema(...args),
    getEventStream: (...args) => mockGetEventStream(...args),
    recordEvent: (...args) => mockRecordEvent(...args),
    uploadLinkedDocument: (...args) => mockUploadLinkedDocument(...args),
    attachDocument: (...args) => mockAttachDocument(...args),
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

import RecordServiceBookRecordDialog from "@/modules/service_book/records/components/RecordServiceBookRecordDialog";

describe("RecordServiceBookRecordDialog fallback mode", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetEventStream.mockResolvedValue({ data: [] });
    mockUploadLinkedDocument.mockResolvedValue({
      data: {
        document_id: "doc-100",
        metadata: { document_type: "ORDER" },
      },
    });
    mockAttachDocument.mockResolvedValue({ data: { ok: true } });
  });

  test("shows fallback warning when live schema is unavailable", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByText("Live event schema is unavailable. Using offline fallback schema.")
      ).toBeInTheDocument();
    });
  });

  test("renders readable labels for select options in fallback fields", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText("Event Category"), {
      target: { value: "PROMOTION" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("Promotion Type *")).toBeInTheDocument();
    });

    const promotionTypeSelect = screen.getByLabelText("Promotion Type *");
    const optionLabels = Array.from(promotionTypeSelect.querySelectorAll("option")).map((option) => option.textContent);

    expect(optionLabels).toEqual(["Select promotion type", "Officiating", "Ad Hoc", "Regular"]);
    expect(screen.queryByText("ad_hoc")).not.toBeInTheDocument();
  });

  test("shows guided placeholders for visible appointment fields in fallback mode", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText("Appointment Order No *")).toBeInTheDocument();
    });

    expect(screen.getByLabelText("Service")).toBeInTheDocument();
    expect(screen.getByLabelText("Grade")).toBeInTheDocument();
    expect(screen.getByLabelText("Service Group *")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., MADC/Est/2020/1234")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., Lower Division Clerk (LDC)")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., MADC Secretariat, Kolasib")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., General service")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., Group A")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., Senior Grade")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Optional notes shown with this event")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Select pay level" })).toBeInTheDocument();
  });

  test("shows target grade for promotion in fallback mode", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(await screen.findByLabelText("Event Category"), {
      target: { value: "PROMOTION" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("To Grade")).toBeInTheDocument();
    });

    expect(screen.getByLabelText("Promotion Type *")).toBeInTheDocument();
    expect(screen.getByLabelText("To Service")).toBeInTheDocument();
    expect(screen.getByLabelText("To Service Group")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., General service")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., Group B")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., Selection Grade")).toBeInTheDocument();
  });

  test("records custom events with manually added detail fields", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockRecordEvent.mockResolvedValueOnce({ data: { ok: true } });
    const onSuccess = vi.fn();

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={onSuccess}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(await screen.findByLabelText("Event Category"), {
      target: { value: "CUSTOM" },
    });

    await waitFor(() => {
      expect(screen.getByText("Add the event detail fields manually for this custom event.")).toBeInTheDocument();
    });

    expect(screen.queryByLabelText("Pay Commission (CPC)")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Custom detail field name 1"), {
      target: { value: "event_title" },
    });
    fireEvent.change(screen.getByLabelText("Custom detail field value 1"), {
      target: { value: "Special assignment" },
    });
    fireEvent.change(screen.getByLabelText("Remarks"), {
      target: { value: "Manual custom payload" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Record Event" }));

    await waitFor(() => {
      expect(mockRecordEvent).toHaveBeenCalledWith({
        employee_id: "EMP-100",
        event_type: "CUSTOM",
        part_code: "IV",
        payload: {
          event_title: "Special assignment",
          remarks: "Manual custom payload",
        },
        effective_from: null,
        effective_to: null,
      });
    });

    expect(onSuccess).toHaveBeenCalled();
  });

  test("keeps the upload section available after switching categories", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    expect(await screen.findByLabelText("Upload New Document")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Event Category"), {
      target: { value: "CUSTOM" },
    });

    await waitFor(() => {
      expect(screen.getByText("Add the event detail fields manually for this custom event.")).toBeInTheDocument();
    });

    expect(screen.getByLabelText("Upload New Document")).toBeInTheDocument();
    expect(screen.getByLabelText("Document Type")).toHaveValue("ORDER");
  });

  test("uploads and attaches a document after recording a custom event", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockRecordEvent.mockResolvedValueOnce({
      data: {
        service_event_id: "se-100",
        event_type: "CUSTOM",
      },
    });
    const onSuccess = vi.fn();
    const file = new File(["order copy"], "custom-order.pdf", { type: "application/pdf" });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={onSuccess}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(await screen.findByLabelText("Event Category"), {
      target: { value: "CUSTOM" },
    });

    await waitFor(() => {
      expect(screen.getByText("Add the event detail fields manually for this custom event.")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Custom detail field name 1"), {
      target: { value: "event_title" },
    });
    fireEvent.change(screen.getByLabelText("Custom detail field value 1"), {
      target: { value: "Special assignment" },
    });
    fireEvent.change(screen.getByLabelText("Document Type"), {
      target: { value: "notification" },
    });
    fireEvent.change(screen.getByLabelText("Category (optional)"), {
      target: { value: "custom order" },
    });
    fireEvent.change(screen.getByLabelText("Upload New Document"), {
      target: { files: [file] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Record Event" }));

    await waitFor(() => {
      expect(mockRecordEvent).toHaveBeenCalled();
      expect(mockUploadLinkedDocument).toHaveBeenCalledWith(file, {
        entity_type: "SERVICE_RECORD",
        entity_id: "se-100",
        document_type: "NOTIFICATION",
        category: "CUSTOM_ORDER",
        source_context: "service_book.records.attach",
      });
      expect(mockAttachDocument).toHaveBeenCalledWith("se-100", {
        service_event_id: "se-100",
        document_id: "doc-100",
        document_type: "ORDER",
      });
    });

    expect(onSuccess).toHaveBeenCalledWith({
      service_event_id: "se-100",
      event_type: "CUSTOM",
    });
  });

  test("derives CPC fixation from basic pay from the latest recorded pay context", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "INCREMENT",
          effective_from: "2026-04-01",
          payload: {
            cpc: "6TH_CPC",
            pay_band: "PB-2 (9300-34800)",
            grade_pay: "4200",
            to_basic_pay: 26300,
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText("Event Category"), {
      target: { value: "CPC_PAY_FIXATION" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("From Basic Pay *")).toHaveValue(26300);
    });
    const fromBasicPayInput = screen.getByLabelText("From Basic Pay *");
    expect(fromBasicPayInput).toHaveAttribute("readonly");
  });

  test("does not offer 7th CPC in the source commission list for CPC fixation", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText("Event Category"), {
      target: { value: "CPC_PAY_FIXATION" },
    });

    const fromCpcSelect = await screen.findByLabelText("From Pay Commission (CPC) *");
    const optionLabels = Array.from(fromCpcSelect.querySelectorAll("option")).map((option) => option.textContent);

    expect(optionLabels).toEqual([
      "Select from pay commission",
      "4th CPC (1986)",
      "5th CPC (1997)",
      "6th CPC (2006)",
    ]);
    expect(optionLabels).not.toContain("7th CPC (2016)");
  });

  test("clears derived from basic pay when selected from CPC does not match latest pay context", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "INCREMENT",
          effective_from: "2026-04-01",
          payload: {
            cpc: "7TH_CPC",
            pay_level: "Level 4",
            pay_cell_index: 5,
            to_basic_pay: 26300,
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText("Event Category"), {
      target: { value: "CPC_PAY_FIXATION" },
    });

    fireEvent.change(await screen.findByLabelText("From Pay Commission (CPC) *"), {
      target: { value: "6TH_CPC" },
    });

    const fromBasicPayInput = await screen.findByLabelText("From Basic Pay *");

    expect(fromBasicPayInput).toHaveDisplayValue("");
  });

  test("calculates 6th CPC fixation basic pay from fitment against the pre-revised basic pay", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "INCREMENT",
          recorded_at: "2026-04-07T23:19:00Z",
          payload: {
            cpc: "5TH_CPC",
            increment_date: "2005-07-01",
            pay_scale: "4000 100 6000",
            from_basic_pay: "4500",
            to_basic_pay: "4600",
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText("Event Category"), {
      target: { value: "CPC_PAY_FIXATION" },
    });

    fireEvent.change(await screen.findByLabelText("From Pay Commission (CPC) *"), {
      target: { value: "5TH_CPC" },
    });
    fireEvent.change(screen.getByLabelText("To Pay Commission (CPC) *"), {
      target: { value: "6TH_CPC" },
    });
    fireEvent.change(screen.getByLabelText("Pay Band *"), {
      target: { value: "PB-1 (5200-20200)" },
    });
    fireEvent.change(screen.getByLabelText("Grade Pay *"), {
      target: { value: "2400" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("From Pay Scale")).toHaveValue("4000-100-6000");
      expect(screen.getByLabelText("From Basic Pay *")).toHaveValue(4600);
      expect(screen.getByLabelText("Basic Pay *")).toHaveValue("10960");
    });

    expect(screen.getByLabelText("From Pay Scale")).toBeDisabled();
    expect(screen.getByLabelText("Pay Band *")).not.toBeDisabled();
    expect(screen.getByLabelText("Grade Pay *")).not.toBeDisabled();
  });

  test("shows 6th CPC fixation source pay band and grade pay as system-filled while leaving 7th CPC target editable", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "PROMOTION",
          effective_from: "2015-07-01",
          recorded_at: "2026-04-07T23:23:00Z",
          payload: {
            cpc: "6TH_CPC",
            from_pay_band: "PB-2 (9300-34800)",
            from_grade_pay: "4400",
            to_pay_band: "PB-2 (9300-34800)",
            to_grade_pay: "4800",
            from_basic_pay: "16380",
            to_basic_pay: "16880",
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText("Event Category"), {
      target: { value: "CPC_PAY_FIXATION" },
    });

    fireEvent.change(await screen.findByLabelText("From Pay Commission (CPC) *"), {
      target: { value: "6TH_CPC" },
    });
    fireEvent.change(screen.getByLabelText("To Pay Commission (CPC) *"), {
      target: { value: "7TH_CPC" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("From Pay Band")).toHaveValue("PB-2 (9300-34800)");
      expect(screen.getByLabelText("From Grade Pay")).toHaveValue("4800");
      expect(screen.getByLabelText("From Basic Pay *")).toHaveValue(16880);
    });

    expect(screen.getByLabelText("From Pay Band")).toBeDisabled();
    expect(screen.getByLabelText("From Grade Pay")).toBeDisabled();
    expect(screen.getByLabelText("Pay Level *")).not.toBeDisabled();
    expect(screen.getByLabelText("Cell Index *")).not.toHaveAttribute("readonly");
  });

  test("requires non-fixation CPC pay structure fields on submit", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText("Event Category"), {
      target: { value: "INCREMENT" },
    });

    fireEvent.change(await screen.findByLabelText("Effective Date *"), {
      target: { value: "2026-04-01" },
    });
    fireEvent.change(screen.getByLabelText("Increment Type *"), {
      target: { value: "annual" },
    });
    fireEvent.change(screen.getByLabelText("Increment Order No *"), {
      target: { value: "MADC/FIN/2026/001" },
    });
    fireEvent.change(screen.getByLabelText("Increment Order Date *"), {
      target: { value: "2026-04-02" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Record Event" }));

    await waitFor(() => {
      expect(mockRecordEvent).not.toHaveBeenCalled();
    });

    expect(screen.getByLabelText("Pay Level *")).toBeRequired();
    expect(screen.getByLabelText("Cell Index *")).toBeRequired();
  });

  test("shows target pay structure fields for financial upgradation", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "INCREMENT",
          effective_from: "2026-07-01",
          recorded_at: "2026-04-07T23:30:00Z",
          payload: {
            cpc: "7TH_CPC",
            pay_level: "Level 8",
            from_basic_pay: "50500",
            to_basic_pay: "52000",
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(await screen.findByLabelText("Event Category"), {
      target: { value: "FINANCIAL_UPGRADATION" },
    });

    fireEvent.change(screen.getByLabelText("Pay Commission (CPC)"), {
      target: { value: "7TH_CPC" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("From Pay Level *")).toHaveValue("Level 8");
    });

    expect(screen.getByLabelText("From Pay Level *")).toBeDisabled();
    expect(screen.getByLabelText("To Pay Level *")).toBeInTheDocument();
    expect(screen.queryByLabelText("Pay Level *")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Cell Index *")).not.toBeInTheDocument();
  });

  test("prefills matching CPC pay structure from the latest effective pay fixation and keeps increment to basic editable", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "CPC_PAY_FIXATION",
          recorded_at: "2026-04-07T21:56:00Z",
          payload: {},
        },
        {
          event_type: "CPC_PAY_FIXATION",
          effective_from: "1997-01-01",
          recorded_at: "2026-04-07T22:12:00Z",
          payload: {
            to_cpc: "5TH_CPC",
            post_revised_pay: {
              pay_scale: "3050 75 3950 80 4590",
              basic_pay: 3050,
            },
          },
        },
        {
          event_type: "INCREMENT",
          effective_from: "1996-06-01",
          recorded_at: "2026-04-07T21:37:00Z",
          payload: {
            cpc: "4TH_CPC",
            pay_scale: "975 25 1150 30 1660",
            to_basic_pay: 975,
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(await screen.findByLabelText("Event Category"), {
      target: { value: "INCREMENT" },
    });

    fireEvent.change(screen.getByLabelText("Pay Commission (CPC)"), {
      target: { value: "5TH_CPC" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("Pay Scale *")).toHaveValue("3050-75-3950-80-4590");
    });

    expect(screen.getByLabelText("From Basic Pay *")).toHaveValue(3050);
    expect(screen.getByLabelText("To Basic Pay *")).toHaveDisplayValue("");
    expect(screen.getByLabelText("To Basic Pay *")).not.toHaveAttribute("readonly");
  });

  test("prefills promotion from pay structure from the latest matching CPC context", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "INCREMENT",
          effective_from: "1999-06-01",
          recorded_at: "2026-04-07T22:40:00Z",
          payload: {
            cpc: "5TH_CPC",
            pay_scale: "3050 75 3950 80 4590",
            from_basic_pay: 3125,
            to_basic_pay: 3200,
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(await screen.findByLabelText("Event Category"), {
      target: { value: "PROMOTION" },
    });

    fireEvent.change(screen.getByLabelText("Pay Commission (CPC)"), {
      target: { value: "5TH_CPC" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("From Pay Scale *")).toHaveValue("3050-75-3950-80-4590");
    });

    expect(screen.getByLabelText("From Pay Scale *")).toBeDisabled();
    expect(screen.getByLabelText("From Basic Pay *")).toHaveValue(3200);
    expect(screen.getByLabelText("To Pay Scale *")).toHaveValue("");
    expect(screen.getByLabelText("To Pay Scale *")).not.toBeDisabled();
    expect(screen.getByLabelText("To Basic Pay *")).toHaveDisplayValue("");
  });

  test("locks 6th CPC promotion source pay band and grade pay while leaving destination fields editable", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "INCREMENT",
          effective_from: "2012-07-01",
          recorded_at: "2026-04-07T23:23:00Z",
          payload: {
            cpc: "6TH_CPC",
            pay_band: "PB-2 (9300-34800)",
            grade_pay: "4400",
            from_basic_pay: "16380",
            to_basic_pay: "16880",
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(await screen.findByLabelText("Event Category"), {
      target: { value: "PROMOTION" },
    });

    fireEvent.change(screen.getByLabelText("Pay Commission (CPC)"), {
      target: { value: "6TH_CPC" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("From Pay Band *")).toHaveValue("PB-2 (9300-34800)");
      expect(screen.getByLabelText("From Grade Pay *")).toHaveValue("4400");
    });

    expect(screen.getByLabelText("From Pay Band *")).toBeDisabled();
    expect(screen.getByLabelText("From Grade Pay *")).toBeDisabled();
    expect(screen.getByLabelText("To Pay Band *")).not.toBeDisabled();
    expect(screen.getByLabelText("To Grade Pay *")).not.toBeDisabled();
  });

  test("locks 7th CPC promotion source pay level while leaving destination level editable", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "INCREMENT",
          effective_from: "2026-07-01",
          recorded_at: "2026-04-07T23:30:00Z",
          payload: {
            cpc: "7TH_CPC",
            pay_level: "Level 8",
            pay_cell_index: "5",
            from_basic_pay: "50500",
            to_basic_pay: "52000",
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(await screen.findByLabelText("Event Category"), {
      target: { value: "PROMOTION" },
    });

    fireEvent.change(screen.getByLabelText("Pay Commission (CPC)"), {
      target: { value: "7TH_CPC" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("From Pay Level *")).toHaveValue("Level 8");
    });

    expect(screen.getByLabelText("From Pay Level *")).toBeDisabled();
    expect(screen.getByLabelText("To Pay Level *")).not.toBeDisabled();
  });

  test("uses the latest recorded increment basic pay for promotion when live payloads only carry increment_date", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "CPC_PAY_FIXATION",
          effective_from: "1997-01-01",
          recorded_at: "2026-04-07T16:42:02Z",
          payload: {
            to_cpc: "5TH_CPC",
            post_revised_pay: {
              pay_scale: "3050-75-3950-80-4590",
              basic_pay: "3050",
            },
          },
        },
        {
          event_type: "INCREMENT",
          recorded_at: "2026-04-07T16:58:05Z",
          payload: {
            cpc: "5TH_CPC",
            increment_date: "1998-06-01",
            pay_scale: "3050 75 3950 80 4590",
            from_basic_pay: "3050",
            to_basic_pay: "3125",
          },
        },
        {
          event_type: "INCREMENT",
          recorded_at: "2026-04-07T17:10:16Z",
          payload: {
            cpc: "5TH_CPC",
            increment_date: "1999-06-01",
            pay_scale: "3050 75 3950 80 4590",
            from_basic_pay: "3125",
            to_basic_pay: "3200",
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(await screen.findByLabelText("Event Category"), {
      target: { value: "PROMOTION" },
    });

    fireEvent.change(screen.getByLabelText("Pay Commission (CPC)"), {
      target: { value: "5TH_CPC" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("From Basic Pay *")).toHaveValue(3200);
    });
  });

  test("calculates 5th CPC promotion to basic pay from the next higher stage in the promoted scale", async () => {
    mockGetRecordSchema.mockRejectedValueOnce(new Error("schema unavailable"));
    mockGetEventStream.mockResolvedValueOnce({
      data: [
        {
          event_type: "INCREMENT",
          recorded_at: "2026-04-07T17:10:16Z",
          payload: {
            cpc: "5TH_CPC",
            increment_date: "1999-06-01",
            pay_scale: "3050 75 3950 80 4590",
            from_basic_pay: "3125",
            to_basic_pay: "3200",
          },
        },
      ],
    });

    render(
      <RecordServiceBookRecordDialog
        employeeId="EMP-100"
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />
    );

    fireEvent.change(await screen.findByLabelText("Event Category"), {
      target: { value: "PROMOTION" },
    });

    fireEvent.change(screen.getByLabelText("Pay Commission (CPC)"), {
      target: { value: "5TH_CPC" },
    });

    fireEvent.change(screen.getByLabelText("To Pay Scale *"), {
      target: { value: "3200-85-4900" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText("To Basic Pay *")).toHaveValue(3285);
    });
  });
});
