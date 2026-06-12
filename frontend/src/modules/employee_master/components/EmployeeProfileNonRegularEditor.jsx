import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { FileText, Loader2, Upload, X } from "lucide-react";
import {
  DOCUMENT_ACCEPT,
  EmploymentTypeRadioField,
  SearchableSelectField,
  SelectField,
  TextAreaField,
  TextField,
  WAGE_RATE_UNIT_OPTIONS,
  getDocumentRefId,
} from "@/modules/employee_master/components/EmployeeProfileExtensionEditor.support";

const getDocumentHref = (document) => {
  const path = document?.storage_path || document?.file_url || document?.url;
  if (!path) return null;
  return path.startsWith("http") ? path : `/api/documents/files/${encodeURIComponent(path)}`;
};

const EmployeeProfileNonRegularEditor = ({
  formData,
  errors,
  setFormData,
  setErrors,
  updateField,
  nonRegularEmploymentOptions,
  selectedEmploymentType,
  departmentOptions,
  designationOptions,
  payLevelOptions,
  isCoTerminus,
  showWages,
  showFixed,
  showRemunerationTypeSelector,
  showWageInputs,
  showFixedInputs,
  remunerationOptions,
  documentRecommendations,
  attachedDocumentCounts,
  documentPurposeOptions,
  selectedDocumentPurpose,
  setSelectedDocumentPurpose,
  resolveDocumentPurpose,
  uploadingDocument,
  handleUploadDocument,
  attachedDocuments,
  handleRemoveAttachedDocument,
}) => (
  <>
    <Card>
      <CardHeader>
        <CardTitle>Employment Details</CardTitle>
        <CardDescription>Capture non-regular engagement details in the same profile-extension flow used for regular employees.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <EmploymentTypeRadioField
          label="Employment Type"
          value={formData.employment_type}
          onChange={(value) => {
            setErrors({});
            setFormData((current) => ({
              ...current,
              employment_type: value,
              remuneration_type: "",
              daily_wage_rate: "",
              wage_rate_unit: "PER_DAY",
              fixed_monthly_amount: "",
              pay_level: "",
              basic_pay: "",
            }));
          }}
          options={nonRegularEmploymentOptions}
          error={errors.employment_type}
          helper="Select the non-regular employment type to load its posting, remuneration, and document fields."
        />

        {formData.employment_type ? (
          <>
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Posting</p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <SearchableSelectField
                  id="current_department_id"
                  label="Department"
                  value={formData.current_department_id}
                  onChange={updateField}
                  options={departmentOptions}
                  error={errors.current_department_id}
                  placeholder="Select department"
                />
                <SearchableSelectField
                  id="current_designation_id"
                  label="Designation"
                  value={formData.current_designation_id}
                  onChange={updateField}
                  options={designationOptions}
                  error={errors.current_designation_id}
                  placeholder="Select designation"
                />
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Engagement Order</p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {selectedEmploymentType?.requires_engagement_order && (
                  <>
                    <TextField
                      id="engagement_order_no"
                      label="Engagement Order No"
                      value={formData.engagement_order_no}
                      onChange={updateField}
                      error={errors.engagement_order_no}
                      helper="As printed on the office order"
                    />
                    <TextField
                      id="engagement_order_date"
                      label="Engagement Order Date"
                      type="date"
                      value={formData.engagement_order_date}
                      onChange={updateField}
                    />
                  </>
                )}
                <TextField
                  id="date_of_initial_engagement"
                  label="Engagement Start Date"
                  type="date"
                  value={formData.date_of_initial_engagement}
                  onChange={updateField}
                  error={errors.date_of_initial_engagement}
                />
                {selectedEmploymentType?.requires_contract_period && (
                  <TextField
                    id="engagement_end_date"
                    label="Engagement End Date"
                    type="date"
                    value={formData.engagement_end_date}
                    onChange={updateField}
                    error={errors.engagement_end_date}
                  />
                )}
              </div>
            </div>

            {(isCoTerminus || showWages || showFixed) && (
              <div className="space-y-3">
                <p className="text-xs font-bold uppercase tracking-widest text-slate-500">{isCoTerminus ? "Pay" : "Remuneration"}</p>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {isCoTerminus && (
                    <>
                      <SearchableSelectField
                        id="pay_level"
                        label="Pay Level"
                        value={formData.pay_level}
                        onChange={updateField}
                        options={payLevelOptions}
                        error={errors.pay_level}
                        placeholder="Select pay level"
                      />
                      <TextField
                        id="basic_pay"
                        label="Basic Pay"
                        type="number"
                        min={0}
                        value={formData.basic_pay}
                        onChange={updateField}
                        error={errors.basic_pay}
                      />
                    </>
                  )}
                  {showRemunerationTypeSelector && (
                    <SelectField
                      id="remuneration_type"
                      label="Remuneration Type"
                      value={formData.remuneration_type}
                      onChange={updateField}
                      options={remunerationOptions}
                      error={errors.remuneration_type}
                      placeholder="Select remuneration type"
                    />
                  )}
                  {showWageInputs && (
                    <>
                      <TextField
                        id="daily_wage_rate"
                        label="Wage Rate"
                        type="number"
                        min={0}
                        value={formData.daily_wage_rate}
                        onChange={updateField}
                        error={errors.daily_wage_rate}
                      />
                      <SelectField
                        id="wage_rate_unit"
                        label="Wage Rate Unit"
                        value={formData.wage_rate_unit}
                        onChange={updateField}
                        options={WAGE_RATE_UNIT_OPTIONS}
                        error={errors.wage_rate_unit}
                        placeholder="Select wage rate unit"
                      />
                    </>
                  )}
                  {showFixedInputs && (
                    <TextField
                      id="fixed_monthly_amount"
                      label="Monthly Remuneration"
                      type="number"
                      min={0}
                      value={formData.fixed_monthly_amount}
                      onChange={updateField}
                      error={errors.fixed_monthly_amount}
                    />
                  )}
                </div>
              </div>
            )}

            <TextAreaField
              id="engagement_remarks"
              label="Notes"
              value={formData.engagement_remarks}
              onChange={updateField}
              error={errors.engagement_remarks}
              placeholder="Optional remarks for this engagement"
            />
          </>
        ) : (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
            Select a non-regular employment type to load the relevant profile-extension fields.
          </div>
        )}
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Supporting Documents</CardTitle>
        <CardDescription>Attach the documents that belong with this non-regular employee profile.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {formData.employment_type ? (
          <>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {documentRecommendations.map((item) => {
                const count = attachedDocumentCounts[item.key] || 0;
                return (
                  <div key={item.key} className="rounded-lg border border-slate-200 bg-slate-50/70 px-4 py-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-slate-800">{item.label}</p>
                        <p className="mt-1 text-xs text-slate-500">{item.helper}</p>
                      </div>
                      <Badge variant={count ? "default" : "outline"}>{count ? `${count} attached` : "Recommended"}</Badge>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,260px)_1fr]">
              <SelectField
                id="document-purpose"
                label="Document For"
                value={selectedDocumentPurpose}
                onChange={(_, nextValue) => setSelectedDocumentPurpose(nextValue)}
                options={documentPurposeOptions}
                placeholder="Select document purpose"
              />
              <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-600">
                <p className="font-medium text-slate-800">Current purpose</p>
                <p className="mt-1">{resolveDocumentPurpose().label}</p>
                <p className="mt-2 text-xs text-slate-500">{resolveDocumentPurpose().helper}</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <label className={`inline-flex cursor-pointer items-center gap-2 rounded-md border border-dashed px-4 py-2 text-sm transition-colors hover:bg-slate-50 ${uploadingDocument ? "pointer-events-none opacity-60" : ""}`}>
                {uploadingDocument ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                {uploadingDocument ? "Uploading..." : "Upload file"}
                <input
                  type="file"
                  className="hidden"
                  accept={DOCUMENT_ACCEPT}
                  disabled={uploadingDocument}
                  onChange={async (event) => {
                    const file = event.target.files?.[0];
                    event.target.value = "";
                    if (!file) return;
                    await handleUploadDocument(file);
                  }}
                />
              </label>
            </div>

            {attachedDocuments.length > 0 ? (
              <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50/70 p-3">
                {attachedDocuments.map((document, index) => {
                  const documentId = getDocumentRefId(document) || `attached-${index}`;
                  const href = getDocumentHref(document);
                  return (
                    <div key={`${documentId}-${index}`} className="flex items-start justify-between gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 shrink-0 text-slate-500" />
                          <span className="truncate font-medium text-slate-700">{document.original_name || document.filename || documentId}</span>
                        </div>
                        <p className="mt-1 truncate text-xs text-slate-400">{documentId}</p>
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {document.purpose_label ? <Badge variant="outline">{document.purpose_label}</Badge> : null}
                          {document.document_type ? <Badge variant="secondary">{document.document_type}</Badge> : null}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {href ? (
                          <a href={href} target="_blank" rel="noopener noreferrer" className="text-sm text-slate-600 underline underline-offset-2">
                            Open
                          </a>
                        ) : null}
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-slate-500 hover:text-rose-600"
                          onClick={() => handleRemoveAttachedDocument(documentId)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="rounded-md border border-dashed border-slate-300 px-4 py-6 text-sm text-slate-500">
                No documents attached yet.
              </div>
            )}
          </>
        ) : (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
            Select an employment type first so the supporting document guidance can be tailored to that profile.
          </div>
        )}
      </CardContent>
    </Card>
  </>
);

export default EmployeeProfileNonRegularEditor;
