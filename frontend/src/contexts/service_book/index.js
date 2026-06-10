import { lazy } from "react";

export const ServiceBookPage = lazy(() => import("./pages/ServiceBookPage"));
export const ServiceBookLandingPage = lazy(() => import("./pages/ServiceBookLandingPage"));
export const ServiceBookReadScreen = lazy(() => import("./containers/ServiceBookReadScreen"));
export { serviceBookAPI } from "./api/serviceBookApi";
export { serviceBookOpeningApi } from "./opening/api/serviceBookOpeningApi";
export { serviceRecordsApi } from "./records";
export {
  determineEmploymentType,
  isNonRegularEmploymentType,
  isServiceBookEligible,
} from "./services/serviceBookEligibility";
export { SERVICE_BOOK_STATUS, resolveServiceBookStatus } from "./services/serviceBookStatus";
export {
  OPENING_STATUS,
  getOpeningActionLabel,
  normalizeOpeningStatus,
} from "./opening/model/openingStatus";
export { getOpeningCta } from "./opening/services/openingDomainService";
