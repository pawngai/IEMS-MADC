import { lazy } from "react";

export const EssDashboardPage = lazy(() => import("./pages/EssDashboardPage"));
export const EssDocumentsPage = lazy(() => import("./pages/EssDocumentsPage"));
export { essAPI } from "./api/essApi";
