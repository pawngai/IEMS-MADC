import { lazy } from "react";
import { Navigate, Route, useParams, generatePath } from "react-router-dom";
import { GLOBAL_IDENTITY_DATA_ENTRY_AUTHORITIES } from "@/platform/permissions";
import { Permissions } from "@/platform/permissions";
import { ProtectedRoute } from "@/app/router/guards";

const ServiceBookPage = lazy(() => import("@/contexts/service_book/pages/ServiceBookPage"));
const ServiceBookLandingPage = lazy(() => import("@/contexts/service_book/pages/ServiceBookLandingPage"));
const ServiceBookOpeningPage = lazy(() => import("@/contexts/service_book/opening/pages/ServiceBookOpeningPage"));
const ServiceBookOpeningQueuePage = lazy(() => import("@/contexts/service_book/opening/pages/ServiceBookOpeningQueuePage"));
const ServiceBookRecordsPage = lazy(() => import("@/contexts/service_book/records/pages/ServiceBookRecordsPage"));
const ServiceBookRecordsLandingPage = lazy(() => import("@/contexts/service_book/records/pages/ServiceBookRecordsLandingPage"));
const DocumentManagementPage = lazy(() => import("@/contexts/documents/pages/DocumentManagementPage"));
const WorkQueue = lazy(() => import("@/contexts/workflow/pages/WorkflowQueuePage"));
const EmployeeDirectoryPage = lazy(() => import("@/contexts/employee_master/pages/EmployeeDirectoryPage"));
const EmployeeFile = lazy(() => import("@/contexts/employee_master/pages/EmployeeFilePage"));
const EmployeeIdentityEditorPage = lazy(() => import("@/contexts/employee_master/pages/EmployeeIdentityEditorPage"));
const RegularisationRecordPage = lazy(() => import("@/contexts/employee_master/pages/RegularisationRecordPage"));
const EmployeeProfileEditorPage = lazy(() => import("@/contexts/employee_master/pages/EmployeeProfileEditorPage"));

/** Redirect that preserves matched route params via react-router's generatePath. */
const ParamRedirect = ({ to }) => {
  const params = useParams();
  return <Navigate to={generatePath(to, params)} replace />;
};

const EMPLOYEE_DIR_PERMISSIONS = [
  Permissions.PROFILE_READ_ALL,
  Permissions.PROFILE_CREATE,
  Permissions.PROFILE_UPDATE_ALL,
  Permissions.PROFILE_UPDATE_OWN_LIMITED,
  Permissions.SERVICE_BOOK_READ_ALL,
  Permissions.SERVICE_BOOK_ENTRY_CREATE,
  Permissions.SERVICE_BOOK_ENTRY_VERIFY,
  Permissions.SERVICE_BOOK_ENTRY_APPROVE,
  Permissions.SERVICE_BOOK_ENTRY_ATTEST,
  Permissions.SERVICE_BOOK_OPENING_CREATE,
  Permissions.SERVICE_BOOK_OPENING_UPDATE,
  Permissions.SERVICE_BOOK_OPENING_SUBMIT,
  Permissions.SERVICE_BOOK_OPENING_VERIFY,
  Permissions.SERVICE_BOOK_OPENING_APPROVE,
  Permissions.AUDIT_READ_ALL,
];

const SERVICE_BOOK_OPENING_ROUTE_PERMISSIONS = [
  Permissions.SERVICE_BOOK_READ_ALL,
  Permissions.SERVICE_BOOK_OPENING_CREATE,
  Permissions.SERVICE_BOOK_OPENING_UPDATE,
  Permissions.SERVICE_BOOK_OPENING_SUBMIT,
  Permissions.SERVICE_BOOK_OPENING_VERIFY,
  Permissions.SERVICE_BOOK_OPENING_APPROVE,
];

const SERVICE_BOOK_OPENING_AUTHORITIES = ["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"];

const SERVICE_BOOK_VIEW_ROUTE_PERMISSIONS = [
  Permissions.SERVICE_BOOK_READ_ALL,
  Permissions.SERVICE_BOOK_PRINT,
];

const IDENTITY_EDITOR_PERMISSIONS = [
  Permissions.IDENTITY_READ_ALL,
  Permissions.IDENTITY_CREATE,
  Permissions.IDENTITY_UPDATE_ALL,
];

export const EmployeeRoutes = () => (
  <>
    {/* Canonical routes */}
    <Route path="/work" element={<ProtectedRoute><WorkQueue /></ProtectedRoute>} />
    <Route path="/employees" element={<ProtectedRoute requiredPermissions={EMPLOYEE_DIR_PERMISSIONS}><EmployeeDirectoryPage /></ProtectedRoute>} />
    <Route path="/employees/new/identity" element={<ProtectedRoute requiredPermissions={IDENTITY_EDITOR_PERMISSIONS} requiredAuthorities={GLOBAL_IDENTITY_DATA_ENTRY_AUTHORITIES}><EmployeeIdentityEditorPage /></ProtectedRoute>} />
    <Route path="/employees/:employeeId" element={<ProtectedRoute requiredPermissions={EMPLOYEE_DIR_PERMISSIONS}><EmployeeFile /></ProtectedRoute>} />
    <Route path="/employees/:employeeId/identity/edit" element={<ProtectedRoute requiredPermissions={IDENTITY_EDITOR_PERMISSIONS} requiredAuthorities={GLOBAL_IDENTITY_DATA_ENTRY_AUTHORITIES}><EmployeeIdentityEditorPage /></ProtectedRoute>} />
    <Route path="/employees/:employeeId/profile/edit" element={<ProtectedRoute requiredPermissions={EMPLOYEE_DIR_PERMISSIONS}><EmployeeProfileEditorPage /></ProtectedRoute>} />
    <Route path="/employees/:employeeId/regularisation" element={<ProtectedRoute requiredPermissions={EMPLOYEE_DIR_PERMISSIONS}><RegularisationRecordPage /></ProtectedRoute>} />
    <Route path="/documents" element={<ProtectedRoute requiredAuthorities={["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT", "SYSTEM_ADMIN"]}><DocumentManagementPage /></ProtectedRoute>} />
    <Route path="/service-book" element={<ProtectedRoute requiredPermissions={[Permissions.SERVICE_BOOK_READ_ALL]} moduleId="service_book"><ServiceBookLandingPage /></ProtectedRoute>} />
    <Route path="/service-book/opening" element={<ProtectedRoute requiredPermissions={SERVICE_BOOK_OPENING_ROUTE_PERMISSIONS} requiredAuthorities={SERVICE_BOOK_OPENING_AUTHORITIES} moduleId="service_book"><ServiceBookOpeningQueuePage /></ProtectedRoute>} />
    <Route path="/service-book/opening/:employeeId" element={<ProtectedRoute requiredPermissions={SERVICE_BOOK_OPENING_ROUTE_PERMISSIONS} requiredAuthorities={SERVICE_BOOK_OPENING_AUTHORITIES} moduleId="service_book"><ServiceBookOpeningPage /></ProtectedRoute>} />
    <Route path="/service-book/records" element={<ProtectedRoute requiredPermissions={[Permissions.SERVICE_BOOK_READ_ALL]} moduleId="service_book"><ServiceBookRecordsLandingPage /></ProtectedRoute>} />
    <Route path="/service-book/records/:employeeId" element={<ProtectedRoute requiredPermissions={[Permissions.SERVICE_BOOK_READ_ALL]} moduleId="service_book"><ServiceBookRecordsPage /></ProtectedRoute>} />
    <Route path="/service-book/:employeeId" element={<ProtectedRoute requiredPermissions={SERVICE_BOOK_VIEW_ROUTE_PERMISSIONS} moduleId="service_book"><ServiceBookPage /></ProtectedRoute>} />

    {/*
      Allowlisted /portal/* compatibility scope: active operations portal scope used
      by the OPS route table in src/shared/lib/routes.js. Each /portal/* path here
      is a thin alias for a canonical path and is documented in
      frontend/ROUTE_ALIAS_ALLOWLIST.md.
    */}
    <Route path="/portal/work" element={<Navigate to="/work" replace />} />
    <Route path="/portal/employees" element={<Navigate to="/employees" replace />} />
    <Route path="/portal/documents" element={<Navigate to="/documents" replace />} />
    <Route path="/portal/employees/new/identity" element={<Navigate to="/employees/new/identity" replace />} />
    <Route path="/portal/employees/:employeeId" element={<ParamRedirect to="/employees/:employeeId" />} />
    <Route path="/portal/employees/:employeeId/identity/edit" element={<ParamRedirect to="/employees/:employeeId/identity/edit" />} />
    <Route path="/portal/employees/:employeeId/profile/edit" element={<ParamRedirect to="/employees/:employeeId/profile/edit" />} />
    <Route path="/portal/employees/:employeeId/regularisation" element={<ParamRedirect to="/employees/:employeeId/regularisation" />} />
    <Route path="/portal/service-book" element={<Navigate to="/service-book" replace />} />
    <Route path="/portal/service-book/opening" element={<Navigate to="/service-book/opening" replace />} />
    <Route path="/portal/service-book/opening/:employeeId" element={<ParamRedirect to="/service-book/opening/:employeeId" />} />
    <Route path="/portal/service-book/:employeeId" element={<ParamRedirect to="/service-book/:employeeId" />} />
    <Route path="/portal/service-book/records" element={<Navigate to="/service-book/records" replace />} />
    <Route path="/portal/service-book/records/:employeeId" element={<ParamRedirect to="/service-book/records/:employeeId" />} />
  </>
);
