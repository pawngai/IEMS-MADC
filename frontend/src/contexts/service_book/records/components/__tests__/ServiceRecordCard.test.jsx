import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import ServiceRecordCard from "@/contexts/service_book/records/components/ServiceRecordCard";

describe("ServiceRecordCard", () => {
  test("formats event metadata into readable labels and values", () => {
    render(
      <ServiceRecordCard
        event={{
          id: "SE-1",
          event_type: "PROMOTION",
          part_code: "IV",
          effective_from: "2024-06-15",
          recorded_at: "2026-03-25T01:40:00Z",
          actor_id: "a1a78532-e9b8-4ccc-b3a4-0e6a5c458da9",
          payload: {
            promotion_date: "2024-06-15",
            to_post: "Upper Division Clerk (UDC)",
            promotion_type: "regular",
            order_date: "2024-06-10",
          },
        }}
        canCorrect={false}
        canVoid={false}
        canAttach={false}
        onCorrect={vi.fn()}
        onVoid={vi.fn()}
        onAttach={vi.fn()}
      />,
    );

    expect(screen.getAllByText("Promotion")).toHaveLength(1);
    expect(screen.getByText("Part IV")).toBeInTheDocument();
    expect(screen.getByText("Effective Date:")).toBeInTheDocument();
    expect(screen.getByText("15 Jun 2024")).toBeInTheDocument();
    expect(screen.getByText("Promotion Type:")).toBeInTheDocument();
    expect(screen.getByText("Regular")).toBeInTheDocument();
    expect(screen.getByText("Order Date:")).toBeInTheDocument();
    expect(screen.getByText("10 Jun 2024")).toBeInTheDocument();
    expect(screen.getByText("By: Internal user")).toBeInTheDocument();
    expect(screen.queryByText("PROMOTION")).not.toBeInTheDocument();
    expect(screen.queryByText("promotion date:")).not.toBeInTheDocument();
    expect(screen.queryByText("2024-06-10")).not.toBeInTheDocument();
    expect(screen.queryByText("a1a78532-e9b8-4ccc-b3a4-0e6a5c458da9")).not.toBeInTheDocument();
  });

  test("renders legacy annual pay events with increment terminology", () => {
    render(
      <ServiceRecordCard
        event={{
          id: "SE-2",
          event_type: "PAY",
          part_code: "IV",
          effective_from: "2025-01-01",
          payload: {
            grant_date: "2025-01-01",
            to_level: "Level 4",
            remarks: "Annual increment for FY 2025-26",
          },
        }}
        canCorrect={false}
        canVoid={false}
        canAttach={false}
        onCorrect={vi.fn()}
        onVoid={vi.fn()}
        onAttach={vi.fn()}
      />,
    );

    expect(screen.getByText("Increment")).toBeInTheDocument();
    expect(screen.getByText("To Level:")).toBeInTheDocument();
    expect(screen.queryByText("Pay")).not.toBeInTheDocument();
  });

  test("lets users expand hidden payload fields instead of showing a dead-end summary", () => {
    render(
      <ServiceRecordCard
        event={{
          id: "SE-3",
          event_type: "PROMOTION",
          part_code: "IV",
          payload: {
            promotion_date: "2024-06-15",
            to_post: "Upper Division Clerk (UDC)",
            promotion_type: "regular",
            order_no: "MADC/Est/2024/3456",
            order_date: "2024-06-10",
            authority: "Chief Executive Member, MADC",
            remarks: "Promotion regularized after review",
            office_name: "MADC Secretariat, Kolasib",
          },
        }}
        canCorrect={false}
        canVoid={false}
        canAttach={false}
        onCorrect={vi.fn()}
        onVoid={vi.fn()}
        onAttach={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Show 2 more fields" })).toBeInTheDocument();
    expect(screen.queryByText("Office Name:")).not.toBeInTheDocument();
    expect(screen.queryByText("Promotion regularized after review")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show 2 more fields" }));

    expect(screen.getByText("Office Name:")).toBeInTheDocument();
    expect(screen.getByText("Promotion regularized after review")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Show fewer fields" })).toBeInTheDocument();
  });

  test("renders nested payload objects as readable summaries instead of raw JSON", () => {
    render(
      <ServiceRecordCard
        event={{
          id: "SE-4",
          event_type: "PROMOTION",
          part_code: "IV",
          payload: {
            promotion_date: "2024-06-15",
            to_post: "Upper Division Clerk (UDC)",
            promotion_type: "regular",
            order_no: "MADC/Est/2024/3456",
            order_date: "2024-06-10",
            authority: "Chief Executive Member, MADC",
            remarks: "Promoted from LDC to UDC after 4 years of regular service",
            pay_change: {
              affects_pay: true,
              old_basic: 25500,
              new_basic: 29200,
              effective_from: "2024-06-15",
              old_level: "Level 2",
              new_level: "Level 4",
            },
          },
        }}
        canCorrect={false}
        canVoid={false}
        canAttach={false}
        onCorrect={vi.fn()}
        onVoid={vi.fn()}
        onAttach={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Show 2 more fields" }));

    expect(screen.getByText("Pay Change:")).toBeInTheDocument();
    expect(screen.getByText("Affects Pay:")).toBeInTheDocument();
    expect(screen.getByText("Yes")).toBeInTheDocument();
    expect(screen.getByText("Old Basic:")).toBeInTheDocument();
    expect(screen.getByText("25500")).toBeInTheDocument();
    expect(screen.getByText("New Level:")).toBeInTheDocument();
    expect(screen.getByText("Level 4")).toBeInTheDocument();
    expect(screen.queryByText(/\{"affects_pay":true/i)).not.toBeInTheDocument();
  });
});