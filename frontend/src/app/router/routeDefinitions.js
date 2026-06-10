import { Permissions } from "@/platform/permissions";

export const routeDefinitions = [
  { path: "/employees", portal: "admin", context: "employee_identity", permissions: [Permissions.PROFILE_READ_ALL], breadcrumb: "Employees" },
  { path: "/employees/:employeeId", portal: "admin", context: "employee_profile", permissions: [Permissions.PROFILE_READ_ALL], breadcrumb: "Employee File" },
  { path: "/service-book", portal: "admin", context: "service_book", permissions: [Permissions.SERVICE_BOOK_READ_ALL, Permissions.SERVICE_BOOK_PRINT], breadcrumb: "Service Book" },
  { path: "/service-book/opening", portal: "admin", context: "service_book", permissions: [Permissions.SERVICE_BOOK_OPENING_CREATE, Permissions.SERVICE_BOOK_OPENING_UPDATE], breadcrumb: "Service Book Opening" },
  { path: "/service-book/records", portal: "admin", context: "service_book", permissions: [Permissions.SERVICE_BOOK_READ_ALL], breadcrumb: "Service Book Records" },
  { path: "/work", portal: "approval_authority", context: "workflow", permissions: [], breadcrumb: "Workflow" },
  { path: "/ess", portal: "ess", context: "ess", permissions: [], breadcrumb: "ESS" },
  { path: "/department", portal: "department", context: "department", permissions: [], breadcrumb: "Department" },
  { path: "/admin", portal: "admin", context: "admin", permissions: [Permissions.USER_MANAGEMENT, Permissions.SYSTEM_CONFIG], breadcrumb: "Admin" },
];

export const routeDefinitionByPath = new Map(routeDefinitions.map((route) => [route.path, route]));
