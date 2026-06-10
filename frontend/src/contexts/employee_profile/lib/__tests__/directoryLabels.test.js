import { formatDirectoryEnumLabel } from "@/contexts/employee_profile/lib/directoryLabels";

describe("formatDirectoryEnumLabel", () => {
  test("humanizes uppercase enum values", () => {
    expect(formatDirectoryEnumLabel("ACTIVE")).toBe("Active");
    expect(formatDirectoryEnumLabel("RETIRED")).toBe("Retired");
  });

  test("humanizes underscore and hyphen separated values", () => {
    expect(formatDirectoryEnumLabel("DAILY_WAGE")).toBe("Daily Wage");
    expect(formatDirectoryEnumLabel("FIXED-PAY")).toBe("Fixed Pay");
    expect(formatDirectoryEnumLabel("COMPASSIONATE")).toBe("Compassionate");
  });
});