# Large Files Inventory (> 300 lines)

Generated: 2026-06-11 (Phase 0)

Split target: files > 300 lines, using the pattern
**page (route shell) → screen/container (orchestration) → hooks (API/state/
actions) → model (validation/labels/mapping/command builders) → components
(presentational)**.

## Frontend priority list (from refactor spec)

| Lines | File | Split status |
|---|---|---|
| 1044 | contexts/leave_attendance/pages/LeaveDashboardPage.jsx | TODO (P8, priority 1) |
| 997 | contexts/service_book/records/components/RecordServiceBookRecordDialog.jsx | TODO (P8, priority 2) |
| 911 | contexts/employee_master/pages/EmployeeDirectoryPage.jsx | TODO (P8, priority 3) |
| 888 | contexts/employee_master/components/EmployeeProfileExtensionEditor.jsx | TODO (P8, priority 4) |
| 956 | contexts/reporting_analytics/components/AnalyticsDashboardSections.jsx | TODO (P8, priority 5) |
| 1012 | contexts/change_requests/containers/EssChangeRequestsScreen.jsx | TODO (P8, priority 6) |

## Frontend — full list > 300 lines

```
1044  contexts/leave_attendance/pages/LeaveDashboardPage.jsx
1012  contexts/change_requests/containers/EssChangeRequestsScreen.jsx
 997  contexts/service_book/records/components/RecordServiceBookRecordDialog.jsx
 956  contexts/reporting_analytics/components/AnalyticsDashboardSections.jsx
 911  contexts/employee_master/pages/EmployeeDirectoryPage.jsx
 888  contexts/employee_master/components/EmployeeProfileExtensionEditor.jsx
 817  contexts/seniority/components/SeniorityListsTab.jsx
 699  contexts/employee_master/components/EmployeeProfileSummary.jsx
 675  contexts/leave_attendance/pages/EssLeavePage.jsx
 673  contexts/ess/pages/EssDashboardPage.jsx
 671  contexts/service_book/records/model/recordServiceBookRecordDialogModel.js
 624  contexts/employee_master/components/EmployeeProfileExtensionEditor.support.jsx
 618  contexts/workflow/containers/WorkflowQueueScreen.jsx
 600  contexts/workflow/components/WorkflowDetailPanel.jsx
 554  contexts/employee_master/hooks/useEmployeeDirectory.js
 524  contexts/organization_master/pages/DeptSanctionedStrengthPage.jsx
 520  app/layout/Layout.jsx
 518  contexts/applications/pages/GlobalPortalDashboardPage.jsx
 508  contexts/reporting_analytics/pages/AnalyticsDashboardPage.jsx
 506  contexts/ess/pages/EssDocumentsPage.jsx
 492  contexts/admin/model/policyMasterForms.js
 475  contexts/reporting_analytics/components/analyticsDashboardPanels.jsx
 441  contexts/service_book/services/projectionNormalizer.js
 437  contexts/service_book/records/components/CorrectServiceBookRecordDialog.jsx
 421  contexts/employee_master/pages/EmployeeFilePage.jsx
 404  contexts/organization_master/hooks/useDepartmentEmployeeDirectory.js
 398  contexts/reporting_analytics/model/analyticsDashboardModel.js
 395  contexts/organization_master/pages/DeptDashboardPage.jsx
 375  contexts/documents/pages/DocumentManagementPage.jsx
 368  contexts/service_book/records/components/ServiceRecordCard.jsx
 366  contexts/employee_master/pages/EmployeeIdentityEditorPage.jsx
 361  contexts/service_book/opening/components/OpeningPartFormFields.jsx
 360  contexts/change_requests/hooks/useChangeRequestForm.js
 352  contexts/admin/components/MasterDialogs.jsx
 339  contexts/service_book/records/model/serviceBookRecordsSchemaFallback.js
 339  contexts/employee_master/components/ProfileCompletionCard.jsx
 323  contexts/admin/components/RoleManagementTab.jsx
 320  contexts/admin/hooks/usePolicyMasterAdmin.js
 308  contexts/service_book/records/components/AttachDocumentDialog.jsx
 306  contexts/organization_master/components/DirectoryFilterBar.jsx
 305  contexts/employee_master/pages/RegularisationRecordPage.jsx
 303  contexts/change_requests/model/changeRequestFieldSchema.js
```

Note: many of these files move during context relocation (Phase 1–6); split work
(Phase 8) happens **after** the file lands in its final context to avoid
re-splitting moved code. "Where practical" — generated/schema-fallback files
(e.g. `serviceBookRecordsSchemaFallback.js`) may be left intact.

## Backend — informational (> 300 lines, top 30)

Backend split is not a spec priority but recorded for awareness:
```
965  app_platform/forms/infrastructure/dynamic_forms_catalog.py
804  app_platform/domain_separation/schema_definitions.py
761  contexts/reporting_analytics/queries/analytics_queries.py
753  contexts/system_admin/api/router.py
749  contexts/identity_access/identity/infrastructure/user_management_service.py
744  app_platform/reference_data/infrastructure/employee_form_catalog.py
730  app_platform/db/runtime.py
703  contexts/documents/repository/metadata_repository.py
670  contexts/identity_access/rbac/domain/policy_engine.py
...
```
