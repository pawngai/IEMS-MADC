import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import WorkflowQueueScreen from "@/modules/workflow/containers/WorkflowQueueScreen";

const mockNavigate = vi.fn();
const mockRefresh = vi.fn();
const mockGetProfileAuditTrail = vi.fn();
const mockGetActions = vi.fn();
const mockListServiceBookEntries = vi.fn();
const mockGetServiceSummary = vi.fn();
let mockPathname = "/work";
let mockAuthority = "GLOBAL_DATA_ENTRY";
let mockAuthorityLabel = "Global Data Entry";
let mockItems = [
  {
    id: "item-1",
    employeeId: "EMP-1",
    type: "profile",
    stage: "DRAFT",
    raw: {
      employee_section_completed: true,
      data_entry_section_completed: false,
    },
  },
];

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ pathname: mockPathname }),
  };
});

vi.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout-shell">{children}</div>,
}));

vi.mock("@/modules/workflow/hooks/useWorkflowQueueQuery", () => ({
  useWorkflowQueueQuery: () => ({
    loading: false,
    refreshing: false,
    refresh: mockRefresh,
    authority: mockAuthority,
    authorityLabel: mockAuthorityLabel,
    items: mockItems,
  }),
}));

vi.mock("@/modules/workflow/hooks/useWorkflowQueueFilters", () => ({
  useWorkflowQueueFilters: ({ items }) => ({
    query: "",
    setQuery: vi.fn(),
    typeFilter: "all",
    setTypeFilter: vi.fn(),
    slaFilter: "all",
    setSlaFilter: vi.fn(),
    filteredItems: items,
    kanbanColumns: [{ id: "draft", title: "Draft", items }],
  }),
}));

vi.mock("@/modules/workflow/hooks/useWorkflowQueueActions", () => ({
  useWorkflowQueueActions: () => ({
    getActions: (...args) => mockGetActions(...args),
    performAction: vi.fn(),
  }),
}));

vi.mock("@/modules/workflow/model/workflowQueueSelectors", () => ({
  selectCountsByType: () => ({ identity: 0, profile: 1, service: 0, change_request: 0 }),
  selectSlaCounts: () => ({ GREEN: 1, YELLOW: 0, RED: 0 }),
}));

vi.mock("@/modules/workflow/model/workQueueGateway", () => ({
  getProfileAuditTrail: (...args) => mockGetProfileAuditTrail(...args),
}));

vi.mock("@/modules/service_book", () => ({
  getOpeningActionLabel: (status) => (status === "OPENED" ? "View Service Book" : status === "NOT_OPENED" ? "Open Service Book" : "Continue Opening"),
  resolveServiceBookStatus: ({ summary, entries = [] }) => {
    if (entries.some((entry) => String(entry?.workflow_state || "").toUpperCase() === "LOCKED")) {
      return { status: "OPENED" };
    }
    if (summary?.eligible_for_service_book) {
      return { status: "NOT_OPENED" };
    }
    return { status: "NOT_OPENED" };
  },
  serviceBookAPI: {
    listEntries: (...args) => mockListServiceBookEntries(...args),
  },
  serviceRecordsApi: {
    getServiceSummary: (...args) => mockGetServiceSummary(...args),
  },
}));

vi.mock("@/modules/workflow/components/WorkflowQueueFilters", () => ({
  __esModule: true,
  default: () => <div data-testid="workflow-filters" />,
}));

vi.mock("@/modules/workflow/components/WorkflowQueueBulkActions", () => ({
  __esModule: true,
  default: () => null,
}));

vi.mock("@/modules/workflow/components/WorkflowKanbanView", () => ({
  __esModule: true,
  default: ({ columns, onSelect }) => (
    <button type="button" onClick={() => onSelect(columns[0]?.items?.[0]?.id)}>
      Open Draft Item
    </button>
  ),
}));

vi.mock("@/modules/workflow/components/WorkflowTableView", () => ({
  __esModule: true,
  default: ({ items, getActions }) => (
    <div data-testid="workflow-table">
      {items.flatMap((item) => getActions(item).map((action) => (
        <button key={`${item.id}:${action.id}`} type="button">
          {action.label}
        </button>
      )))}
    </div>
  ),
}));

vi.mock("@/modules/workflow/components/WorkflowDetailPanel", () => ({
  __esModule: true,
  default: ({ onEditPrimary, onOpenSecondary, secondaryOpenLabel = "View Service Book" }) => (
    <div>
      {onEditPrimary ? (
        <button type="button" onClick={onEditPrimary}>
          Edit / Complete Profile
        </button>
      ) : null}
      {onOpenSecondary ? (
        <button type="button" onClick={onOpenSecondary}>
          {secondaryOpenLabel}
        </button>
      ) : null}
    </div>
  ),
}));

vi.mock("@/modules/workflow/components/workflowQueuePrimitives", () => ({
  MiniStat: ({ label, value }) => (
    <div data-testid={`stat-${label.toLowerCase()}`}>{value}</div>
  ),
}));

vi.mock("@/shared/ui/badge", () => ({
  Badge: ({ children }) => <span>{children}</span>,
}));

vi.mock("@/shared/ui/button", () => ({
  Button: ({ children, onClick, ...props }) => (
    <button type="button" onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock("@/shared/ui/card", () => ({
  Card: ({ children }) => <div>{children}</div>,
  CardContent: ({ children }) => <div>{children}</div>,
}));

vi.mock("@/shared/ui/sheet", () => ({
  Sheet: ({ children }) => <div>{children}</div>,
  SheetContent: ({ children }) => <div>{children}</div>,
  SheetHeader: ({ children }) => <div>{children}</div>,
  SheetTitle: ({ children }) => <div>{children}</div>,
  SheetDescription: ({ children }) => <div>{children}</div>,
}));

vi.mock("@/shared/ui/tooltip", () => ({
  TooltipProvider: ({ children }) => <div>{children}</div>,
}));

vi.mock("@/shared/ui/skeletons", () => ({
  WorkQueueSkeleton: () => <div data-testid="workqueue-skeleton" />,
  PageHeaderSkeleton: () => <div data-testid="pageheader-skeleton" />,
}));

vi.mock("sonner", () => ({
  __esModule: true,
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe("WorkflowQueueScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetProfileAuditTrail.mockResolvedValue([]);
    mockGetActions.mockReturnValue([]);
    mockListServiceBookEntries.mockResolvedValue({ entries: [] });
    mockGetServiceSummary.mockResolvedValue({ data: { eligible_for_service_book: true } });
    mockPathname = "/work";
    mockAuthority = "GLOBAL_DATA_ENTRY";
    mockAuthorityLabel = "Global Data Entry";
    mockItems = [
      {
        id: "item-1",
        employeeId: "EMP-1",
        type: "profile",
        stage: "DRAFT",
        raw: {
          employee_section_completed: true,
          data_entry_section_completed: false,
        },
      },
    ];
  });

  test("opens the shared employee profile editor from the work queue draft item", async () => {
    render(<WorkflowQueueScreen />);

    fireEvent.click(screen.getByRole("button", { name: /Pipeline/i }));

    fireEvent.click(screen.getByRole("button", { name: "Open Draft Item" }));

    await waitFor(() => {
      expect(mockGetProfileAuditTrail).toHaveBeenCalledWith("EMP-1");
    });

    fireEvent.click(screen.getByRole("button", { name: "Edit / Complete Profile" }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/employees/EMP-1/profile/edit", {
        state: { returnTo: "/work" },
      });
    });
  });

  test("uses table as the default work queue view", () => {
    render(<WorkflowQueueScreen />);

    expect(screen.getByTestId("workflow-table")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Open Draft Item" })).not.toBeInTheDocument();
  });

  test("exposes profile submit as a row-level quick action when available", () => {
    mockGetActions.mockReturnValue([
      { id: "profile-submit", label: "Submit", variant: "default", disabled: false },
    ]);

    render(<WorkflowQueueScreen />);

    expect(screen.getByRole("button", { name: "Submit" })).toBeInTheDocument();
  });

  test("routes the work queue Service Book button to opening when the employee has not opened service book yet", async () => {
    render(<WorkflowQueueScreen />);

    fireEvent.click(screen.getByRole("button", { name: /Pipeline/i }));
    fireEvent.click(screen.getByRole("button", { name: "Open Draft Item" }));

    await waitFor(() => {
      expect(mockGetServiceSummary).toHaveBeenCalledWith("EMP-1");
    });

    fireEvent.click(await screen.findByRole("button", { name: "Open Service Book" }));

    expect(mockNavigate).toHaveBeenCalledWith("/service-book/opening/EMP-1");
  });

  test("exposes opening from the work queue for dealing assistant when the employee has not opened service book yet", async () => {
    mockAuthority = "DEALING_ASSISTANT";
    mockAuthorityLabel = "Dealing Assistant";

    render(<WorkflowQueueScreen />);

    fireEvent.click(screen.getByRole("button", { name: /Pipeline/i }));
    fireEvent.click(screen.getByRole("button", { name: "Open Draft Item" }));

    await waitFor(() => {
      expect(mockGetServiceSummary).toHaveBeenCalledWith("EMP-1");
    });

    expect(await screen.findByRole("button", { name: "Open Service Book" })).toBeInTheDocument();
  });

  test("does not expose opening from the work queue for non-global authorities when service book is not opened", async () => {
    mockAuthority = "APPROVING_AUTHORITY";
    mockAuthorityLabel = "Approving Authority";

    render(<WorkflowQueueScreen />);

    fireEvent.click(screen.getByRole("button", { name: /Pipeline/i }));
    fireEvent.click(screen.getByRole("button", { name: "Open Draft Item" }));

    await waitFor(() => {
      expect(mockGetServiceSummary).toHaveBeenCalledWith("EMP-1");
    });

    expect(screen.queryByRole("button", { name: "Open Service Book" })).not.toBeInTheDocument();
  });

  test("routes a service book opening queue item back to the opening editor", async () => {
    mockItems = [
      {
        id: "opening-1",
        employeeId: "EMP-1",
        employeeCode: "MADC-0001",
        title: "Opening Employee",
        subtitle: "MADC-0001 • Opening Workflow",
        type: "service_opening",
        stage: "DRAFT",
        raw: {
          workflow_status: "DRAFT",
        },
      },
    ];

    render(<WorkflowQueueScreen />);

    fireEvent.click(screen.getByRole("button", { name: /Pipeline/i }));
    fireEvent.click(screen.getByRole("button", { name: "Open Draft Item" }));

    fireEvent.click(await screen.findByRole("button", { name: "Continue Opening" }));

    expect(mockNavigate).toHaveBeenCalledWith("/service-book/opening/MADC-0001");
  });
});
