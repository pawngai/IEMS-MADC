import { describe, expect, test } from "vitest";

import {
  classifyServiceRecord,
  routeServiceRecordToServiceBook,
  validateServiceRecordPayload,
} from "@/modules/service_book/records/services/serviceBookRecordDomainService";

describe("serviceBookRecordDomainService", () => {
  test("classifies core operational event types", () => {
    expect(classifyServiceRecord("appointment").event_type).toBe("APPOINTMENT");
    expect(classifyServiceRecord("promotion").event_type).toBe("PROMOTION");
    expect(classifyServiceRecord("increment").event_type).toBe("INCREMENT");
    expect(classifyServiceRecord("suspension").event_type).toBe("SUSPENSION");
    expect(classifyServiceRecord("custom").event_type).toBe("GENERIC");
  });

  test("validates payload and normalizes event type", () => {
    const normalized = validateServiceRecordPayload({
      employee_id: "EMP-100",
      event_type: "appointment",
      payload: { order_no: "123" },
    });

    expect(normalized.event_type).toBe("APPOINTMENT");
  });

  test("normalizes custom category to generic storage type", () => {
    const normalized = validateServiceRecordPayload({
      employee_id: "EMP-100",
      event_type: "CUSTOM",
      payload: { remarks: "Custom event" },
    });

    expect(normalized.event_type).toBe("GENERIC");
  });

  test("preserves increment event types during normalization", () => {
    const normalized = validateServiceRecordPayload({
      employee_id: "EMP-100",
      event_type: "increment",
      payload: {
        increment_date: "2026-03-14",
        increment_type: "annual",
      },
    });

    expect(normalized.event_type).toBe("INCREMENT");
  });

  test("passes through external CPC change fixation commands", () => {
    const normalized = validateServiceRecordPayload({
      employee_id: "EMP-100",
      event_type: "CPC_CHANGE_FIXATION",
      effective_date: "2026-04-01",
      order_no: "MADC/FIN/CPC/2026/001",
      order_date: "2026-04-02",
      from_cpc: "6TH_CPC",
      to_cpc: "7TH_CPC",
      pre_revised_pay: { basic_pay: "15600" },
      fitment: { pay_level: "Level 6", pay_cell_index: 1 },
      post_revised_pay: { pay_level: "Level 6", pay_cell_index: 1, basic_pay: "35400" },
      option: {},
    });

    expect(normalized.event_type).toBe("CPC_PAY_FIXATION");
    expect(normalized.post_revised_pay.basic_pay).toBe("35400");
  });

  test("accepts canonical CPC pay fixation commands without a flat payload object", () => {
    const normalized = validateServiceRecordPayload({
      employee_id: "EMP-100",
      event_type: "CPC_PAY_FIXATION",
      effective_date: "2026-04-01",
      order_no: "MADC/FIN/CPC/2026/001",
      order_date: "2026-04-02",
      from_cpc: "6TH_CPC",
      to_cpc: "7TH_CPC",
      pre_revised_pay: { basic_pay: "15600" },
      fitment: { pay_level: "Level 6", pay_cell_index: 1 },
      post_revised_pay: { pay_level: "Level 6", pay_cell_index: 1, basic_pay: "35400" },
      option: {},
    });

    expect(normalized.event_type).toBe("CPC_PAY_FIXATION");
    expect(normalized.post_revised_pay.basic_pay).toBe("35400");
  });

  test("route metadata preserves service-book authority", () => {
    expect(routeServiceRecordToServiceBook({ status: "APPROVED" }).routed).toBe(true);
    expect(
      routeServiceRecordToServiceBook({ status: "APPROVED" }).service_book_remains_authoritative,
    ).toBe(true);
    expect(routeServiceRecordToServiceBook({ status: "DRAFT" }).routed).toBe(false);
  });
});
