import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";

import SeniorityListsTab from "@/contexts/seniority/components/SeniorityListsTab";

const mockHasAuthority = jest.fn();

jest.mock("@/contexts/identity/model/authContext", () => ({
  __esModule: true,
  useAuth: () => ({ user: { authorities: [] } }),
}));

jest.mock("@/contexts/access_control/services/authorizationService", () => ({
  __esModule: true,
  hasAuthority: (...args) => mockHasAuthority(...args),
}));

const createProps = (overrides = {}) => ({
  lists: [
    {
      list_id: "list-1",
      title: "Draft Seniority - MINISTERIAL",
      version: 3,
      list_type: "PROVISIONAL",
      service: "MINISTERIAL",
      designation_code: "SO",
      status: "SUBMITTED",
      total: 12,
      created_at: "2025-04-01T10:30:00",
    },
    {
      list_id: "list-2",
      title: "Draft Seniority - GRP-C / LDC",
      version: 1,
      list_type: "DRAFT",
      service: "GRP-C",
      designation_code: "LDC",
      status: "DRAFT",
      total: 4,
      created_at: "2025-04-02T10:30:00",
    },
  ],
  total: 2,
  loading: false,
  detail: null,
  detailLoading: false,
  generating: false,
  transitioning: false,
  availableServices: ["MINISTERIAL"],
  availableDesignations: ["SO"],
  statusFilter: "",
  setStatusFilter: jest.fn(),
  serviceFilter: "",
  setServiceFilter: jest.fn(),
  listTypeFilter: "",
  setListTypeFilter: jest.fn(),
  yearFilter: "",
  setYearFilter: jest.fn(),
  pagination: { offset: 0, limit: 20 },
  setPagination: jest.fn(),
  fetchLists: jest.fn(),
  fetchOptions: jest.fn(),
  fetchDetail: jest.fn(),
  generateList: jest.fn(),
  overrideRanks: jest.fn(),
  transition: jest.fn(),
  promote: jest.fn(),
  exportCSV: jest.fn(),
  setDetail: jest.fn(),
  ...overrides,
});

describe("SeniorityListsTab", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockHasAuthority.mockReturnValue(false);
  });

  test("renders readable labels in the list table", async () => {
    const props = createProps();

    render(<SeniorityListsTab {...props} />);

    expect(await screen.findByText("Draft Seniority - Ministerial")).toBeInTheDocument();
    expect(screen.getByText("Draft Seniority - Group C / Lower Division Clerk")).toBeInTheDocument();
    expect(screen.getByText("Version 3")).toBeInTheDocument();
    expect(screen.getByText("Version 1")).toBeInTheDocument();
    expect(screen.getByText("2025-04-01 10:30:00")).toBeInTheDocument();
    expect(screen.getByText("2025-04-02 10:30:00")).toBeInTheDocument();
    expect(await screen.findByText("Provisional")).toBeInTheDocument();
    expect(screen.getByText("Ministerial")).toBeInTheDocument();
    expect(screen.getByText("Section Officer")).toBeInTheDocument();
    expect(screen.getByText("Submitted")).toBeInTheDocument();
    expect(screen.getByText("Group C")).toBeInTheDocument();
    expect(screen.getByText("Lower Division Clerk")).toBeInTheDocument();
    expect(props.fetchOptions).toHaveBeenCalledTimes(1);
    expect(props.fetchLists).toHaveBeenCalledTimes(1);
  });

  test("renders readable labels in the detail view", () => {
    render(
      <SeniorityListsTab
        {...createProps({
          detail: {
            list_id: "list-2",
            title: "Final Seniority - GENERAL / ASO",
            list_type: "FINAL",
            status: "APPROVED",
            service: "GENERAL",
            designation_code: "ASO",
            total: 1,
            version: 2,
            year: 2025,
            employees: [
              {
                employee_id: "emp-1",
                rank: 1,
                employee_code: "MADC-2025-0001",
                full_name: "TEST_sample_employee_20260316214313",
                department_code: "FIN",
                date_of_initial_engagement: "2020-01-02",
                service: "ENGINEERING",
                group: "GROUP_B",
                appointment_date: "2020-01-02",
                confirmation_date: "2021-01-02",
                last_promotion_date: "2024-01-02",
              },
            ],
          },
        })}
      />,
    );

    expect(screen.getByText("Final Seniority - General / Assistant Section Officer")).toBeInTheDocument();
    expect(screen.getByText("Type: Final")).toBeInTheDocument();
    expect(screen.getByText("Status: Approved")).toBeInTheDocument();
    expect(screen.getByText("Service: General | Designation: Assistant Section Officer | Total: 1")).toBeInTheDocument();
    expect(screen.getByText("Version 2")).toBeInTheDocument();
    expect(screen.getByText("Test Sample Employee")).toBeInTheDocument();
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("Group B")).toBeInTheDocument();
    expect(screen.getByText("Initial Appointment")).toBeInTheDocument();
    expect(screen.getByText("Latest Appointment")).toBeInTheDocument();
  });

  test("keeps save disabled while edited ranks are duplicate or incomplete", () => {
    mockHasAuthority.mockImplementation((_user, authority) => authority === "GLOBAL_DATA_ENTRY");

    render(
      <SeniorityListsTab
        {...createProps({
          detail: {
            list_id: "list-2",
            title: "Draft Seniority - GENERAL",
            list_type: "DRAFT",
            status: "DRAFT",
            service: "GENERAL",
            designation_code: "",
            total: 3,
            version: 1,
            employees: [
              { employee_id: "emp-1", rank: 1, employee_code: "E-1", full_name: "Alpha", department_code: "FIN", date_of_initial_engagement: "2020-01-01", service: "GENERAL", group: "GROUP_A" },
              { employee_id: "emp-2", rank: 2, employee_code: "E-2", full_name: "Beta", department_code: "FIN", date_of_initial_engagement: "2020-01-02", service: "GENERAL", group: "GROUP_A" },
              { employee_id: "emp-3", rank: 3, employee_code: "E-3", full_name: "Gamma", department_code: "FIN", date_of_initial_engagement: "2020-01-03", service: "GENERAL", group: "GROUP_A" },
            ],
          },
        })}
      />,
    );

    fireEvent.click(screen.getByText("Edit Ranks"));

    const rankInputs = screen.getAllByRole("spinbutton");
    fireEvent.change(rankInputs[2], { target: { value: "1" } });

    expect(screen.getByText("Ranks must stay unique and continuous from 1 to 3.")).toBeInTheDocument();
    expect(screen.getByText("Save Ranks")).toBeDisabled();
  });

  test("supports moving a row up while keeping ranks valid", () => {
    mockHasAuthority.mockImplementation((_user, authority) => authority === "GLOBAL_DATA_ENTRY");

    render(
      <SeniorityListsTab
        {...createProps({
          detail: {
            list_id: "list-2",
            title: "Draft Seniority - GENERAL",
            list_type: "DRAFT",
            status: "DRAFT",
            service: "GENERAL",
            designation_code: "",
            total: 3,
            version: 1,
            employees: [
              { employee_id: "emp-1", rank: 1, employee_code: "E-1", full_name: "Alpha", department_code: "FIN", date_of_initial_engagement: "2020-01-01", service: "GENERAL", group: "GROUP_A" },
              { employee_id: "emp-2", rank: 2, employee_code: "E-2", full_name: "Beta", department_code: "FIN", date_of_initial_engagement: "2020-01-02", service: "GENERAL", group: "GROUP_A" },
              { employee_id: "emp-3", rank: 3, employee_code: "E-3", full_name: "Gamma", department_code: "FIN", date_of_initial_engagement: "2020-01-03", service: "GENERAL", group: "GROUP_A" },
            ],
          },
        })}
      />,
    );

    fireEvent.click(screen.getByText("Edit Ranks"));
    fireEvent.click(screen.getByLabelText("Move Gamma up"));

    const rankInputs = screen.getAllByRole("spinbutton");
    expect(rankInputs[1]).toHaveValue(2);
    expect(rankInputs[2]).toHaveValue(3);
    expect(screen.getByText("Save Ranks")).not.toBeDisabled();
    expect(screen.getByText(/Use the arrows for quick swaps/i)).toBeInTheDocument();
  });
});