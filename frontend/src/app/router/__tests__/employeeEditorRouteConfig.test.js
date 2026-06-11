import fs from "fs";
import path from "path";

describe("Employee editor route config", () => {
  test("registers split identity and profile routes for employee and portal flows", () => {
    const routesPath = path.join(__dirname, "..", "employeeRoutes.jsx");
    const source = fs.readFileSync(routesPath, "utf8");

    expect(source).toContain('path="/employees/new/identity"');
    expect(source).toContain('path="/employees/:employeeId/identity/edit"');
    expect(source).toContain('path="/employees/:employeeId/profile/edit"');
    expect(source).toContain('path="/documents"');
    expect(source).toContain('path="/portal/employees/new/identity"');
    expect(source).toContain('path="/portal/documents"');
    expect(source).toContain('path="/portal/employees/:employeeId/identity/edit"');
    expect(source).toContain('path="/portal/employees/:employeeId/profile/edit"');
    expect(source).toContain("Permissions.IDENTITY_CREATE");
    expect(source).toContain("Permissions.IDENTITY_UPDATE_ALL");
    expect(source).toContain("GLOBAL_IDENTITY_DATA_ENTRY_AUTHORITIES");
    expect(source).toContain("requiredAuthorities={GLOBAL_IDENTITY_DATA_ENTRY_AUTHORITIES}");
    expect(source).toContain('requiredAuthorities={["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT", "SYSTEM_ADMIN"]}');
  });

  test("service book print view route accepts print permission", () => {
    const routesPath = path.join(__dirname, "..", "employeeRoutes.jsx");
    const source = fs.readFileSync(routesPath, "utf8");

    expect(source).toContain("SERVICE_BOOK_VIEW_ROUTE_PERMISSIONS");
    expect(source).toContain("Permissions.SERVICE_BOOK_READ_ALL");
    expect(source).toContain("Permissions.SERVICE_BOOK_PRINT");
    expect(source).toContain('path="/service-book/:employeeId"');
    expect(source).toContain("requiredPermissions={SERVICE_BOOK_VIEW_ROUTE_PERMISSIONS}");
  });

  test("service book opening routes are limited to global and dealing-assistant data entry authorities", () => {
    const routesPath = path.join(__dirname, "..", "employeeRoutes.jsx");
    const source = fs.readFileSync(routesPath, "utf8");

    expect(source).toContain("SERVICE_BOOK_OPENING_AUTHORITIES");
    expect(source).toContain('requiredAuthorities={SERVICE_BOOK_OPENING_AUTHORITIES}');
    expect(source).toContain('const SERVICE_BOOK_OPENING_AUTHORITIES = ["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"]');
  });

  test("registers split identity and profile routes for department flows", () => {
    const routesPath = path.join(__dirname, "..", "departmentRoutes.jsx");
    const source = fs.readFileSync(routesPath, "utf8");

    expect(source).toContain("DEPARTMENT_SCOPED_AUTHORITIES");
    expect(source).toContain('path="/department-portal/employees/new/identity"');
    expect(source).toContain('path="/department-portal/employee/:employeeId/identity/edit"');
    expect(source).toContain('path="/department-portal/employee/:employeeId/profile/edit"');
    expect(source).toContain('path="/department-portal/sanctioned-strength"');
    expect(source).toContain("Permissions.IDENTITY_CREATE");
    expect(source).toContain("Permissions.IDENTITY_UPDATE_ALL");
    expect(source).toContain("DEPARTMENT_IDENTITY_DATA_ENTRY_AUTHORITIES");
    expect(source).toContain("requiredAuthorities={DEPARTMENT_IDENTITY_DATA_ENTRY_AUTHORITIES}");
    expect(source).toContain("requiredAuthorities={DEPARTMENT_SCOPED_AUTHORITIES}");
    expect(source).not.toContain('path="/department-portal/change-requests"');
    expect(source).not.toContain('path="/department/change-requests"');
    expect(source).not.toContain('path="/department/employees/');
  });

  test("active employee/profile/department pages no longer import the combined wizard", () => {
    const frontendRoot = path.join(__dirname, "..", "..", "..", "..");
    const callerFiles = [
      "src/contexts/employee_master/pages/EmployeeDirectoryPage.jsx",
      "src/contexts/employee_master/pages/EmployeeFilePage.jsx",
      "src/contexts/organization_master/pages/DepartmentEmployeeFilePage.jsx",
      "src/contexts/employee_master/pages/EmployeeProfilePage.jsx",
      "src/contexts/organization_master/pages/DeptDirectoryPage.jsx",
      "src/contexts/organization_master/pages/DeptDashboardPage.jsx",
      "src/contexts/workflow/containers/WorkflowQueueScreen.jsx",
    ];

    callerFiles.forEach((relativePath) => {
      const source = fs.readFileSync(path.join(frontendRoot, relativePath), "utf8");
      expect(source).not.toMatch(/EmployeeWizardPage/);
      expect(source).not.toMatch(/<EmployeeWizard/);
    });
  });

  test("department employee file page uses department gateway instead of employee profile api", () => {
    const frontendRoot = path.join(__dirname, "..", "..", "..", "..");
    const source = fs.readFileSync(
      path.join(frontendRoot, "src/contexts/organization_master/pages/DepartmentEmployeeFilePage.jsx"),
      "utf8"
    );

    expect(source).toContain('from "@/contexts/organization_master/model/departmentProfileGateway"');
    expect(source).not.toContain('from "@/contexts/employee_master/api/employeeProfileApi"');
    expect(source).not.toContain("employeeProfileApi.");
    expect(source).toContain('from "@/contexts/organization_master/components/DepartmentEmployeeProfileSummary"');
    expect(source).not.toContain('from "@/contexts/employee_master/components/EmployeeProfileSummary"');
    expect(source).toContain('buildIdentityEditPath("department", employeeId)');
    expect(source).toContain('buildProfileEditPath("department", employeeId)');
    expect(source).toContain('<DepartmentEmployeeProfileSummary profile={profile} compact />');
    expect(source).not.toContain('<DepartmentEmployeeProfileSummary employee={profile} compact />');
  });

  test("legacy combined wizard source tree has been removed", () => {
    const frontendRoot = path.join(__dirname, "..", "..", "..", "..");
    const wizardRoot = path.join(frontendRoot, "src", "contexts", "employee_master", "wizard");
    const legacyPage = path.join(wizardRoot, "page", "EmployeeWizardPage.jsx");

    expect(fs.existsSync(legacyPage)).toBe(false);
  });
});
