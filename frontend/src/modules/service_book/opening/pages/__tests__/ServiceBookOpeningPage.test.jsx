import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import ServiceBookOpeningPage from "@/modules/service_book/opening/pages/ServiceBookOpeningPage";

const mockCan = vi.fn();
const mockGetIdentity = vi.fn();
const mockGetProfile = vi.fn();
const mockGetDefaults = vi.fn();
const mockGetOpening = vi.fn();
const mockCreateDraft = vi.fn();
const mockUpdateDraft = vi.fn();
const mockSubmit = vi.fn();
const mockVerify = vi.fn();
const mockApprove = vi.fn();
const mockUploadDocument = vi.fn();
const mockAttachDocument = vi.fn();
let mockRouteEmployeeId = "EMP-1";

vi.mock("react-router-dom", () => ({
  __esModule: true,
  useParams: () => ({ employeeId: mockRouteEmployeeId }),
  useNavigate: () => vi.fn(),
  Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a>,
}));

vi.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

vi.mock("@/modules/identity_access", () => ({
  __esModule: true,
  useAuth: () => ({
    user: { employee_id: "EMP-1", name: "Opening Clerk" },
    can: (...args) => mockCan(...args),
  }),
  usePermissions: () => ({
    can: (...args) => mockCan(...args),
  }),
}));

vi.mock("@/modules/service_book/opening/api/serviceBookOpeningApi", () => ({
  __esModule: true,
  serviceBookOpeningApi: {
    getEmployeeIdentity: (...args) => mockGetIdentity(...args),
    getEmployeeProfile: (...args) => mockGetProfile(...args),
    getPartIDefaults: (...args) => mockGetDefaults(...args),
    getForEmployee: (...args) => mockGetOpening(...args),
    createDraft: (...args) => mockCreateDraft(...args),
    updateDraft: (...args) => mockUpdateDraft(...args),
    submit: (...args) => mockSubmit(...args),
    verify: (...args) => mockVerify(...args),
    approve: (...args) => mockApprove(...args),
    uploadLinkedDocument: (...args) => mockUploadDocument(...args),
    attachDocument: (...args) => mockAttachDocument(...args),
  },
}));

vi.mock("sonner", () => ({
  __esModule: true,
  toast: { success: vi.fn(), error: vi.fn() },
}));

describe("ServiceBookOpeningPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRouteEmployeeId = "EMP-1";
    mockCan.mockImplementation((permission) =>
      [
        "SERVICE_BOOK_OPENING_CREATE",
        "SERVICE_BOOK_OPENING_UPDATE",
        "SERVICE_BOOK_OPENING_SUBMIT",
      ].includes(permission)
    );
    mockGetIdentity.mockResolvedValue({
      data: {
        employee_id: "EMP-1",
        employee_code: "MADC-0001",
        full_name: "Identity Name",
        employment_type: "REGULAR",
        date_of_birth: "1990-01-01",
      },
    });
    mockGetProfile.mockResolvedValue({
      data: {
        employee_id: "EMP-1",
        full_name: "Profile Name",
        father_name: "Profile Father",
      },
    });
    mockGetDefaults.mockRejectedValue(new Error("defaults unavailable"));
    mockGetOpening.mockRejectedValue(new Error("not opened"));
    mockCreateDraft.mockResolvedValue({ data: { employee_id: "EMP-1", status: "DRAFT", parts: {}, documents: [] } });
    mockUpdateDraft.mockResolvedValue({ data: { employee_id: "EMP-1", status: "DRAFT", parts: {}, documents: [] } });
    mockSubmit.mockResolvedValue({ data: { employee_id: "EMP-1", status: "SUBMITTED", workflow_status: "SUBMITTED" } });
    mockVerify.mockResolvedValue({ data: { employee_id: "EMP-1", status: "VERIFIED", workflow_status: "VERIFIED" } });
    mockApprove.mockResolvedValue({ data: { employee_id: "EMP-1", status: "LOCKED", workflow_status: "LOCKED" } });
    mockUploadDocument.mockResolvedValue({ data: { document_id: "DOC-1", filename: "appointment.pdf" } });
    mockAttachDocument.mockResolvedValue({
      data: {
        employee_id: "EMP-1",
        status: "DRAFT",
        parts: {},
        documents: [{ document_id: "DOC-1", name: "medical.pdf", field_key: "medical_fitness_certificate", part_id: "part_iia" }],
      },
    });
  });

  test("Part I form prefills identity/profile defaults", async () => {
    render(<ServiceBookOpeningPage />);

    expect(await screen.findByDisplayValue("IDENTITY NAME")).toBeInTheDocument();
    expect(screen.getByDisplayValue("MADC-0001")).toBeInTheDocument();
    expect(screen.getByLabelText("Father's Name *")).toHaveValue("Profile Father");
    expect(screen.queryByLabelText("Parent's Name")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Permanent City")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Permanent State")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Permanent PIN")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Permanent Country")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Phone")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Photograph URL")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Signature URL")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Thumb Impression URL")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Date of Birth (Saka era)")).not.toBeInTheDocument();
  });

  test("Back to Employee uses resolved employee UUID when opening route param is employee code", async () => {
    mockRouteEmployeeId = "MADC-0001";

    render(<ServiceBookOpeningPage />);

    const backLink = await screen.findByRole("link", { name: /back to employee/i });
    await waitFor(() => {
      expect(backLink).toHaveAttribute("href", "/employees/EMP-1");
    });
  });

  test("save draft and submit use the resolved employee UUID when the route param is an employee code", async () => {
    mockRouteEmployeeId = "MADC-0001";
    const completeDraft = {
      employee_id: "EMP-1",
      status: "DRAFT",
      parts: {
        part_i: {
          employee_id: "EMP-1",
          name_in_block_letters: "PROFILE NAME",
          father_name: "Profile Father",
          marital_status: "Married",
          caste_category: "General",
          date_of_birth_christian: "1990-01-01",
        },
        part_iia: {
          medical_fitness_certificate: true,
          character_verification_done: true,
          entries_confirmed: true,
        },
        part_iib: { family_members: [{ name: "Asha" }] },
        part_iii: { previous_services: "Nil", foreign_services: "Nil" },
      },
      documents: [],
    };
    mockGetOpening.mockResolvedValue({ data: completeDraft });
    mockUpdateDraft.mockResolvedValue({ data: completeDraft });

    render(<ServiceBookOpeningPage />);

    fireEvent.click(await screen.findByTestId("opening-step-tab-part_iii"));
    fireEvent.change(screen.getByLabelText("Workflow remarks"), { target: { value: "route code mutation test" } });
    fireEvent.click(screen.getByRole("button", { name: "Save Draft" }));

    await waitFor(() => {
      expect(mockUpdateDraft).toHaveBeenCalledWith(
        "EMP-1",
        expect.objectContaining({ employee_id: "EMP-1" })
      );
    });

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith("EMP-1", "route code mutation test");
    });
  });

  test("final review step renders draft workflow actions for opening editors", async () => {
    render(<ServiceBookOpeningPage />);

    fireEvent.click(await screen.findByTestId("opening-step-tab-part_iii"));

    expect(screen.getByText("Review")).toBeInTheDocument();
    expect(screen.getByTestId("opening-workflow-actions")).toBeInTheDocument();
    expect(screen.getByLabelText("Workflow remarks")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save Draft" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Verify" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
  });

  test("non-regular employee cannot open Service Book", async () => {
    mockGetIdentity.mockResolvedValue({
      data: {
        employee_id: "EMP-2",
        full_name: "Contract Worker",
        employment_type: "CONTRACTUAL",
      },
    });

    render(<ServiceBookOpeningPage />);

    expect(await screen.findByText("Service Book Opening Not Applicable")).toBeInTheDocument();
    expect(screen.queryByTestId("opening-workflow-actions")).not.toBeInTheDocument();
  });

  test("uploads and attaches opening documents through the opening API for the matching field", async () => {
    render(<ServiceBookOpeningPage />);

    fireEvent.click(await screen.findByTestId("opening-step-tab-part_iia"));
    const file = new File(["pdf"], "appointment.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText("Upload Medical Fitness Certificate document"), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(mockUploadDocument).toHaveBeenCalledWith(
        file,
        expect.objectContaining({
          employee_id: "EMP-1",
          source_context: "service_book.opening",
        })
      );
      expect(mockAttachDocument).toHaveBeenCalledWith(
        "EMP-1",
        expect.objectContaining({
          document_id: "DOC-1",
          field_key: "medical_fitness_certificate",
          field_label: "Medical Fitness Certificate",
          part_id: "part_iia",
        })
      );
    });

    expect(await screen.findByText("medical.pdf")).toBeInTheDocument();
  });

  test("Part II-A groups immutable certificate fields into separate cards", async () => {
    render(<ServiceBookOpeningPage />);

    fireEvent.click(await screen.findByTestId("opening-step-tab-part_iia"));

    expect(screen.getByTestId("opening-section-part_iia-medical")).toBeInTheDocument();
    expect(screen.getByTestId("opening-section-part_iia-character")).toBeInTheDocument();
    expect(screen.getByTestId("opening-section-part_iia-police")).toBeInTheDocument();
    expect(screen.getByTestId("opening-section-part_iia-oath_allegiance")).toBeInTheDocument();
    expect(screen.getByTestId("opening-section-part_iia-oath_secrecy")).toBeInTheDocument();
    expect(screen.getByTestId("opening-section-part_iia-entries_confirmation")).toBeInTheDocument();
    expect(screen.getByTestId("opening-section-part_iia-marital_status_declaration")).toBeInTheDocument();
    expect(screen.getByTestId("opening-section-part_iia-hometown_declaration")).toBeInTheDocument();

    expect(within(screen.getByTestId("opening-section-part_iia-medical")).getByText("Medical Fitness")).toBeInTheDocument();
    expect(within(screen.getByTestId("opening-section-part_iia-medical")).getByLabelText("Medical Exam Date")).toBeInTheDocument();
    expect(within(screen.getByTestId("opening-section-part_iia-character")).getByLabelText("Character Verification Date")).toBeInTheDocument();
    expect(within(screen.getByTestId("opening-section-part_iia-entries_confirmation")).getByLabelText("Confirming Officer")).toBeInTheDocument();
    expect(within(screen.getByTestId("opening-section-part_iia-marital_status_declaration")).getByLabelText("Marital Status Declaration Date")).toBeInTheDocument();
    expect(within(screen.getByTestId("opening-section-part_iia-hometown_declaration")).getByLabelText("Declared Hometown")).toBeInTheDocument();
    expect(within(screen.getByTestId("opening-section-part_iia-hometown_declaration")).getByLabelText("Hometown Declaration Date")).toBeInTheDocument();
  });

  test("Part II-B uses canonical family, nomination, and bank fields", async () => {
    render(<ServiceBookOpeningPage />);

    fireEvent.click(await screen.findByTestId("opening-step-tab-part_iib"));
    expect(screen.getByText("Family")).toBeInTheDocument();
    expect(screen.getByText("Nominations")).toBeInTheDocument();
    expect(screen.getByText("Bank / Account Identifiers")).toBeInTheDocument();
    expect(screen.getByText("No family members added yet.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Add Family Member" }));
    expect(await screen.findByLabelText("Name")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Asha" } });
    fireEvent.change(screen.getByLabelText("Relationship"), { target: { value: "Spouse" } });
    fireEvent.change(screen.getByLabelText("Date of Birth"), { target: { value: "1992-03-01" } });
    expect(screen.getByDisplayValue("Asha")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Spouse")).toBeInTheDocument();
    expect(screen.getByDisplayValue("1992-03-01")).toBeInTheDocument();
    expect(screen.getByLabelText("Family Declaration Date")).toBeInTheDocument();
    expect(screen.getByLabelText("PCF Account Number")).toBeInTheDocument();
    expect(screen.getByText("No PCF nominees added yet.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Add PCF Nominee" }));
    expect(await screen.findByText("PCF Nominee 1")).toBeInTheDocument();
    const pcfCards = screen.getAllByText("PCF Nominee 1");
    expect(pcfCards.length).toBeGreaterThan(0);
    const pcfCard = pcfCards[0].closest("div.rounded-lg") || pcfCards[0].parentElement?.parentElement;
    const pcfScope = pcfCard || screen.getByText("PCF Nominee 1").parentElement;
    fireEvent.change(within(pcfScope).getByLabelText("Name"), { target: { value: "Asha" } });
    fireEvent.change(within(pcfScope).getByLabelText("Share (%)"), { target: { value: "100" } });
    expect(within(pcfScope).getByDisplayValue("Asha")).toBeInTheDocument();
    expect(screen.getAllByDisplayValue("Spouse").length).toBeGreaterThan(0);
    expect(screen.getByDisplayValue("100")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Upload PCF Nomination document" })).not.toBeInTheDocument();
    expect(screen.getByText("Nomination Documents")).toBeInTheDocument();
    expect(screen.getByText("Attach the supporting nomination document for the entries recorded in this section.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Upload nomination document" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add DCRG Nominee" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add NPS Nominee" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add Leave Encashment Nominee" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add Family Pension Nominee" })).toBeInTheDocument();
    expect(screen.getByLabelText("Bank Account Number")).toBeInTheDocument();
    expect(screen.getByLabelText("Bank Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Bank IFSC")).toBeInTheDocument();
    expect(screen.getByLabelText("NPS PRAN Number")).toBeInTheDocument();
    expect(screen.queryByLabelText("Pay Level *")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Basic Pay *")).not.toBeInTheDocument();
  });

  test("uses top step cards as tabs and renders the selected part form", async () => {
    render(<ServiceBookOpeningPage />);

    await screen.findByTestId("opening-stepper");
    expect(screen.getAllByText("Bio-Data").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Immutable Certificates").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Mutable Certificates").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Part III").length).toBeGreaterThan(0);

    expect(screen.getByTestId("opening-step-tab-part_i")).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByLabelText("Previous Services")).not.toBeInTheDocument();

    const partIPanel = screen.getByRole("tabpanel");
    expect(within(partIPanel).queryByText("Documents")).not.toBeInTheDocument();
    expect(within(partIPanel).queryByText("Review")).not.toBeInTheDocument();
    expect(within(partIPanel).queryByLabelText("Workflow remarks")).not.toBeInTheDocument();
    expect(within(partIPanel).queryByRole("button", { name: "Save Draft" })).not.toBeInTheDocument();
    expect(within(partIPanel).queryByTestId("opening-submit-btn")).not.toBeInTheDocument();
    expect(screen.queryByText("Review")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Workflow remarks")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save Draft" })).not.toBeInTheDocument();
    expect(screen.queryByTestId("opening-submit-btn")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("opening-step-tab-part_iii"));

    expect(screen.getByTestId("opening-step-tab-part_iii")).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByLabelText("Name in Block Letters *")).not.toBeInTheDocument();
    expect(screen.getByTestId("opening-part-iii-form")).toBeInTheDocument();

    const partIIIPanel = screen.getByRole("tabpanel");
    expect(within(partIIIPanel).getByLabelText("Previous Services")).toBeInTheDocument();
    expect(within(partIIIPanel).getByLabelText("Foreign Services")).toBeInTheDocument();
    expect(within(partIIIPanel).queryByLabelText("Part III Verified")).not.toBeInTheDocument();
    expect(within(partIIIPanel).queryByLabelText("Verified By")).not.toBeInTheDocument();
    expect(within(partIIIPanel).queryByLabelText("Verification Date")).not.toBeInTheDocument();
    expect(within(partIIIPanel).queryByText("Documents")).not.toBeInTheDocument();
    expect(within(partIIIPanel).getByRole("button", { name: /upload previous service document/i })).toBeInTheDocument();
    expect(within(partIIIPanel).getByRole("button", { name: /upload foreign service document/i })).toBeInTheDocument();
    expect(within(partIIIPanel).queryByText("Review")).not.toBeInTheDocument();
    expect(within(partIIIPanel).queryByLabelText("Workflow remarks")).not.toBeInTheDocument();
    expect(screen.getByText("Review")).toBeInTheDocument();
    expect(screen.getByLabelText("Workflow remarks")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save Draft" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Verify" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    expect(screen.getAllByText("Review")).toHaveLength(1);
  });
});
