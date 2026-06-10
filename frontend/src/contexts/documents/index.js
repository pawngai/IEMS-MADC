import { lazy } from "react";

export const DocumentManagementPage = lazy(() => import("./pages/DocumentManagementPage"));
export { documentsAPI, uploadAPI } from "./api/documentsApi";
export { getDocumentFilterOptions, useDocumentsBrowser } from "./hooks/useDocumentsBrowser";
