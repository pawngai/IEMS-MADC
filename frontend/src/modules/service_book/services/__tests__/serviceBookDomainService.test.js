import { beforeEach, describe, expect, test, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  getComplete: vi.fn(),
  printFull: vi.fn(),
}));

vi.mock("@/modules/service_book/api/projectionApi", () => ({
  projectionAPI: {
    getComplete: mocks.getComplete,
  },
}));

vi.mock("@/modules/service_book/api/printApi", () => ({
  printAPI: {
    printFull: mocks.printFull,
  },
}));

import {
  generateServiceBookPrintModel,
  validateServiceBookEligibility,
} from "@/modules/service_book/services/serviceBookDomainService";

describe("serviceBookDomainService eligibility", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("allows REGULAR employment type", () => {
    expect(validateServiceBookEligibility({ employment_type: "REGULAR" })).toBe(true);
    expect(validateServiceBookEligibility("REGULAR")).toBe(true);
  });

  test("blocks non-regular employment type", () => {
    expect(() =>
      validateServiceBookEligibility({ employment_type: "CONTRACTUAL" }),
    ).toThrow(/REGULAR/);
  });

  test("uses employee service summary eligibility flag", () => {
    expect(validateServiceBookEligibility({ eligible_for_service_book: true })).toBe(true);
    expect(() =>
      validateServiceBookEligibility({
        current_employment_type_code: "REGULAR",
        eligible_for_service_book: false,
      }),
    ).toThrow(/REGULAR/);
  });
});

describe("serviceBookDomainService print model", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("falls back to dedicated print API when read projection is forbidden", async () => {
    mocks.getComplete.mockRejectedValueOnce({ response: { status: 403 } });
    mocks.printFull.mockResolvedValueOnce({
      data: {
        parts: {
          SB_PART_I: [
            {
              id: "ENTRY-1",
              schema_key: "SB_I_BIODATA",
              payload: { name_in_block_letters: "A Regular Employee" },
            },
          ],
        },
      },
    });

    const result = await generateServiceBookPrintModel({
      employeeId: "EMP-1",
      employeeOrType: "REGULAR",
    });

    expect(mocks.printFull).toHaveBeenCalledWith("EMP-1");
    expect(result.service_book.part_i).toMatchObject({
      name_in_block_letters: "A Regular Employee",
    });
  });

  test("does not fall back to full print payload for filtered ESS projections", async () => {
    const error = { response: { status: 403 } };
    mocks.getComplete.mockRejectedValueOnce(error);

    await expect(
      generateServiceBookPrintModel({
        employeeId: "EMP-1",
        employeeOrType: "REGULAR",
        statuses: ["APPROVED", "LOCKED"],
      }),
    ).rejects.toBe(error);
    expect(mocks.printFull).not.toHaveBeenCalled();
  });
});
