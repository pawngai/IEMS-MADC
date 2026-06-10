import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";

import WorkflowQueueFilters from "@/contexts/workflow/components/WorkflowQueueFilters";

describe("WorkflowQueueFilters", () => {
  test("renders accessible search and SLA controls", () => {
    const onQueryChange = jest.fn();
    const onTypeFilterChange = jest.fn();
    const onSlaFilterChange = jest.fn();

    render(
      <WorkflowQueueFilters
        query=""
        onQueryChange={onQueryChange}
        typeFilter="ALL"
        onTypeFilterChange={onTypeFilterChange}
        slaFilter="RED"
        onSlaFilterChange={onSlaFilterChange}
        typeOptions={[
          { value: "ALL", label: "All (12)" },
          { value: "identity", label: "Identities (2)", color: "bg-emerald-100 text-emerald-700" },
          { value: "profile", label: "Profiles (8)", color: "bg-blue-100 text-blue-700" },
          { value: "service", label: "Service Book (4)", color: "bg-amber-100 text-amber-700" },
        ]}
      />,
    );

    expect(screen.getByRole("textbox", { name: "Search work queue items" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search queue items")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Work item type filters" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "SLA status filters" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Identities \(2\)/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Profiles \(8\)/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Service Book \(4\)/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All SLA statuses" })).toHaveTextContent("All");
    expect(screen.getByRole("button", { name: "Overdue items, more than 72 hours old" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Aging items, between 24 and 72 hours old" })).toHaveTextContent("Aging");
    expect(screen.getByRole("button", { name: "On-time items, less than 24 hours old" })).toHaveTextContent("On Time");

    fireEvent.change(screen.getByRole("textbox", { name: "Search work queue items" }), {
      target: { value: "rahul" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Aging items, between 24 and 72 hours old" }));

    expect(onQueryChange).toHaveBeenCalledWith("rahul");
    expect(onSlaFilterChange).toHaveBeenCalledWith("YELLOW");
  });
});