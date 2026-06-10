import { useEffect, useMemo, useState } from "react";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Checkbox } from "@/shared/ui/checkbox";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { documentsAPI } from "@/contexts/documents";
import { mastersAPI } from "@/contexts/masters";
import { employeeProfileApi } from "@/contexts/employee_profile/api/employeeProfileApi";
import { buildPayLevelOptions } from "@/contexts/employee_profile/model/profileEditorOptions";
import { TYPE_SPECIFIC_FIELDS } from "@/contexts/employee_profile/model/profileEditorConstants";
import { resolveProfileSubmitError } from "@/contexts/employee_profile/model/profileSubmitErrors";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { toast } from "sonner";
import { AlertTriangle, Camera, Loader2, PenLine, Save, Upload } from "lucide-react";
import {
  ADDRESS_FIELD_PAIRS,
  BLOOD_GROUP_OPTIONS,
  DEFAULT_DOCUMENT_PURPOSE,
  DOCUMENT_ACCEPT,
  DOCUMENT_REQUIREMENTS,
  DOCUMENT_SOURCE_CONTEXT,
  EmploymentTypeRadioField,
  FieldError,
  FIXED_ENGAGEMENT_DOCUMENT_TYPES,
  LIEN_STATUS_OPTIONS,
  LIST_FIELDS,
  MARITAL_STATUS_OPTIONS,
  MediaUploadField,
  NUMBER_FIELDS,
  RENEWAL_OPTIONS,
  REMUNERATION_TYPE_OPTIONS,
  SelectField,
  SearchableSelectField,
  TextAreaField,
  TextField,
  WAGE_RATE_UNIT_OPTIONS,
  buildAdminPayload,
  buildEssPayload,
  createEmptyForm,
  getDocumentRecommendations,
  getDocumentRefId,
  isModernNonRegularType,
  mapProfileToForm,
  normalizeCode,
  renderTypeSpecificField,
  resolveMediaUrl,
  titleCase,
  toOptions,
  validateForm,
} from "@/contexts/employee_profile/components/EmployeeProfileExtensionEditor.support";

const getDocumentHref = (document) => {
  const filename = String(document?.filename || "").trim();
  if (filename) return documentsAPI.getFileUrl(filename);
  return String(document?.url || "").trim();
};

const EmployeeProfileExtensionEditor = ({
  profile,
  essMode = false,
  nonRegular = false,
  submitAction,
  onCancel,
  onSuccess,
}) => {
  const [formData, setFormData] = useState(() => mapProfileToForm(profile));
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [uploadingSignature, setUploadingSignature] = useState(false);
  const [uploadingDocument, setUploadingDocument] = useState(false);
  const [selectedDocumentPurpose, setSelectedDocumentPurpose] = useState(DEFAULT_DOCUMENT_PURPOSE);
  const [attachedDocuments, setAttachedDocuments] = useState([]);
  const [masters, setMasters] = useState({ employmentTypes: [], departments: [], designations: [], payLevels: [] });

  const employmentType = useMemo(
    () => normalizeCode(formData.employment_type || profile?.employment_type || profile?.employment_type_code),
    [formData.employment_type, profile?.employment_type, profile?.employment_type_code]
  );

  const selectedEmploymentType = useMemo(
    () => masters.employmentTypes.find((item) => normalizeCode(item?.employment_type_code || item?.code || item?.value || item?.id) === employmentType) || null,
    [employmentType, masters.employmentTypes]
  );

  const showModernNonRegularEditor = useMemo(
    () => !essMode && (
      nonRegular
      || isModernNonRegularType(employmentType)
      || Boolean(selectedEmploymentType && (selectedEmploymentType.employment_class === "NON_REGULAR" || selectedEmploymentType.eligible_for_service_book === false))
    ),
    [employmentType, essMode, nonRegular, selectedEmploymentType]
  );

  const typeSpecificFields = useMemo(
    () => (essMode || showModernNonRegularEditor ? [] : TYPE_SPECIFIC_FIELDS[employmentType] || []),
    [employmentType, essMode, showModernNonRegularEditor]
  );

  const isRegular = employmentType === "REGULAR";
  const nonRegularEmploymentOptions = useMemo(
    () => toOptions(
      masters.employmentTypes.filter((item) => item?.employment_class === "NON_REGULAR" || item?.eligible_for_service_book === false),
      ["employment_type_code", "code", "value", "id"],
      ["name", "label", "description"]
    ),
    [masters.employmentTypes]
  );
  const regularEmploymentOptions = useMemo(
    () => toOptions(
      masters.employmentTypes.filter((item) => {
        const code = normalizeCode(item?.employment_type_code || item?.code || item?.value || item?.id);
        return code === "REGULAR" || item?.employment_class === "REGULAR";
      }),
      ["employment_type_code", "code", "value", "id"],
      ["name", "label", "description"]
    ),
    [masters.employmentTypes]
  );
  const effectiveRegularEmploymentOptions = useMemo(
    () => (regularEmploymentOptions.length
      ? regularEmploymentOptions
      : [{ value: "REGULAR", label: "Regular", search: "Regular REGULAR" }]),
    [regularEmploymentOptions]
  );
  const departmentOptions = useMemo(
    () => toOptions(masters.departments, ["department_id", "code", "value", "id"], ["department_name", "name", "label", "description"]),
    [masters.departments]
  );
  const designationOptions = useMemo(
    () => toOptions(masters.designations, ["designation_id", "code", "value", "id"], ["designation_name", "name", "label", "description"]),
    [masters.designations]
  );
  const payLevelOptions = useMemo(() => buildPayLevelOptions(masters.payLevels), [masters.payLevels]);
  const documentRecommendations = useMemo(() => getDocumentRecommendations(selectedEmploymentType), [selectedEmploymentType]);
  const documentPurposeOptions = useMemo(() => {
    const recommended = documentRecommendations.map((item) => ({ value: item.key, label: item.label }));
    return [...recommended, { value: DEFAULT_DOCUMENT_PURPOSE, label: DOCUMENT_REQUIREMENTS[DEFAULT_DOCUMENT_PURPOSE].label }];
  }, [documentRecommendations]);
  const attachedDocumentCounts = useMemo(
    () => attachedDocuments.reduce((acc, document) => {
      const purposeKey = String(document?.purpose_key || "").trim();
      if (!purposeKey) return acc;
      acc[purposeKey] = (acc[purposeKey] || 0) + 1;
      return acc;
    }, {}),
    [attachedDocuments]
  );

  const showWages = selectedEmploymentType ? selectedEmploymentType.eligible_for_wages !== false : true;
  const showFixed = selectedEmploymentType ? selectedEmploymentType.eligible_for_fixed_remuneration !== false : true;
  const isCoTerminus = employmentType === "CO_TERMINUS";
  const remunerationOptions = REMUNERATION_TYPE_OPTIONS.filter((option) => {
    if (option.value === "DAILY_WAGE") return showWages;
    if (option.value === "FIXED_MONTHLY") return showFixed && !isCoTerminus;
    return false;
  });
  const showRemunerationTypeSelector = !isCoTerminus && remunerationOptions.length > 1;
  const showWageInputs = showWages && (showRemunerationTypeSelector ? formData.remuneration_type === "DAILY_WAGE" : remunerationOptions[0]?.value === "DAILY_WAGE");
  const showFixedInputs = showFixed && !isCoTerminus && (showRemunerationTypeSelector ? formData.remuneration_type === "FIXED_MONTHLY" : remunerationOptions[0]?.value === "FIXED_MONTHLY");
  const requiredModernFields = useMemo(() => {
    if (!showModernNonRegularEditor) return null;
    const fields = new Set(["employment_type", "current_department_id", "current_designation_id", "date_of_initial_engagement"]);
    if (selectedEmploymentType?.requires_engagement_order) fields.add("engagement_order_no");
    if (selectedEmploymentType?.requires_contract_period) fields.add("engagement_end_date");
    if (isCoTerminus) {
      fields.add("pay_level");
      fields.add("basic_pay");
    } else if (showRemunerationTypeSelector) {
      fields.add("remuneration_type");
    }
    if (showWageInputs) fields.add("daily_wage_rate");
    if (showFixedInputs) fields.add("fixed_monthly_amount");
    return fields;
  }, [isCoTerminus, selectedEmploymentType, showFixedInputs, showModernNonRegularEditor, showRemunerationTypeSelector, showWageInputs]);

  const hasPermanentAddressValue = useMemo(
    () => ADDRESS_FIELD_PAIRS.some(([sourceField]) => Boolean(formData[sourceField]?.trim?.() || formData[sourceField])),
    [formData]
  );

  const areAddressesSynced = useMemo(
    () => ADDRESS_FIELD_PAIRS.every(([sourceField, targetField]) => formData[sourceField] === formData[targetField]),
    [formData]
  );

  useEffect(() => {
    const nextForm = mapProfileToForm(profile);
    setFormData(nextForm);
    setAttachedDocuments((nextForm.document_ids || []).map((documentId) => ({ document_id: documentId })));
    setErrors({});
  }, [profile]);

  useEffect(() => {
    let cancelled = false;

    const loadMasters = async () => {
      try {
        const [employmentTypesRes, departmentsRes, designationsRes, payLevelsRes] = await Promise.all([
          mastersAPI.getEmploymentTypes().catch(() => ({ data: [] })),
          mastersAPI.getDepartments().catch(() => ({ data: [] })),
          mastersAPI.getDesignations().catch(() => ({ data: [] })),
          mastersAPI.getPayLevels().catch(() => ({ data: [] })),
        ]);

        if (cancelled) return;
        setMasters({
          employmentTypes: Array.isArray(employmentTypesRes.data) ? employmentTypesRes.data : [],
          departments: Array.isArray(departmentsRes.data) ? departmentsRes.data : [],
          designations: Array.isArray(designationsRes.data) ? designationsRes.data : [],
          payLevels: Array.isArray(payLevelsRes.data) ? payLevelsRes.data : [],
        });
      } catch (error) {
        if (!cancelled) {
          console.error("Failed to load profile editor masters:", error);
        }
      }
    };

    loadMasters();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const allowedPurposes = new Set(documentPurposeOptions.map((option) => option.value));
    if (!allowedPurposes.has(selectedDocumentPurpose)) {
      setSelectedDocumentPurpose(documentPurposeOptions[0]?.value || DEFAULT_DOCUMENT_PURPOSE);
    }
  }, [documentPurposeOptions, selectedDocumentPurpose]);

  useEffect(() => {
    if (!showModernNonRegularEditor || !employmentType) return;
    if (!selectedEmploymentType) return;
    setFormData((current) => {
      const next = { ...current };
      let changed = false;
      const allowedRemunerationTypes = remunerationOptions.map((option) => option.value);
      const preferredRemunerationType = isCoTerminus ? "" : showWages ? "DAILY_WAGE" : showFixed ? "FIXED_MONTHLY" : "";

      if (!selectedEmploymentType?.requires_engagement_order && (current.engagement_order_no || current.engagement_order_date)) {
        next.engagement_order_no = "";
        next.engagement_order_date = "";
        changed = true;
      }
      if (!selectedEmploymentType?.requires_contract_period && current.engagement_end_date) {
        next.engagement_end_date = "";
        changed = true;
      }
      if (!showWages && (current.daily_wage_rate || current.wage_rate_unit !== "PER_DAY")) {
        next.daily_wage_rate = "";
        next.wage_rate_unit = "PER_DAY";
        changed = true;
      }
      if (!showFixed && current.fixed_monthly_amount) {
        next.fixed_monthly_amount = "";
        changed = true;
      }
      if (isCoTerminus && current.remuneration_type) {
        next.remuneration_type = "";
        changed = true;
      }
      if (!isCoTerminus && (current.basic_pay || current.pay_level)) {
        next.basic_pay = "";
        next.pay_level = "";
        changed = true;
      }
      if (preferredRemunerationType && allowedRemunerationTypes.includes(preferredRemunerationType) && current.remuneration_type !== preferredRemunerationType) {
        next.remuneration_type = preferredRemunerationType;
        changed = true;
      } else if (!isCoTerminus && current.remuneration_type && !allowedRemunerationTypes.includes(current.remuneration_type)) {
        next.remuneration_type = "";
        changed = true;
      }

      return changed ? next : current;
    });
  }, [employmentType, isCoTerminus, remunerationOptions, selectedEmploymentType, showFixed, showModernNonRegularEditor, showWages]);

  useEffect(() => {
    if (essMode || showModernNonRegularEditor || employmentType || effectiveRegularEmploymentOptions.length !== 1) return;
    setFormData((current) => {
      if (current.employment_type) return current;
      return {
        ...current,
        employment_type: effectiveRegularEmploymentOptions[0].value,
      };
    });
  }, [effectiveRegularEmploymentOptions, employmentType, essMode, showModernNonRegularEditor]);

  const updateField = (field, value) => {
    setFormData((current) => ({ ...current, [field]: value }));
    setErrors((current) => {
      if (!current[field]) return current;
      const next = { ...current };
      delete next[field];
      return next;
    });
  };

  const syncAttachedDocuments = (nextDocuments) => {
    setAttachedDocuments(nextDocuments);
    updateField("document_ids", nextDocuments.map((document) => getDocumentRefId(document)).filter(Boolean));
  };

  const resolveDocumentPurpose = () => DOCUMENT_REQUIREMENTS[selectedDocumentPurpose] || DOCUMENT_REQUIREMENTS[DEFAULT_DOCUMENT_PURPOSE];

  const handleUploadDocument = async (file) => {
    const purpose = resolveDocumentPurpose();
    let uploaded = null;
    setUploadingDocument(true);
    try {
      const response = await documentsAPI.upload(file, {
        source_context: DOCUMENT_SOURCE_CONTEXT,
        document_type: purpose.documentType || undefined,
        category: purpose.key !== DEFAULT_DOCUMENT_PURPOSE ? purpose.key : undefined,
      });
      uploaded = response?.data ?? null;
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to upload document"));
      return;
    } finally {
      setUploadingDocument(false);
    }

    const documentId = getDocumentRefId(uploaded);
    if (!uploaded || !documentId) return;
    if (attachedDocuments.some((item) => getDocumentRefId(item) === documentId)) return;

    syncAttachedDocuments([
      ...attachedDocuments,
      {
        document_id: uploaded.document_id || documentId,
        filename: uploaded.filename || "",
        original_name: uploaded.original_name || file.name,
        file_size: uploaded.file_size || null,
        content_type: uploaded.content_type || file.type || null,
        url: uploaded.url || "",
        source_context: DOCUMENT_SOURCE_CONTEXT,
        uploaded_at: uploaded.uploaded_at || null,
        document_type: uploaded?.metadata?.document_type || purpose.documentType || "",
        purpose_key: purpose.key,
        purpose_label: purpose.label,
      },
    ]);
    toast.success("Document uploaded and added to this profile");
  };

  const handleRemoveAttachedDocument = (documentId) => {
    syncAttachedDocuments(attachedDocuments.filter((document) => getDocumentRefId(document) !== documentId));
  };

  const handleMediaUpload = async ({ event, type }) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const setUploading = type === "photo" ? setUploadingPhoto : setUploadingSignature;
    const upload = type === "photo" ? employeeProfileApi.uploadPhoto : employeeProfileApi.uploadSignature;
    const responseField = type === "photo" ? "photo_url" : "signature_url";

    setUploading(true);
    try {
      const res = await upload(file);
      const uploadedUrl = res.data?.[responseField];
      if (!uploadedUrl) throw new Error(`No ${responseField} returned`);
      updateField(responseField, uploadedUrl);
      toast.success(type === "photo" ? "Photo uploaded. Save profile to apply it." : "Signature uploaded. Save profile to apply it.");
    } catch (error) {
      toast.error(getApiErrorMessage(error, type === "photo" ? "Failed to upload photo" : "Failed to upload signature"));
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextErrors = validateForm({
      formData,
      employmentType,
      essMode,
      typeSpecificFields,
      modernRequiredFields: requiredModernFields,
    });
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    try {
      const payload = essMode
        ? buildEssPayload(formData, employmentType)
        : buildAdminPayload(formData, employmentType);
      await submitAction(payload);
      await onSuccess?.();
    } catch (error) {
      const { fieldErrors, toastMessage } = resolveProfileSubmitError({
        error,
        isEditMode: true,
      });
      if (fieldErrors) setErrors(fieldErrors);
      toast.error(getApiErrorMessage(error, toastMessage));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6" data-testid="employee-profile-extension-editor">
      {!essMode && isRegular && (
        <Card className="border-amber-200 bg-amber-50/60">
          <CardContent className="py-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-1 text-sm text-amber-900">
              <p className="font-medium">Service Book biodata is immutable here.</p>
              <p>This screen updates only profile-extension fields. Service Book Part I corrections must stay in Service Book flows.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {showModernNonRegularEditor && (
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
      )}

      {!!typeSpecificFields.length && (
        <Card>
          <CardHeader>
            <CardTitle>Employment Details</CardTitle>
            <CardDescription>Fields specific to {employmentType.toLowerCase()} employees.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {typeSpecificFields.map((field) => renderTypeSpecificField({
              field,
              value: formData[field.id],
              onChange: updateField,
              error: errors[field.id],
              payLevelOptions,
            }))}
          </CardContent>
        </Card>
      )}

      {showModernNonRegularEditor && (
        <Card>
          <CardHeader>
            <CardTitle>Personal Profile</CardTitle>
            <CardDescription>Additional demographic details stored on the employee-owned profile extension.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <TextField id="father_name" label="Father's Name" value={formData.father_name} onChange={updateField} error={errors.father_name} />
            <TextField id="mother_name" label="Mother's Name" value={formData.mother_name} onChange={updateField} error={errors.mother_name} />
            <TextField id="nationality" label="Nationality" value={formData.nationality} onChange={updateField} error={errors.nationality} />
            <TextField id="category" label="Category" value={formData.category} onChange={updateField} error={errors.category} placeholder="General / ST / SC / OBC" />
            <TextField id="religion" label="Religion" value={formData.religion} onChange={updateField} error={errors.religion} />
            <SelectField
              id="blood_group"
              label="Blood Group"
              value={formData.blood_group}
              onChange={updateField}
              options={BLOOD_GROUP_OPTIONS}
              error={errors.blood_group}
              placeholder="Select blood group"
            />
            <SelectField
              id="marital_status"
              label="Marital Status"
              value={formData.marital_status}
              onChange={updateField}
              options={MARITAL_STATUS_OPTIONS}
              error={errors.marital_status}
              placeholder="Select marital status"
            />
            {formData.marital_status === "MARRIED" && (
              <TextField id="spouse_name" label="Spouse Name" value={formData.spouse_name} onChange={updateField} error={errors.spouse_name} />
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Contact Details</CardTitle>
          <CardDescription>Employee-owned contact and communication details.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextField id="mobile_primary" label="Primary Mobile" value={formData.mobile_primary} onChange={updateField} error={errors.mobile_primary} />
          <TextField id="mobile_alternate" label="Alternate Mobile" value={formData.mobile_alternate} onChange={updateField} error={errors.mobile_alternate} />
          <TextField id="email_personal" label="Personal Email" type="email" value={formData.email_personal} onChange={updateField} error={errors.email_personal} />
          {!essMode && (
            <TextField id="email_official" label="Official Email" type="email" value={formData.email_official} onChange={updateField} error={errors.email_official} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Address</CardTitle>
          <CardDescription>Permanent and present address details.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Permanent Address</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TextField id="address_line1" label="Address Line 1" value={formData.address_line1} onChange={updateField} error={errors.address_line1} />
              <TextField id="address_line2" label="Address Line 2" value={formData.address_line2} onChange={updateField} error={errors.address_line2} />
              <TextField id="city" label="City" value={formData.city} onChange={updateField} error={errors.city} />
              <TextField id="district" label="District" value={formData.district} onChange={updateField} error={errors.district} />
              <TextField id="state" label="State" value={formData.state} onChange={updateField} error={errors.state} />
              <TextField id="pincode" label="Pincode" value={formData.pincode} onChange={updateField} error={errors.pincode} />
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Present Address</p>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Checkbox
                  id="copy-address"
                  checked={hasPermanentAddressValue && areAddressesSynced}
                  disabled={!hasPermanentAddressValue}
                  onCheckedChange={(checked) => {
                    if (!checked || !hasPermanentAddressValue) return;
                    setFormData((current) => ({
                      ...current,
                      present_address_line1: current.address_line1,
                      present_address_line2: current.address_line2,
                      present_city: current.city,
                      present_district: current.district,
                      present_state: current.state,
                      present_pincode: current.pincode,
                    }));
                  }}
                />
                <Label htmlFor="copy-address">Same as permanent address</Label>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TextField id="present_address_line1" label="Address Line 1" value={formData.present_address_line1} onChange={updateField} error={errors.present_address_line1} />
              <TextField id="present_address_line2" label="Address Line 2" value={formData.present_address_line2} onChange={updateField} error={errors.present_address_line2} />
              <TextField id="present_city" label="City" value={formData.present_city} onChange={updateField} error={errors.present_city} />
              <TextField id="present_district" label="District" value={formData.present_district} onChange={updateField} error={errors.present_district} />
              <TextField id="present_state" label="State" value={formData.present_state} onChange={updateField} error={errors.present_state} />
              <TextField id="present_pincode" label="Pincode" value={formData.present_pincode} onChange={updateField} error={errors.present_pincode} />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Photo and Signature</CardTitle>
          <CardDescription>Upload profile media as part of the profile extension.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <MediaUploadField id="profile-extension-photo-upload" label="Profile Photo" value={formData.photo_url} icon={Camera} uploading={uploadingPhoto} onUpload={(event) => handleMediaUpload({ event, type: "photo" })} buttonLabel="Upload Photo" />
          <MediaUploadField id="profile-extension-signature-upload" label="Signature" value={formData.signature_url} icon={PenLine} uploading={uploadingSignature} onUpload={(event) => handleMediaUpload({ event, type: "signature" })} buttonLabel="Upload Signature" previewClassName="h-16 max-w-full object-contain" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Emergency Contact</CardTitle>
          <CardDescription>Profile-managed emergency contact details.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextField id="emergency_name" label="Emergency Contact Name" value={formData.emergency_name} onChange={updateField} error={errors.emergency_name} />
          <TextField id="emergency_phone" label="Emergency Contact Phone" value={formData.emergency_phone} onChange={updateField} error={errors.emergency_phone} />
          <TextField id="emergency_relation" label="Emergency Contact Relation" value={formData.emergency_relation} onChange={updateField} error={errors.emergency_relation} />
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" className="gap-2" disabled={submitting}>
          <Save className="w-4 h-4" />
          {submitting ? "Saving..." : "Save Profile"}
        </Button>
      </div>
    </form>
  );
};

export default EmployeeProfileExtensionEditor;
