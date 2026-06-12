import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import EmployeeProfileSummary from "@/modules/employee_master/components/EmployeeProfileSummary";

describe("EmployeeProfileSummary", () => {
  test("prefers canonical service-book Part IV details for the current service card", () => {
    render(
      <EmployeeProfileSummary
        profile={{
          full_name: "Rahul Sharma",
          employee_code: "EMP-1001",
          employment_type: "REGULAR",
          workflow_status: "APPROVED",
          current_designation_id: "Legacy Profile Designation",
          current_department_id: "Finance",
          current_office_id: "Legacy Office",
          date_of_initial_engagement: "2024-01-15",
          gender: "Male",
          date_of_birth: "1990-08-10",
          father_name: "R. Sharma",
          nationality: "Indian",
          marital_status: "SINGLE",
          category: "GENERAL",
          mobile_primary: "9876543210",
          email_official: "rahul.sharma@madc.gov.in",
          identifiers: {
            aadhaar_number: "123456789012",
            pan_number: "ABCDE1234F",
          },
        }}
        serviceBook={{
          part_iv: {
            entries: [
              {
                period_from: "2025-04-01",
                period_to: null,
                office_station: "Accounts HQ",
                post_held: "Section Officer",
                pay_level: "LEVEL_7",
                basic_pay: 52300,
                mode_of_recruitment: "DIRECT",
                _meta: {
                  workflow_state: "LOCKED",
                  locked_at: "2025-04-02T10:00:00Z",
                },
              },
            ],
          },
        }}
      />
    );

    expect(screen.getByText("Current Service Details")).toBeInTheDocument();
    expect(screen.getByText("Personal Profile")).toBeInTheDocument();
    expect(screen.getByText("Official IDs")).toBeInTheDocument();
    expect(screen.getByText("Service Book Records")).toBeInTheDocument();

    expect(screen.getByText("Pay Level")).toBeInTheDocument();
    expect(screen.getByText("Current Pay")).toBeInTheDocument();
    expect(screen.getByText("Level 7")).toBeInTheDocument();
    expect(screen.getByText("₹52,300")).toBeInTheDocument();
    expect(screen.getByText("Section Officer")).toBeInTheDocument();
    expect(screen.getByText("Accounts HQ")).toBeInTheDocument();
    expect(screen.getByText("Approved")).toBeInTheDocument();
    expect(screen.getByText("Direct")).toBeInTheDocument();
    expect(screen.getAllByText("General").length).toBeGreaterThan(0);
    expect(screen.getByText("01/04/2025")).toBeInTheDocument();

    expect(screen.queryByText("Profile Extension")).not.toBeInTheDocument();
    expect(screen.queryByText("Employee Identity")).not.toBeInTheDocument();
    expect(screen.queryByText("Service Book Managed Data")).not.toBeInTheDocument();
    expect(screen.queryByText("Legacy Profile Designation")).not.toBeInTheDocument();
    expect(screen.queryByText("Legacy Office")).not.toBeInTheDocument();
    expect(screen.queryByText("PROFILE_LEVEL")).not.toBeInTheDocument();
  });

  test("uses reference label maps to replace raw designation and department codes", () => {
    render(
      <EmployeeProfileSummary
        profile={{
          full_name: "Rahul Sharma",
          employee_code: "EMP-1001",
          employment_type: "REGULAR",
          workflow_status: "APPROVED",
          current_designation_id: "ASO",
          current_department_id: "FIN",
          current_office_id: "HQ",
          date_of_initial_engagement: "2024-01-15",
          gender: "MALE",
          date_of_birth: "1990-08-10",
          father_name: "R. Sharma",
          nationality: "INDIAN",
          marital_status: "SINGLE",
          category: "GENERAL",
        }}
        referenceLabelMaps={{
          designation: new Map([["ASO", "Assistant Section Officer"]]),
          department: new Map([["FIN", "Finance Department"]]),
          office: new Map([["HQ", "Headquarters"]]),
        }}
      />
    );

    expect(screen.getByText("Assistant Section Officer in Finance Department")).toBeInTheDocument();
    expect(screen.getByText("Assistant Section Officer")).toBeInTheDocument();
    expect(screen.getByText("Finance Department")).toBeInTheDocument();
    expect(screen.getByText("Headquarters")).toBeInTheDocument();
    expect(screen.getByText("Male")).toBeInTheDocument();
    expect(screen.getAllByText("General").length).toBeGreaterThan(0);
  });

  test("shows draft employee status for draft identity records", () => {
    render(
      <EmployeeProfileSummary
        profile={{
          full_name: "Draft Identity Employee",
          employee_code: "MADC-2026-R0001",
          employment_type: "REGULAR",
          workflow_status: "DRAFT",
          identity_workflow_status: "DRAFT",
          employee_status: "DRAFT",
          current_designation_id: "ASO",
          current_department_id: "FIN",
        }}
      />
    );

    expect(screen.getAllByText("Draft").length).toBeGreaterThanOrEqual(2);
    expect(screen.queryByText("Active")).not.toBeInTheDocument();
  });

  test("shows 100 percent completion when both backend completion flags are true", () => {
    render(
      <EmployeeProfileSummary
        profile={{
          full_name: "Completed Non-Regular Employee",
          employee_code: "MADC-2026-E0006",
          employment_type: "FIXED_PAY",
          workflow_status: "LOCKED",
          employee_section_completed: true,
          data_entry_section_completed: true,
          current_designation_id: "ES",
          current_department_id: "GAD",
          date_of_initial_engagement: "2025-05-12",
          gender: "Female",
          date_of_birth: "1992-05-12",
          mobile_primary: "9862000517",
        }}
        referenceLabelMaps={{
          designation: new Map([["ES", "Executive Secretary"]]),
          department: new Map([["GAD", "General Administration & Control"]]),
        }}
      />
    );

    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  test("renders non-regular engagement details instead of regular service-book fields", () => {
    render(
      <EmployeeProfileSummary
        profile={{
          full_name: "Completed Non-Regular Employee",
          employee_code: "MADC-2026-E0006",
          employment_type: "FIXED_PAY",
          workflow_status: "SUBMITTED",
          current_designation_id: "ES",
          current_department_id: "GAD",
          date_of_initial_engagement: "2025-05-12",
          engagement_order_no: "ENG-205117",
          engagement_order_date: "2026-04-12",
          fixed_monthly_amount: 25000,
          engagement_remarks: "Live submit button validation",
          gender: "Female",
          date_of_birth: "1992-05-12",
          mobile_primary: "9862000517",
        }}
        referenceLabelMaps={{
          designation: new Map([["ES", "Executive Secretary"]]),
          department: new Map([["GAD", "General Administration & Control"]]),
        }}
      />
    );

    expect(screen.getByText("Current Engagement Details")).toBeInTheDocument();
    expect(screen.queryByText("Current Service Details")).not.toBeInTheDocument();
    expect(screen.getByText("Engagement Order No")).toBeInTheDocument();
    expect(screen.getByText("ENG-205117")).toBeInTheDocument();
    expect(screen.getByText("Monthly Remuneration")).toBeInTheDocument();
    expect(screen.getByText("₹25,000")).toBeInTheDocument();
    expect(screen.getByText("Notes")).toBeInTheDocument();
    expect(screen.getByText("Live submit button validation")).toBeInTheDocument();
    expect(screen.queryByText("Service / Cadre")).not.toBeInTheDocument();
    expect(screen.queryByText("Service Group")).not.toBeInTheDocument();
    expect(screen.queryByText("Mode of Recruitment")).not.toBeInTheDocument();
    expect(screen.queryByText("Current Posting From")).not.toBeInTheDocument();
  });

  test("shows wage-based fields without leaking monthly remuneration on wages records", () => {
    render(
      <EmployeeProfileSummary
        profile={{
          full_name: "Wages Employee",
          employee_code: "MADC-2026-E0007",
          employment_type: "WAGES",
          workflow_status: "DRAFT",
          current_designation_id: "ES",
          current_department_id: "GAD",
          date_of_initial_engagement: "2025-05-12",
          daily_wage_rate: 800,
          wage_rate_unit: "PER_DAY",
          engagement_office: "District Treasury",
          nature_of_work: "Clerical support",
          fixed_monthly_amount: 25000,
          engagement_remarks: "Wage-based validation",
          gender: "Female",
          date_of_birth: "1992-05-12",
          mobile_primary: "9862000517",
        }}
        referenceLabelMaps={{
          designation: new Map([["ES", "Executive Secretary"]]),
          department: new Map([["GAD", "General Administration & Control"]]),
        }}
      />
    );

    expect(screen.getByText("Wage Rate")).toBeInTheDocument();
    expect(screen.getByText("₹800")).toBeInTheDocument();
    expect(screen.getByText("Wage Rate Unit")).toBeInTheDocument();
    expect(screen.getByText("Per Day")).toBeInTheDocument();
    expect(screen.getByText("Engagement Office")).toBeInTheDocument();
    expect(screen.getByText("District Treasury")).toBeInTheDocument();
    expect(screen.getByText("Nature of Work")).toBeInTheDocument();
    expect(screen.getByText("Clerical support")).toBeInTheDocument();
    expect(screen.queryByText("Monthly Remuneration")).not.toBeInTheDocument();
    expect(screen.queryByText("₹25,000")).not.toBeInTheDocument();
  });

  test("prefers serviceSummary over profile for employment classification after regularisation", () => {
    render(
      <EmployeeProfileSummary
        profile={{
          full_name: "Regularised Employee",
          employee_code: "MADC-2026-E0009",
          employment_type: "CONTRACT",
          workflow_status: "LOCKED",
          current_designation_id: "ES",
          current_department_id: "GAD",
          date_of_initial_engagement: "2025-05-12",
          engagement_order_no: "ENG-301",
          engagement_end_date: "2026-04-30",
          fixed_monthly_amount: 50000,
          engagement_remarks: "Initial engagement before regularisation",
        }}
        serviceSummary={{
          current_employment_type_code: "REGULAR",
          current_employment_class: "REGULAR",
          eligible_for_service_book: true,
        }}
        referenceLabelMaps={{
          designation: new Map([["ES", "Executive Secretary"]]),
          department: new Map([["GAD", "General Administration & Control"]]),
        }}
      />
    );

    expect(screen.getByText("Current Service Details")).toBeInTheDocument();
    expect(screen.queryByText("Current Engagement Details")).not.toBeInTheDocument();
    expect(screen.getAllByText("Regular").length).toBeGreaterThan(0);

    const priorCard = screen.getByTestId("employee-profile-prior-engagement");
    expect(priorCard).toBeInTheDocument();
    expect(priorCard).toHaveTextContent("Prior Engagement");
    expect(priorCard).toHaveTextContent("Contract");
    expect(priorCard).toHaveTextContent("ENG-301");
    expect(priorCard).toHaveTextContent("₹50,000");
    expect(priorCard).toHaveTextContent("Initial engagement before regularisation");
  });

  test("does not render the Prior Engagement card for employees who were always regular", () => {
    render(
      <EmployeeProfileSummary
        profile={{
          full_name: "Always Regular",
          employee_code: "MADC-2026-R0009",
          employment_type: "REGULAR",
          workflow_status: "APPROVED",
        }}
        serviceSummary={{
          current_employment_type_code: "REGULAR",
          current_employment_class: "REGULAR",
          eligible_for_service_book: true,
        }}
      />
    );

    expect(screen.queryByTestId("employee-profile-prior-engagement")).not.toBeInTheDocument();
  });

  test("shows a trimmed personal profile for non-regular employees", () => {
    render(
      <EmployeeProfileSummary
        profile={{
          full_name: "Non-Regular Personal Profile",
          employee_code: "MADC-2026-E0008",
          employment_type: "FIXED_PAY",
          workflow_status: "DRAFT",
          gender: "Female",
          date_of_birth: "1992-05-12",
          category: "GENERAL",
          marital_status: "SINGLE",
          current_designation_id: "ES",
          current_department_id: "GAD",
          date_of_initial_engagement: "2025-05-12",
        }}
        referenceLabelMaps={{
          designation: new Map([["ES", "Executive Secretary"]]),
          department: new Map([["GAD", "General Administration & Control"]]),
        }}
      />
    );

    expect(screen.getByText("Personal Profile")).toBeInTheDocument();
    expect(screen.getByText("Full Name")).toBeInTheDocument();
    expect(screen.getByText("Gender")).toBeInTheDocument();
    expect(screen.getByText("Date of Birth")).toBeInTheDocument();
    expect(screen.getByText("Category")).toBeInTheDocument();
    expect(screen.getByText("General")).toBeInTheDocument();
    expect(screen.getByText("Marital Status")).toBeInTheDocument();
    expect(screen.getByText("Single")).toBeInTheDocument();
    expect(screen.queryByText("Father's Name")).not.toBeInTheDocument();
    expect(screen.queryByText("Mother's Name")).not.toBeInTheDocument();
    expect(screen.queryByText("Religion")).not.toBeInTheDocument();
    expect(screen.queryByText("Blood Group")).not.toBeInTheDocument();
    expect(screen.queryByText("Nationality")).not.toBeInTheDocument();
    expect(screen.queryByText("Spouse Name")).not.toBeInTheDocument();
  });
});