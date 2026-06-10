import { describe, expect, test, vi } from "vitest";
import { OPENING_STATUS } from "@/contexts/service_book/opening/model/openingStatus";
import { resolveOpeningPermissions } from "@/contexts/service_book/opening/model/openingPermissions";
import {
  buildOpeningEligibility,
  canSubmitOpeningDraft,
} from "@/contexts/service_book/opening/services/openingDomainService";

describe("Service Book Opening domain service", () => {
  test("non-regular employee cannot open Service Book", () => {
    expect(buildOpeningEligibility({ employment_type: "CONTRACTUAL" })).toEqual({
      eligible: false,
      reason: "Service Book Opening is only available for REGULAR employees.",
    });
  });

  test("regular employee can open draft", () => {
    expect(buildOpeningEligibility({ employment_type: "REGULAR" }).eligible).toBe(true);
    expect(
      resolveOpeningPermissions({
        can: (permission) => permission === "SERVICE_BOOK_OPENING_CREATE",
        status: OPENING_STATUS.NOT_STARTED,
        eligible: true,
      }).canCreate
    ).toBe(true);
  });

  test("submit disabled until required opening parts are complete", () => {
    expect(canSubmitOpeningDraft({ parts: { part_i: { employee_id: "EMP-1" } } })).toBe(false);

    expect(
      canSubmitOpeningDraft({
        parts: {
          part_i: {
            employee_id: "EMP-1",
            employee_code: "MADC-1",
            name_in_block_letters: "DEMO EMPLOYEE",
            father_name: "Demo Father",
            marital_status: "SINGLE",
            caste_category: "GENERAL",
            date_of_birth_christian: "1990-01-01",
          },
          part_iia: {
            medical_fitness_certificate: true,
            character_verification_done: true,
            entries_confirmed: true,
          },
          part_iib: {},
          part_iii: {},
        },
      })
    ).toBe(false);

    expect(
      canSubmitOpeningDraft({
        parts: {
          part_i: {
            employee_id: "EMP-1",
            employee_code: "MADC-1",
            name_in_block_letters: "DEMO EMPLOYEE",
            father_name: "Demo Father",
            marital_status: "SINGLE",
            caste_category: "GENERAL",
            date_of_birth_christian: "1990-01-01",
          },
          part_iia: {
            medical_fitness_certificate: true,
            character_verification_done: true,
            entries_confirmed: true,
          },
          part_iib: {
            family_members: [{ name: "Asha", relationship: "Spouse" }],
          },
          part_iii: {
            previous_services: "Nil",
          },
        },
      })
    ).toBe(true);
  });

  test("verifier and approver actions are permission-gated", () => {
    const canVerify = vi.fn((permission) => permission === "SERVICE_BOOK_OPENING_VERIFY");
    const submitted = resolveOpeningPermissions({
      can: canVerify,
      status: OPENING_STATUS.SUBMITTED,
      eligible: true,
    });
    expect(submitted.canVerify).toBe(true);
    expect(submitted.canApprove).toBe(false);

    const canApprove = vi.fn((permission) => permission === "SERVICE_BOOK_OPENING_APPROVE");
    const verified = resolveOpeningPermissions({
      can: canApprove,
      status: OPENING_STATUS.VERIFIED,
      eligible: true,
    });
    expect(verified.canVerify).toBe(false);
    expect(verified.canApprove).toBe(true);
  });
});
