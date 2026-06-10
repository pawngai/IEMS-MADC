import { describe, expect, test } from "vitest";

import { normalizeComplete } from "@/contexts/service_book/services/projectionNormalizer";

describe("projectionNormalizer Part VIII status handling", () => {
  test("preserves audit comment resolution status from payload", () => {
    const result = normalizeComplete("E2E-EMP-001", [
      {
        id: "entry-1",
        employee_id: "E2E-EMP-001",
        part_key: "SB_PART_VIII",
        schema_key: "SB_VIII_AUDIT_COMMENT",
        status: "LOCKED",
        workflow_state: "LOCKED",
        created_at: "2026-03-15T21:52:37.336031+00:00",
        payload: {
          comment_text: "All service book records verified and found in order.",
          auditor_name: "Internal Auditor",
          status: "RESOLVED",
        },
      },
    ]);

    expect(result.part_viii.total_comments).toBe(1);
    expect(result.part_viii.resolved_comments).toBe(1);
    expect(result.part_viii.open_comments).toBe(0);
    expect(result.part_viii.comments[0].status).toBe("RESOLVED");
    expect(result.part_viii.comments[0]._meta.workflow_state).toBe("LOCKED");
  });
});

describe("projectionNormalizer Part II-B nomination fallback", () => {
  test("preserves nominations embedded in family-sheet payload when row entries are absent", () => {
    const result = normalizeComplete("E2E-EMP-001", [
      {
        id: "entry-iib",
        employee_id: "E2E-EMP-001",
        part_key: "SB_PART_II_B",
        schema_key: "SB_IIB_FAMILY_SHEET",
        status: "LOCKED",
        workflow_state: "LOCKED",
        created_at: "2026-03-15T21:52:37.336031+00:00",
        payload: {
          pcf_account_number: "PCF/HR/001",
          pcf_nomination_date: "2018-07-01",
          pcf_nomination: [{ name: "Arun Menon", relationship: "SPOUSE", share_percent: 100 }],
          nps_pran_number: "110056789002",
          nps_nomination_date: "2018-07-01",
          nps_nomination: [{ name: "Arun Menon", relationship: "SPOUSE", share_percent: 100 }],
        },
      },
    ]);

    expect(result.part_ii_b.pcf_nomination).toHaveLength(1);
    expect(result.part_ii_b.pcf_nomination[0].pcf_account_number).toBe("PCF/HR/001");
    expect(result.part_ii_b.pcf_nomination[0].pcf_nomination_date).toBe("2018-07-01");
    expect(result.part_ii_b.pcf_nomination[0].pcf_nomination).toEqual([
      { name: "Arun Menon", relationship: "SPOUSE", share_percent: 100 },
    ]);
    expect(result.part_ii_b.nps_nomination).toHaveLength(1);
    expect(result.part_ii_b.nps_nomination[0].nps_pran_number).toBe("110056789002");
    expect(result.part_ii_b.nps_nomination[0].nps_nomination).toEqual([
      { name: "Arun Menon", relationship: "SPOUSE", share_percent: 100 },
    ]);
  });
});

describe("projectionNormalizer Part V derived totals", () => {
  test("derives total verified service from verification rows", () => {
    const result = normalizeComplete("E2E-EMP-001", [
      {
        id: "entry-v-1",
        employee_id: "E2E-EMP-001",
        part_key: "SB_PART_V",
        schema_key: "SB_V_SERVICE_VERIFICATION_ROW",
        status: "LOCKED",
        workflow_state: "LOCKED",
        created_at: "2026-03-15T21:52:37.336031+00:00",
        payload: {
          period_from: "2018-07-01",
          period_to: "2026-02-20",
          post_held: "ASO",
          purpose_of_qualification: "PENSION",
          verified: true,
        },
      },
    ]);

    expect(result.part_v.verification_entries).toHaveLength(1);
    expect(result.part_v.total_verified_service).toEqual({ years: 7, months: 7, days: 20 });
  });

  test("derives Part V verification entries from Part III and Part IV rows", () => {
    const result = normalizeComplete("E2E-EMP-001", [
      {
        id: "entry-iii-prev-1",
        employee_id: "E2E-EMP-001",
        part_key: "SB_PART_III",
        schema_key: "SB_III_PREVIOUS_SERVICE_ROW",
        status: "LOCKED",
        workflow_state: "LOCKED",
        locked_by: "Approving Authority",
        locked_at: "2026-03-16T00:40:00.000Z",
        payload: {
          service_from: "2018-07-01",
          service_to: "2020-06-30",
          post_held: "ASO",
          organization: "District Treasury",
          purpose_of_qualification: "PENSION",
          certified_by: "Approving Authority",
        },
      },
      {
        entry_id: "entry-iv-1",
        employee_id: "E2E-EMP-001",
        part_code: "IV",
        status: "APPROVED",
        workflow_state: "APPROVED",
        approved_by: "Verification Cell",
        approved_at: "2026-03-16T00:45:00.000Z",
        payload: {
          effective_from: "2021-01-01",
          effective_to: "2021-01-31",
          event_type: "PROMOTION",
          post_held: "Section Officer",
          office_station: "Accounts HQ",
          remarks: "Promotion regularized",
        },
      },
    ]);

    expect(result.part_v.verification_entries).toHaveLength(2);
    expect(result.part_v.verification_entries[0]).toMatchObject({
      period_from: "2018-07-01",
      period_to: "2020-06-30",
      post_held: "ASO",
      purpose_of_qualification: "PENSION",
      certifying_officer: "Approving Authority",
      verified: true,
    });
    expect(result.part_v.verification_entries[1]).toMatchObject({
      period_from: "2021-01-01",
      period_to: "2021-01-31",
      post_held: "Section Officer",
      purpose_of_qualification: "PROMOTION",
      remarks: "Promotion regularized",
      verified: true,
    });
    expect(result.part_v.total_verified_service).toEqual({ years: 2, months: 7, days: 0 });
  });
});

describe("projectionNormalizer projected Part IV entries", () => {
  test("maps service-event projections without schema keys into Part IV entries", () => {
    const result = normalizeComplete("E2E-EMP-001", [
      {
        entry_id: "entry-iv-1",
        employee_id: "E2E-EMP-001",
        part_code: "IV",
        event_name: "ServiceEventLifecycleApproved",
        status: "APPROVED",
        workflow_state: "APPROVED",
        created_at: "2026-03-15T22:47:43.874377+00:00",
        payload: {
          effective_from: "2026-03-16",
          effective_to: null,
          event_type: "DISCIPLINARY",
          order_no: "SB-NEWREG-001",
          reason: "New regular employee servicebook entry test",
          suspension_date: "2026-03-16",
        },
      },
    ]);

    expect(result.part_iv.entries).toHaveLength(1);
    expect(result.part_iv.entries[0]).toMatchObject({
      event_type: "DISCIPLINARY",
      period_from: "2026-03-16",
      event_order_number: "SB-NEWREG-001",
      reason: "New regular employee servicebook entry test",
      suspension_date: "2026-03-16",
    });
    expect(result.part_iv.entries[0]._meta.workflow_state).toBe("APPROVED");
  });

  test("normalizes service classification fields from projected appointment and promotion payloads", () => {
    const result = normalizeComplete("E2E-EMP-001", [
      {
        entry_id: "entry-iv-appointment-1",
        employee_id: "E2E-EMP-001",
        part_code: "IV",
        event_name: "ServiceEventLifecycleApproved",
        created_at: "2026-03-15T22:47:43.874377+00:00",
        payload: {
          effective_from: "2025-01-01",
          event_type: "APPOINTMENT",
          service: "Mizoram District Council Service",
          service_group: "Group A",
          grade: "Junior Grade",
        },
      },
      {
        entry_id: "entry-iv-promotion-1",
        employee_id: "E2E-EMP-001",
        part_code: "IV",
        event_name: "ServiceEventLifecycleApproved",
        created_at: "2026-03-15T22:47:43.874377+00:00",
        payload: {
          effective_from: "2026-01-01",
          event_type: "PROMOTION",
          to_grade: "Selection Grade",
        },
      },
    ]);

    expect(result.part_iv.entries[0]).toMatchObject({
      service: "Mizoram District Council Service",
      service_group: "Group A",
      grade: "Junior Grade",
    });
    expect(result.part_iv.entries[1]).toMatchObject({
      grade: "Selection Grade",
    });
  });
});

describe("projectionNormalizer Part VI leave account", () => {
  test("combines opening balance and leave transactions into Part VI", () => {
    const result = normalizeComplete("E2E-EMP-001", [
      {
        id: "entry-vi-opening",
        employee_id: "E2E-EMP-001",
        part_key: "SB_PART_VI",
        schema_key: "SB_VI_LEAVE_OPENING_BALANCE",
        status: "LOCKED",
        workflow_state: "LOCKED",
        payload: {
          earned_leave_balance: 18,
          half_pay_leave_balance: 10,
          commuted_leave_balance: 5,
          leave_not_due_balance: 4,
        },
      },
      {
        id: "entry-vi-txn-1",
        employee_id: "E2E-EMP-001",
        part_key: "SB_PART_VI",
        schema_key: "SB_VI_LEAVE_TRANSACTION_ROW",
        status: "APPROVED",
        workflow_state: "APPROVED",
        payload: {
          leave_type: "EL",
          transaction_type: "CREDIT",
          transaction_date: "2026-01-31",
          credit_days: 3,
          closing_balance: 21,
          remarks: "Half-yearly credit",
        },
      },
    ]);

    expect(result.part_vi).toMatchObject({
      earned_leave_balance: 18,
      half_pay_leave_balance: 10,
      commuted_leave_balance: 5,
      leave_not_due_balance: 4,
    });
    expect(result.part_vi.transactions).toHaveLength(1);
    expect(result.part_vi.transactions[0]).toMatchObject({
      leave_type: "EL",
      transaction_type: "CREDIT",
      transaction_date: "2026-01-31",
      credit_days: 3,
      closing_balance: 21,
      remarks: "Half-yearly credit",
    });
    expect(result.part_vi.transactions[0]._meta.workflow_state).toBe("APPROVED");
  });
});