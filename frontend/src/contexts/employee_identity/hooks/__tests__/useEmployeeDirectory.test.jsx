import React from "react";
import { render, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import { useEmployeeDirectory } from "@/contexts/employee_identity/hooks/useEmployeeDirectory";

const mockNavigate = vi.fn();
const mockListIdentityDirectory = vi.fn();
const mockEmployeeProfileList = vi.fn();
const mockGetDepartments = vi.fn();
const mockGetEmploymentTypes = vi.fn();
const mockGetDesignations = vi.fn();
const mockGetOffices = vi.fn();
const mockGetPayLevels = vi.fn();
const mockGetServices = vi.fn();
const mockGetServiceGroups = vi.fn();

let mockLocation = {
  pathname: "/employees",
  search: "",
};

vi.mock("react-router-dom", () => ({
  __esModule: true,
  useNavigate: () => mockNavigate,
  useLocation: () => mockLocation,
}));

vi.mock("@/contexts/employee_profile", () => ({
  __esModule: true,
  employeeProfileApi: {
    list: (...args) => mockEmployeeProfileList(...args),
  },
  formatDirectoryEnumLabel: (value) => value,
}));

vi.mock("@/contexts/masters", () => ({
  __esModule: true,
  mastersAPI: {
    getDepartments: (...args) => mockGetDepartments(...args),
    getEmploymentTypes: (...args) => mockGetEmploymentTypes(...args),
    getDesignations: (...args) => mockGetDesignations(...args),
    getOffices: (...args) => mockGetOffices(...args),
    getPayLevels: (...args) => mockGetPayLevels(...args),
    getServices: (...args) => mockGetServices(...args),
    getServiceGroups: (...args) => mockGetServiceGroups(...args),
  },
}));

vi.mock("sonner", () => ({
  __esModule: true,
  toast: {
    error: vi.fn(),
  },
}));

const DirectoryProbe = () => {
  useEmployeeDirectory({
    useIdentityDirectory: true,
    listIdentityDirectory: (...args) => mockListIdentityDirectory(...args),
  });
  return <div data-testid="probe">ready</div>;
};

describe("useEmployeeDirectory", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation = {
      pathname: "/employees",
      search: "",
    };
    mockListIdentityDirectory.mockResolvedValue({
      data: {
        identities: [],
        total: 0,
        total_pages: 1,
      },
    });
    mockEmployeeProfileList.mockResolvedValue({ data: { profiles: [], total: 0, total_pages: 1 } });
    mockGetDepartments.mockResolvedValue({ data: [] });
    mockGetEmploymentTypes.mockResolvedValue({ data: [] });
    mockGetDesignations.mockResolvedValue({ data: [] });
    mockGetOffices.mockResolvedValue({ data: [] });
    mockGetPayLevels.mockResolvedValue({ data: [] });
    mockGetServices.mockResolvedValue({ data: [] });
    mockGetServiceGroups.mockResolvedValue({ data: [] });
  });

  test("passes sort params to the identity directory request", async () => {
    mockLocation.search = "?sort=employee_code&dir=desc&page=2";

    render(<DirectoryProbe />);

    await waitFor(() => {
      expect(mockListIdentityDirectory).toHaveBeenCalledWith({
        page: 2,
        page_size: 20,
        search: undefined,
        status: undefined,
        department_id: undefined,
        employment_type: undefined,
        sort_by: "employee_code",
        sort_dir: "desc",
      });
    });
  });
});