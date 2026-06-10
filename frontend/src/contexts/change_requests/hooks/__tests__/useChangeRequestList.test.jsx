import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import { useChangeRequestList } from "@/contexts/change_requests/hooks/useChangeRequestList";

const mockListMyChangeRequests = jest.fn();
const mockGetMyProfile = jest.fn();
const mockGetComplete = jest.fn();

jest.mock("@/contexts/ess/api/essApi", () => ({
  __esModule: true,
  essAPI: {
    listMyChangeRequests: (...args) => mockListMyChangeRequests(...args),
    getMyProfile: (...args) => mockGetMyProfile(...args),
  },
}));

jest.mock("@/contexts/service_book/api/serviceBookApi", () => ({
  __esModule: true,
  serviceBookAPI: {
    getComplete: (...args) => mockGetComplete(...args),
  },
}));

jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
  },
}));

function Harness() {
  const { serviceBookEligible, serviceBook } = useChangeRequestList({
    partKeyToCompleteKey: { I: "part_i", IV: "part_iv" },
  });

  return (
    <div>
      <div data-testid="eligible">{String(serviceBookEligible)}</div>
      <div data-testid="has-part-i">{String(Boolean(serviceBook?.I))}</div>
    </div>
  );
}

describe("useChangeRequestList", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockListMyChangeRequests.mockResolvedValue({ data: { items: [] } });
    mockGetMyProfile.mockResolvedValue({
      data: {
        employee_id: "EMP-1",
        employment_type: "REGULAR",
      },
    });
    mockGetComplete.mockResolvedValue({
      data: {
        part_i: { employee_name: "Regular Employee" },
      },
    });
  });

  test("loads finalized service book projection for ESS change requests", async () => {
    render(<Harness />);

    await waitFor(() => {
      expect(mockGetComplete).toHaveBeenCalledWith("EMP-1", {
        statuses: ["APPROVED", "LOCKED"],
      });
    });

    expect(screen.getByTestId("eligible")).toHaveTextContent("true");
    expect(screen.getByTestId("has-part-i")).toHaveTextContent("true");
  });
});