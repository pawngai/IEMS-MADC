import { lazy } from "react";

export const ServiceBookRecordsPage = lazy(() => import("./pages/ServiceBookRecordsPage"));
export const ServiceBookRecordsLandingPage = lazy(() => import("./pages/ServiceBookRecordsLandingPage"));
export { serviceBookRecordsAPI } from "./api/serviceBookRecordsApi";
export { serviceRecordsApi } from "./api/serviceRecordsApi";
