import { useEffect, useMemo, useState } from "react";
import { Button } from "@/shared/ui/button";
import { documentsAPI } from "@/modules/documents";
import { mastersAPI } from "@/modules/organization_master";
import { employeeProfileApi } from "@/modules/employee_master/api/employeeProfileApi";
import { buildPayLevelOptions } from "@/modules/employee_master/model/profileEditorOptions";
import { TYPE_SPECIFIC_FIELDS } from "@/modules/employee_master/model/profileEditorConstants";
import { resolveProfileSubmitError } from "@/modules/employee_master/model/profileSubmitErrors";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { toast } from "sonner";
import { Save } from "lucide-react";
import EmployeeProfileNonRegularEditor from "@/modules/employee_master/components/EmployeeProfileNonRegularEditor";
import {
  EmployeeProfileImmutableNotice,
  EmployeeProfileStandardSections,
  EmployeeProfileTypeSpecificFieldsCard,
} from "@/modules/employee_master/components/EmployeeProfileExtensionSections";
import {
  ADDRESS_FIELD_PAIRS,
  DEFAULT_DOCUMENT_PURPOSE,
  DOCUMENT_REQUIREMENTS,
  DOCUMENT_SOURCE_CONTEXT,
  FieldError,
  FIXED_ENGAGEMENT_DOCUMENT_TYPES,
  LIEN_STATUS_OPTIONS,
  LIST_FIELDS,
  NUMBER_FIELDS,
  RENEWAL_OPTIONS,
  REMUNERATION_TYPE_OPTIONS,
  buildAdminPayload,
  buildEssPayload,
  createEmptyForm,
  getDocumentRecommendations,
  getDocumentRefId,
  isModernNonRegularType,
  mapProfileToForm,
  normalizeCode,
  resolveMediaUrl,
  toOptions,
  validateForm,
} from "@/modules/employee_master/components/EmployeeProfileExtensionEditor.support";

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

  const copyPermanentAddressToPresent = () => {
    setFormData((current) => ({
      ...current,
      present_address_line1: current.address_line1,
      present_address_line2: current.address_line2,
      present_city: current.city,
      present_district: current.district,
      present_state: current.state,
      present_pincode: current.pincode,
    }));
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
      {!essMode && isRegular && <EmployeeProfileImmutableNotice />}

      {showModernNonRegularEditor && (
        <EmployeeProfileNonRegularEditor
          formData={formData}
          errors={errors}
          setFormData={setFormData}
          setErrors={setErrors}
          updateField={updateField}
          nonRegularEmploymentOptions={nonRegularEmploymentOptions}
          selectedEmploymentType={selectedEmploymentType}
          departmentOptions={departmentOptions}
          designationOptions={designationOptions}
          payLevelOptions={payLevelOptions}
          isCoTerminus={isCoTerminus}
          showWages={showWages}
          showFixed={showFixed}
          showRemunerationTypeSelector={showRemunerationTypeSelector}
          showWageInputs={showWageInputs}
          showFixedInputs={showFixedInputs}
          remunerationOptions={remunerationOptions}
          documentRecommendations={documentRecommendations}
          attachedDocumentCounts={attachedDocumentCounts}
          documentPurposeOptions={documentPurposeOptions}
          selectedDocumentPurpose={selectedDocumentPurpose}
          setSelectedDocumentPurpose={setSelectedDocumentPurpose}
          resolveDocumentPurpose={resolveDocumentPurpose}
          uploadingDocument={uploadingDocument}
          handleUploadDocument={handleUploadDocument}
          attachedDocuments={attachedDocuments}
          handleRemoveAttachedDocument={handleRemoveAttachedDocument}
        />
      )}

      <EmployeeProfileTypeSpecificFieldsCard
        employmentType={employmentType}
        typeSpecificFields={typeSpecificFields}
        formData={formData}
        errors={errors}
        updateField={updateField}
        payLevelOptions={payLevelOptions}
      />

      <EmployeeProfileStandardSections
        showModernNonRegularEditor={showModernNonRegularEditor}
        formData={formData}
        errors={errors}
        updateField={updateField}
        essMode={essMode}
        hasPermanentAddressValue={hasPermanentAddressValue}
        areAddressesSynced={areAddressesSynced}
        onCopyPermanentAddress={copyPermanentAddressToPresent}
        uploadingPhoto={uploadingPhoto}
        uploadingSignature={uploadingSignature}
        handleMediaUpload={handleMediaUpload}
      />

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
