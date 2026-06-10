import { describe, expect, test } from "vitest";

import {
  CanonicalCategory,
  CANONICAL_CATEGORY_OPTIONS,
  CATEGORY_TO_PART_CODE,
  getFallbackServiceRecordSchema,
  normalizeServiceRecordSchema,
  buildRecordCommand,
  buildCpcChangeFixationCommand,
} from "@/contexts/service_book/records/model/serviceBookRecordsModel";

describe("serviceBookRecordsModel", () => {
  test("buildRecordCommand routes promotion records to the configured service-book part", () => {
    const command = buildRecordCommand({
      employeeId: "EMP-100",
      eventType: "PROMOTION",
      payload: { order_no: "PROMO-12" },
    });

    expect(command.part_code).toBe(CATEGORY_TO_PART_CODE.PROMOTION);
    expect(command.part_code).toBe("IV");
  });

  test("buildRecordCommand keeps optional dates nullable", () => {
    const command = buildRecordCommand({
      employeeId: "EMP-101",
      eventType: "GENERIC",
      payload: { note: "test" },
    });

    expect(command.effective_from).toBeNull();
    expect(command.effective_to).toBeNull();
  });

  test("buildRecordCommand maps category directly to backend event type", () => {
    const command = buildRecordCommand({
      employeeId: "EMP-102",
      eventType: "TRANSFER",
      payload: { transfer_date: "2026-03-14", transfer_type: "office", to_office: "HQ" },
    });

    expect(command.event_type).toBe(CanonicalCategory.TRANSFER);
    expect(command.payload).toEqual({ transfer_date: "2026-03-14", transfer_type: "office", to_office: "HQ" });
  });

  test("buildCpcChangeFixationCommand emits the canonical record-event payload contract", () => {
    const command = buildCpcChangeFixationCommand({
      employeeId: "EMP-103",
      effectiveDate: "2026-04-01",
      orderNo: "MADC/FIN/CPC/2026/001",
      orderDate: "2026-04-02",
      fromCpc: "6TH_CPC",
      toCpc: "7TH_CPC",
      preRevisedPay: { basic_pay: "15600" },
      fitment: { pay_level: "Level 6", pay_cell_index: 1 },
      postRevisedPay: { pay_level: "Level 6", pay_cell_index: 1, basic_pay: "35400" },
      option: {},
      remarks: "Migrated to revised structure",
    });

    expect(command.event_type).toBe("CPC_PAY_FIXATION");
    expect(command.part_code).toBe("IV");
    expect(command.effective_from).toBe("2026-04-01");
    expect(command.payload.pre_revised_pay).toEqual({ basic_pay: "15600" });
    expect(command.payload.post_revised_pay.basic_pay).toBe("35400");
  });

  test("fallback schema exposes category-level defaults", () => {
    const fallback = getFallbackServiceRecordSchema();

    expect(fallback.categoryToPartCode.INCREMENT).toBe("IV");
    expect(fallback.categoryToPartCode.CUSTOM).toBe("IV");
    expect(fallback.requiredPayloadKeysByCategory.CUSTOM).toEqual([]);
    expect(fallback.requiredPayloadKeysByCategory.PROMOTION).toEqual(["promotion_date", "to_post", "promotion_type"]);
  });

  test("normalizeServiceRecordSchema exposes category-based mappings", () => {
    const schema = normalizeServiceRecordSchema({
      canonical_category_options: [{ value: "PROMOTION", label: "Promotion" }],
      category_to_part_code: { PROMOTION: "II-A" },
      required_payload_keys_by_category: { PROMOTION: ["promotion_date"] },
      field_definitions: { promotion_date: { label: "Promotion Date", type: "date" } },
    });

    expect(schema.canonicalCategoryOptions).toEqual([{ value: "PROMOTION", label: "Promotion" }]);
    expect(schema.categoryToPartCode.PROMOTION).toBe("II-A");
    expect(schema.requiredPayloadKeysByCategory.PROMOTION).toEqual(["promotion_date"]);
  });

  test("fallback schema exposes one canonical category list", () => {
    expect(CANONICAL_CATEGORY_OPTIONS.some((item) => item.value === CanonicalCategory.CUSTOM)).toBe(true);
    expect(CANONICAL_CATEGORY_OPTIONS.some((item) => item.value === CanonicalCategory.PROMOTION)).toBe(true);
    expect(CANONICAL_CATEGORY_OPTIONS.some((item) => item.value === CanonicalCategory.CONFIRMATION)).toBe(false);
    expect(CANONICAL_CATEGORY_OPTIONS.some((item) => item.value === CanonicalCategory.GENERIC)).toBe(false);
  });
});
