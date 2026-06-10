import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import { useDepartmentEmployeeDirectory } from "@/contexts/department/hooks/useDepartmentEmployeeDirectory";

const mockNavigate = vi.fn();
const mockGetEmployees = vi.fn();
const mockGetEmploymentTypes = vi.fn();
const mockGetDesignations = vi.fn();
const mockGetOffices = vi.fn();
const mockGetPayLevels = vi.fn();
const mockGetServices = vi.fn();
const mockGetServiceGroups = vi.fn();

let mockLocation = {
  pathname: "/department-portal/directory",
  search: "",
};

vi.mock("react-router-dom", () => ({
  __esModule: true,
  useNavigate: () => mockNavigate,
  useLocation: () => mockLocation,
}));

vi.mock("@/contexts/department/api/departmentApi", () => ({
  __esModule: true,
  departmentPortalAPI: {
    getEmployees: (...args) => mockGetEmployees(...args),
  },
}));

vi.mock("@/contexts/masters/api/mastersApi", () => ({
  __esModule: true,
  mastersAPI: {
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

const DirectoryProbe = ({ enabled = true }) => {
  const directory = useDepartmentEmployeeDirectory({ enabled });

  return (
    <div>
      <div data-testid="probe-query">{directory.query}</div>
      <div data-testid="probe-page">{String(directory.page)}</div>
      <button type="button" onClick={() => directory.setTypeFilter("CONTRACTUAL")}>set-type</button>
      <button type="button" onClick={() => directory.setPage(5)}>set-page</button>
    </div>
  );
};

describe("useDepartmentEmployeeDirectory", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation = {
      pathname: "/department-portal/directory",
      search: "",
    };
    mockGetEmployees.mockResolvedValue({
      data: {
        employees: [],
        total: 0,
        total_pages: 1,
      },
    });
    mockGetEmploymentTypes.mockResolvedValue({ data: [] });
    mockGetDesignations.mockResolvedValue({ data: [] });
    mockGetOffices.mockResolvedValue({ data: [] });
    mockGetPayLevels.mockResolvedValue({ data: [] });
    mockGetServices.mockResolvedValue({ data: [] });
    mockGetServiceGroups.mockResolvedValue({ data: [] });
  });

  test("hydrates from URL state and refetches when location search changes", async () => {
    mockLocation.search = "?q=alice&type=REGULAR&page=3&sort=employee_code&dir=desc";

    const { rerender } = render(<DirectoryProbe />);

    await waitFor(() => {
      expect(mockGetEmployees).toHaveBeenCalledWith({
        page: 3,
        page_size: 20,
        q: "alice",
        employment_type: "REGULAR",
        sort_by: "employee_code",
        sort_dir: "desc",
      });
    });

    expect(screen.getByTestId("probe-query")).toHaveTextContent("alice");
    expect(screen.getByTestId("probe-page")).toHaveTextContent("3");

    mockLocation = {
      ...mockLocation,
      search: "?q=bob&page=2",
    };
    rerender(<DirectoryProbe />);

    await waitFor(() => {
      expect(screen.getByTestId("probe-query")).toHaveTextContent("bob");
      expect(screen.getByTestId("probe-page")).toHaveTextContent("2");
    });

    await waitFor(() => {
      expect(mockGetEmployees).toHaveBeenCalledWith({
        page: 2,
        page_size: 20,
        q: "bob",
        sort_by: "full_name",
        sort_dir: "asc",
      });
    });
  });

  test("resets pagination when a filter changes and syncs the URL", async () => {
    mockLocation.search = "?page=4";
    render(<DirectoryProbe />);

    await waitFor(() => {
      expect(mockGetEmployees).toHaveBeenCalledWith({
        page: 4,
        page_size: 20,
        sort_by: "full_name",
        sort_dir: "asc",
      });
    });

    fireEvent.click(screen.getByText("set-type"));

    await waitFor(() => {
      expect(screen.getByTestId("probe-page")).toHaveTextContent("1");
    });

    await waitFor(() => {
      expect(mockGetEmployees).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        employment_type: "CONTRACTUAL",
        sort_by: "full_name",
        sort_dir: "asc",
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(
        {
          pathname: "/department-portal/directory",
          search: "?type=CONTRACTUAL",
        },
        { replace: true },
      );
    });
  });
});