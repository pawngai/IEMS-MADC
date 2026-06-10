import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

import { useWorkflowQueueQuery } from "@/contexts/workflow/hooks/useWorkflowQueueQuery";
import { Permissions } from "@/platform/permissions";

const mockUseAuth = vi.fn();
const mockListIdentitiesByStatus = vi.fn();
const mockListProfilesByStatus = vi.fn();
const mockListServiceBookQueue = vi.fn();
const mockListServiceBookOpeningQueue = vi.fn();
const mockListChangeRequestsByStatus = vi.fn();
const mockToProfileItems = vi.fn();

vi.mock("@/contexts/identity/model/authContext", () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
  },
}));

vi.mock("@/shared/lib/utils", () => ({
  getEmployeeCompletionStatus: () => ({ known: true, complete: true }),
}));

vi.mock("@/contexts/workflow/model/workQueueGateway", () => ({
  clearWorkQueueInflightRequests: vi.fn(),
  getMyEssProfile: vi.fn(),
  listIdentitiesByStatus: (...args) => mockListIdentitiesByStatus(...args),
  listChangeRequestsByStatus: (...args) => mockListChangeRequestsByStatus(...args),
  listProfilesByStatus: (...args) => mockListProfilesByStatus(...args),
  listServiceBookQueue: (...args) => mockListServiceBookQueue(...args),
  listServiceBookOpeningQueue: (...args) => mockListServiceBookOpeningQueue(...args),
}));

vi.mock("@/contexts/workflow/model/workflowQueueMapper", () => ({
  enrichAndSortQueueItems: (items) => items,
  toChangeRequestItems: () => [],
  toEssTaskItem: () => null,
  toIdentityItems: ({ identities, stage }) => identities.map((identity) => ({
    id: `${stage}:${identity.employee_id}`,
    type: "identity",
    stage,
    title: identity.full_name || "",
    subtitle: identity.employee_code || "",
    raw: identity,
  })),
  toProfileItems: (...args) => mockToProfileItems(...args),
  toServiceBookItems: ({ entries, stage }) => entries.map((entry) => ({
    id: `${stage}:${entry.id}`,
    type: "service",
    stage,
    title: entry.full_name || "",
    subtitle: entry.employee_code || "",
    raw: entry,
  })),
  toServiceBookOpeningItems: ({ openings, stage }) => openings.map((opening) => ({
    id: `${stage}:${opening.employee_id}`,
    type: "service_opening",
    stage,
    title: opening.full_name || opening.employee_name || "",
    subtitle: opening.employee_code || "",
    raw: opening,
  })),
}));

function QueueHarness() {
  const { loading, items } = useWorkflowQueueQuery();

  if (loading) return <div>Loading</div>;

  return (
    <div>
      {items.map((item) => (
        <div key={item.id}>{`${item.title}|${item.subtitle}`}</div>
      ))}
    </div>
  );
}

describe("useWorkflowQueueQuery", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockToProfileItems.mockImplementation(({ profiles, stage }) => profiles.map((profile) => ({
      id: `${stage}:${profile.employee_id}`,
      type: "profile",
      stage,
      title: profile.full_name || "",
      subtitle: profile.employee_code || "",
      raw: profile,
    })));

    mockUseAuth.mockReturnValue({
      user: { employee_id: "EMP-operator" },
      can: (permission) => permission !== Permissions.PROFILE_UPDATE_ALL,
      canAny: () => true,
      canAccessEssPortal: () => false,
      canAccessModule: () => true,
      getAuthorityDisplayName: () => "Global Data Entry",
      getPrimaryAuthority: () => "GLOBAL_DATA_ENTRY",
    });

    mockListProfilesByStatus.mockResolvedValue([]);
    mockListIdentitiesByStatus.mockResolvedValue([]);
    mockListChangeRequestsByStatus.mockResolvedValue([]);
    mockListServiceBookOpeningQueue.mockResolvedValue([]);
    mockListServiceBookQueue.mockImplementation(async (stage) => {
      if (Array.isArray(stage)) {
        return [
          {
            id: "entry-1",
            employee_id: "EMP-001",
            full_name: "Asha Employee",
            employee_code: "MADC-2024-0001",
            workflow_state: "DRAFT",
          },
          {
            id: "entry-2",
            employee_id: "EMP-002",
            full_name: "Existing Name",
            employee_code: "MADC-2024-0002",
            workflow_state: "REJECTED",
          },
        ];
      }

      return [];
    });
  });

  test("uses service-book queue identity labels without per-entry profile lookups", async () => {
    render(<QueueHarness />);

    await waitFor(() => {
      expect(screen.getByText("Asha Employee|MADC-2024-0001")).toBeInTheDocument();
    });

    expect(screen.getByText("Existing Name|MADC-2024-0002")).toBeInTheDocument();
    expect(mockListServiceBookQueue).toHaveBeenCalledWith(
      ["DRAFT", "REJECTED", "SUBMITTED", "VERIFIED", "APPROVED"],
      200
    );
  });

  test("includes service book opening items in the default work queue for opening editors", async () => {
    mockListServiceBookQueue.mockResolvedValue([]);
    mockListServiceBookOpeningQueue.mockImplementation(async (stage) => {
      if (stage !== "DRAFT") return [];

      return [
        {
          employee_id: "EMP-OPEN-1",
          employee_code: "MADC-OPEN-0001",
          full_name: "Opening Queue Item",
          workflow_status: "DRAFT",
        },
      ];
    });

    render(<QueueHarness />);

    await waitFor(() => {
      expect(screen.getByText("Opening Queue Item|MADC-OPEN-0001")).toBeInTheDocument();
    });

    expect(mockListServiceBookOpeningQueue).toHaveBeenCalledWith("DRAFT", 200);
    expect(mockListServiceBookOpeningQueue).toHaveBeenCalledWith("REJECTED", 200);
  });

  test("clears loading state under StrictMode after successful loads", async () => {
    render(
      <React.StrictMode>
        <QueueHarness />
      </React.StrictMode>
    );

    await waitFor(() => {
      expect(screen.queryByText("Loading")).not.toBeInTheDocument();
    });

    expect(screen.getByText("Asha Employee|MADC-2024-0001")).toBeInTheDocument();
  });

  test("includes profile and identity items in the default work queue for data entry authorities", async () => {
    mockUseAuth.mockReturnValue({
      user: { employee_id: "EMP-data-entry" },
      can: () => true,
      canAny: () => true,
      canAccessEssPortal: () => false,
      canAccessModule: (moduleId) => moduleId === "data_entry",
      getAuthorityDisplayName: () => "Global Data Entry",
      getPrimaryAuthority: () => "GLOBAL_DATA_ENTRY",
    });
    mockListProfilesByStatus.mockImplementation(async (stage) => {
      if (stage !== "DRAFT") return [];

      return [
        {
          employee_id: "EMP-PROFILE-11",
          employee_code: "MADC-2024-P0011",
          full_name: "Profile In Main Queue",
          workflow_status: "DRAFT",
          employee_section_completed: true,
        },
      ];
    });
    mockListServiceBookQueue.mockResolvedValue([]);
    mockListChangeRequestsByStatus.mockResolvedValue([]);
    mockListIdentitiesByStatus.mockImplementation(async (stage) => {
      if (stage !== "DRAFT") return [];
      return [
        {
          employee_id: "EMP-ID-11",
          employee_code: "MADC-2024-R0011",
          full_name: "Identity In Main Queue",
          workflow_status: "DRAFT",
        },
      ];
    });

    render(<QueueHarness />);

    await waitFor(() => {
      expect(screen.getByText("Identity In Main Queue|MADC-2024-R0011")).toBeInTheDocument();
    });

    expect(screen.getByText("Profile In Main Queue|MADC-2024-P0011")).toBeInTheDocument();
    expect(mockListIdentitiesByStatus).toHaveBeenCalledWith("DRAFT", 200);
    expect(mockListProfilesByStatus).toHaveBeenCalledWith("DRAFT", 200);
  });

  test("does not include non-regular record items in the work queue", async () => {
    mockUseAuth.mockReturnValue({
      user: { employee_id: "EMP-verifier" },
      can: () => true,
      canAny: () => true,
      canAccessEssPortal: () => false,
      canAccessModule: () => true,
      getAuthorityDisplayName: () => "Verifier",
      getPrimaryAuthority: () => "VERIFIER",
    });
    mockListProfilesByStatus.mockResolvedValue([]);
    mockListIdentitiesByStatus.mockResolvedValue([]);
    mockListServiceBookQueue.mockResolvedValue([]);
    mockListChangeRequestsByStatus.mockResolvedValue([]);

    render(<QueueHarness />);

    await waitFor(() => {
      expect(screen.queryByText("Loading")).not.toBeInTheDocument();
    });

    expect(screen.queryByText("Non Regular Queue|MADC-2024-NR001")).not.toBeInTheDocument();
    expect(mockListServiceBookQueue).toHaveBeenCalledWith(
      ["DRAFT", "REJECTED", "SUBMITTED", "VERIFIED", "APPROVED"],
      200
    );
  });

  test("includes identity draft items for dealing assistant", async () => {
    mockUseAuth.mockReturnValue({
      user: { employee_id: "EMP-dealing-assistant" },
      can: () => true,
      canAny: () => true,
      canAccessEssPortal: () => false,
      canAccessModule: (moduleId) => moduleId === "data_entry",
      getAuthorityDisplayName: () => "Dealing Assistant",
      getPrimaryAuthority: () => "DEALING_ASSISTANT",
    });
    mockListProfilesByStatus.mockResolvedValue([]);
    mockListServiceBookQueue.mockResolvedValue([]);
    mockListChangeRequestsByStatus.mockResolvedValue([]);
    mockListIdentitiesByStatus.mockImplementation(async (stage) => {
      if (stage !== "DRAFT") return [];
      return [
        {
          employee_id: "EMP-ID-DA",
          employee_code: "MADC-2024-DA001",
          full_name: "Dealing Identity Draft",
          workflow_status: "DRAFT",
        },
      ];
    });

    render(<QueueHarness />);

    await waitFor(() => {
      expect(screen.getByText("Dealing Identity Draft|MADC-2024-DA001")).toBeInTheDocument();
    });

    expect(mockListIdentitiesByStatus).toHaveBeenCalledWith("DRAFT", 200);
    expect(mockListIdentitiesByStatus).toHaveBeenCalledWith("REJECTED", 200);
  });

  test("loads approved profile items for approving authority final lock", async () => {
    mockUseAuth.mockReturnValue({
      user: { employee_id: "EMP-approver" },
      can: () => true,
      canAny: () => true,
      canAccessEssPortal: () => false,
      canAccessModule: (moduleId) => moduleId === "approval",
      getAuthorityDisplayName: () => "Approving Authority",
      getPrimaryAuthority: () => "APPROVING_AUTHORITY",
    });
    mockListProfilesByStatus.mockImplementation(async (stage) => {
      if (stage !== "APPROVED") return [];

      return [
        {
          employee_id: "EMP-PROFILE-LOCK",
          employee_code: "MADC-2024-R0001",
          full_name: "Approved Profile Ready For Lock",
          workflow_status: "APPROVED",
          employee_section_completed: true,
          data_entry_section_completed: true,
        },
      ];
    });
    mockListIdentitiesByStatus.mockResolvedValue([]);
    mockListServiceBookQueue.mockResolvedValue([]);
    mockListChangeRequestsByStatus.mockResolvedValue([]);

    render(<QueueHarness />);

    await waitFor(() => {
      expect(screen.getByText("Approved Profile Ready For Lock|MADC-2024-R0001")).toBeInTheDocument();
    });

    expect(mockListProfilesByStatus).toHaveBeenCalledWith("VERIFIED", 200);
    expect(mockListProfilesByStatus).toHaveBeenCalledWith("APPROVED", 200);
  });

  test("excludes untouched draft profiles from the profile queue", async () => {
    mockUseAuth.mockReturnValue({
      user: { employee_id: "EMP-section-officer" },
      can: () => true,
      canAny: () => true,
      canAccessEssPortal: () => false,
      canAccessModule: (moduleId) => moduleId === "data_entry",
      getAuthorityDisplayName: () => "Section Officer",
      getPrimaryAuthority: () => "SECTION_OFFICER",
    });
    mockListProfilesByStatus.mockImplementation(async (stage) => {
      if (stage !== "DRAFT") return [];

      return [
        {
          employee_id: "EMP-PROFILE-HIDDEN",
          employee_code: "EMP-HIDDEN",
          full_name: "Identity Placeholder",
          workflow_status: "DRAFT",
          employee_section_completed: false,
          data_entry_section_completed: false,
        },
        {
          employee_id: "EMP-PROFILE-VISIBLE",
          employee_code: "EMP-VISIBLE",
          full_name: "Started Profile",
          workflow_status: "DRAFT",
          employee_section_completed: true,
          data_entry_section_completed: false,
        },
      ];
    });
    mockListIdentitiesByStatus.mockResolvedValue([]);
    mockListServiceBookQueue.mockResolvedValue([]);
    mockListChangeRequestsByStatus.mockResolvedValue([]);

    render(<QueueHarness />);

    await waitFor(() => {
      expect(mockToProfileItems).toHaveBeenCalledWith({
        profiles: [
          expect.objectContaining({
            employee_id: "EMP-PROFILE-VISIBLE",
          }),
        ],
        stage: "DRAFT",
      });
    });

    expect(screen.queryByText("Identity Placeholder|EMP-HIDDEN")).not.toBeInTheDocument();
    expect(screen.getByText("Started Profile|EMP-VISIBLE")).toBeInTheDocument();
  });
});
