import { describe, expect, test } from "vitest";

import {
  buildCsvContent,
  buildWorkforceDrilldownExportDataset,
} from "@/contexts/analytics/lib/workforceDrilldownExport";

describe("buildWorkforceDrilldownExportDataset", () => {
  test("keeps employee identity columns and only includes selected workforce fields", () => {
    const dataset = buildWorkforceDrilldownExportDataset({
      rows: [
        {
          employee_id: "emp-1",
          employee_code: "MADC-001",
          employee_name: "Alice Example",
          department_id: "FIN",
          designation_id: "LDC",
          employment_type: "CONTRACTUAL",
          employee_status: "ACTIVE",
          gender: "FEMALE",
        },
      ],
      visibleFieldKeys: ["department", "status", "gender"],
      getDepartmentLabel: () => "Finance Department",
      getDesignationLabel: () => "Lower Division Clerk",
      getEmploymentTypeLabel: () => "Contractual",
      getStatusLabel: () => "Active",
      getGenderLabel: () => "Female",
      getOfficeLabel: () => "Headquarters",
      getWorkflowStatusLabel: () => "Submitted",
      getServiceLabel: () => "Mizoram Civil Service",
      getServiceGroupLabel: () => "Group B",
      getMaritalStatusLabel: () => "Single",
      getDateOfBirthLabel: () => "1/1/1990",
      getInitialEngagementLabel: () => "1/1/2024",
      getStatusEffectiveDateLabel: () => "1/2/2024",
      getReportingOfficerLabel: () => "emp-9",
      getCreatedAtLabel: () => "Jan 1, 2024, 10:00 AM",
      getUpdatedAtLabel: () => "Jan 2, 2024, 11:00 AM",
    });

    expect(dataset.headers).toEqual([
      "Employee ID",
      "Employee Code",
      "Employee Name",
      "Department",
      "Employee Status",
      "Gender",
    ]);
    expect(dataset.rows).toEqual([
      {
        "Employee ID": "emp-1",
        "Employee Code": "MADC-001",
        "Employee Name": "Alice Example",
        "Department": "Finance Department",
        "Employee Status": "Active",
        "Gender": "Female",
      },
    ]);
  });
});

describe("buildCsvContent", () => {
  test("escapes commas, quotes, and newlines in exported cells", () => {
    const csv = buildCsvContent({
      headers: ["Employee Name", "Department"],
      rows: [
        {
          "Employee Name": 'Alice "AJ" Example',
          "Department": "Finance, Audit\nWing",
        },
      ],
    });

    expect(csv).toBe(
      'Employee Name,Department\r\n"Alice ""AJ"" Example","Finance, Audit\nWing"\r\n'
    );
  });
});