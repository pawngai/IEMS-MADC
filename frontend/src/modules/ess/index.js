import { lazy } from "react";

export { essAPI } from "./api/essApi";
export {
  ESS_DOCUMENTS_REQUIRED_PERMISSIONS,
  hasEssEmployeeIdentity,
  assertEssPortalSession,
  assertEssSelfScope,
  canShowEssServiceBook,
  canAccessEssDocuments,
} from "./services/essDomainService";
export { normalizeEssProfile, getMyProfileAuditTrail } from "./model/essProfileGateway";
export const EssDashboardPage = lazy(() => import("./pages/EssDashboardPage"));
export const EssDocumentsPage = lazy(() => import("./pages/EssDocumentsPage"));
