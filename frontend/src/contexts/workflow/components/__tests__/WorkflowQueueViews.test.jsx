import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";

import WorkflowKanbanView from "@/contexts/workflow/components/WorkflowKanbanView";
import WorkflowTableView from "@/contexts/workflow/components/WorkflowTableView";
import { TooltipProvider } from "@/shared/ui/tooltip";

const baseItem = {
  id: "profile:EMP-1",
  type: "profile",
  stage: "DRAFT",
  statusLabel: "DRAFT",
  title: "Test Workflow",
  subtitle: "MADC-2024-0001",
  sla: "RED",
  ageHours: 100,
};

describe("Workflow queue views", () => {
  test("kanban headers and cards use readable labels", () => {
    const onSelect = jest.fn();

    render(
      <TooltipProvider>
        <WorkflowKanbanView
          columns={[["NOW", [baseItem]]]}
          selectedId={null}
          batchSelected={new Set()}
          onSelect={onSelect}
          onToggleBatch={jest.fn()}
          getActions={() => []}
          onQuickAction={jest.fn()}
          actionBusy={false}
        />
      </TooltipProvider>,
    );

    expect(screen.getByText("Action needed")).toBeInTheDocument();
    expect(screen.getByText("Needs your attention before submission")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open details for Test Workflow" }));

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith("profile:EMP-1");
  });

  test("table rows provide an explicit details button alongside quick actions", () => {
    const onSelect = jest.fn();
    const onQuickAction = jest.fn();

    render(
      <TooltipProvider>
        <WorkflowTableView
          items={[baseItem]}
          selectedId={null}
          batchSelected={new Set()}
          onSelect={onSelect}
          onToggleBatch={jest.fn()}
          onSelectAll={jest.fn()}
          getActions={() => [{ id: "profile-submit", label: "Submit", variant: "default", disabled: false }]}
          onQuickAction={onQuickAction}
          actionBusy={false}
        />
      </TooltipProvider>,
    );

    expect(screen.getByText("Draft")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open details for Test Workflow" }));
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(onSelect).toHaveBeenCalledWith("profile:EMP-1");
    expect(onQuickAction).toHaveBeenCalledWith(baseItem, "profile-submit");
  });

  test("table keeps horizontal scrolling inside the table container", () => {
    render(
      <TooltipProvider>
        <WorkflowTableView
          items={[baseItem]}
          selectedId={null}
          batchSelected={new Set()}
          onSelect={jest.fn()}
          onToggleBatch={jest.fn()}
          onSelectAll={jest.fn()}
          getActions={() => []}
          onQuickAction={jest.fn()}
          actionBusy={false}
        />
      </TooltipProvider>,
    );

    expect(screen.getByTestId("work-queue-table-scroll")).toHaveClass("overflow-x-auto");
    expect(screen.getByRole("table")).toHaveClass("min-w-[960px]");
  });
});
