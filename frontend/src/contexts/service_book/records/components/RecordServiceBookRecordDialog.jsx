import { useEffect, useState } from "react";
import {
  CPC_PAY_FIXATION_EVENT_DETAIL_EXCLUSIONS,
  CPC_PAY_FIXATION_FITMENT_EXCLUSIONS,
  CPC_PAY_FIXATION_PAY_STRUCTURE_EXCLUSIONS,
  CPC_SOURCE_STRUCTURE_KEYS_BY_CPC,
  CURRENT_PAY_CONTEXT_FIELD_MAP,
  CUSTOM_EVENT_CATEGORY,
  DURATION_BASED_EVENT_CATEGORIES,
  FINANCIAL_UPGRADATION_EVENT_DETAIL_EXCLUSIONS,
  GRADE_PAY_PARENT_FIELD,
  GRADE_PAY_OPTIONS_BY_PAY_BAND,
  OPTIONAL_EVENT_DETAIL_KEYS_BY_CATEGORY,
  createEmptyCustomDetailRow,
  getBusinessRequiredKeys,
  getCurrentPayStructureValue,
  getEffectiveCpcFieldValues,
  getLatestPayContext,
  getNextPayCommission,
  getResolvedCpcFieldValue,
  isActuallyRequiredField,
  isPresent,
} from "@/contexts/service_book/records/model/recordServiceBookRecordDialogModel";
import RecordServiceBookRecordDocumentUploadSection from "@/contexts/service_book/records/components/RecordServiceBookRecordDocumentUploadSection";
import RecordServiceBookRecordEventDetailsSection from "@/contexts/service_book/records/components/RecordServiceBookRecordEventDetailsSection";
import RecordServiceBookRecordPayCommissionSection from "@/contexts/service_book/records/components/RecordServiceBookRecordPayCommissionSection";
import { useRecordServiceBookRecordSubmit } from "@/contexts/service_book/records/hooks/useRecordServiceBookRecordSubmit";
import {
  AuthorityField,
  EventCategorySelect,
  FallbackSchemaNotice,
  RecordDialogActions,
  RemarksField,
} from "@/contexts/service_book/records/components/RecordServiceBookRecordFormControls";
import { useRecordServiceBookRecordData } from "@/contexts/service_book/records/hooks/useRecordServiceBookRecordData";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/shared/ui/sheet";

const RecordServiceBookRecordDialog = ({ employeeId, onSuccess, onClose }) => {
  const [eventCategory, setEventCategory] = useState("APPOINTMENT");
  const [selectedFromCpc, setSelectedFromCpc] = useState("");
  const [selectedCpc, setSelectedCpc] = useState("7TH_CPC");
  const [effectiveTo, setEffectiveTo] = useState("");
  const [fieldValues, setFieldValues] = useState({});
  const [customDetailRows, setCustomDetailRows] = useState(() => [createEmptyCustomDetailRow()]);
  const [cpcFieldValues, setCpcFieldValues] = useState({});
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadDocumentType, setUploadDocumentType] = useState("ORDER");
  const [uploadCategory, setUploadCategory] = useState("");
  const [fieldErrors, setFieldErrors] = useState(new Set());
  const [customDetailError, setCustomDetailError] = useState("");
  const { employeeEvents, schema, usingFallbackSchema } = useRecordServiceBookRecordData({
    employeeId,
    eventCategory,
    setEventCategory,
  });

  const canonicalCategoryOptions = schema.canonicalCategoryOptions || [];
  const selectedPartCode = schema.categoryToPartCode?.[eventCategory] || null;
  const requiredFields = schema.requiredPayloadKeysByCategory?.[eventCategory] || [];
  const isCustomEvent = eventCategory === CUSTOM_EVENT_CATEGORY;
  const visibleRequiredFields = eventCategory === "CPC_PAY_FIXATION"
    ? requiredFields.filter((key) => !CPC_PAY_FIXATION_EVENT_DETAIL_EXCLUSIONS.has(key))
    : eventCategory === "FINANCIAL_UPGRADATION"
      ? requiredFields.filter((key) => !FINANCIAL_UPGRADATION_EVENT_DETAIL_EXCLUSIONS.has(key))
      : requiredFields;
  const optionalEventDetailKeys = OPTIONAL_EVENT_DETAIL_KEYS_BY_CATEGORY[eventCategory] || [];

  const cpcOptions = schema.cpcOptions || [];
  const getCpcLabel = (value) => cpcOptions.find((option) => option.value === value)?.label || value;
  const selectedCpcLabel = cpcOptions.find((option) => option.value === selectedCpc)?.label || selectedCpc;
  const selectedCategoryLabel = canonicalCategoryOptions.find((option) => option.value === eventCategory)?.label
    || eventCategory.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase()).replace(/\bCpc\b/g, "CPC");
  const selectedEventLabel = eventCategory === "CPC_PAY_FIXATION"
    ? `${selectedCpcLabel.replace(/\s*\([^)]*\)\s*$/, "")} Pay Fixation`
    : selectedCategoryLabel;
  const cpcFieldDefs = schema.cpcFieldDefinitions || {};
  const cpcFields = schema.cpcPayloadKeysByCategory?.[selectedCpc]?.[eventCategory] || [];
  const isCpcPayFixationEvent = eventCategory === "CPC_PAY_FIXATION";
  const fromCpcOptions = isCpcPayFixationEvent
    ? cpcOptions.filter((option) => option.value !== "7TH_CPC")
    : cpcOptions;
  const visibleCpcFields = eventCategory === "CPC_PAY_FIXATION"
    ? cpcFields.filter((key) => !CPC_PAY_FIXATION_PAY_STRUCTURE_EXCLUSIONS.has(key))
    : cpcFields;
  const cpcFixationFitmentFields = isCpcPayFixationEvent
    ? visibleCpcFields.filter((key) => !CPC_PAY_FIXATION_FITMENT_EXCLUSIONS.has(key))
    : [];
  const cpcFixationSourceFields = isCpcPayFixationEvent
    ? CPC_SOURCE_STRUCTURE_KEYS_BY_CPC[selectedFromCpc] || []
    : [];
  const isAppointmentEvent = eventCategory === "APPOINTMENT";
  const authorityRequired = false;
  const showEffectiveTo = DURATION_BASED_EVENT_CATEGORIES.has(eventCategory);
  const appointmentEventDetailKeys = isAppointmentEvent
    ? [...new Set(["appointment_order_no", "appointment_order_date", "effective_date", ...visibleRequiredFields, ...optionalEventDetailKeys])]
    : [];
  const eventDetailKeys = isCustomEvent
    ? []
    : isAppointmentEvent
    ? appointmentEventDetailKeys
    : [...new Set(["order_no", "order_date", ...visibleRequiredFields, ...optionalEventDetailKeys])];
  const currentPayContext = getLatestPayContext(employeeEvents);
  const currentPayMatchesSelectedCpc = Boolean(currentPayContext?.cpc && currentPayContext.cpc === selectedCpc);
  const currentPayMatchesSelectedFromCpc = Boolean(currentPayContext?.cpc && currentPayContext.cpc === selectedFromCpc);
  const baseValidationContext = {
    requiredFields,
    isAppointmentEvent,
    authorityRequired,
    isCpcPayFixationEvent,
    cpcFields,
    cpcFixationFitmentFields,
  };
  const businessRequiredKeys = getBusinessRequiredKeys(baseValidationContext);
  const cpcValueContext = {
    eventCategory,
    cpcFieldValues,
    selectedCpc,
    selectedFromCpc,
    currentPayContext,
    currentPayMatchesSelectedCpc,
    currentPayMatchesSelectedFromCpc,
    isCpcPayFixationEvent,
  };
  const preRevisedBasicPay = getResolvedCpcFieldValue("from_basic_pay", cpcValueContext);

  const isRequiredField = (key) => isActuallyRequiredField(key, {
    ...baseValidationContext,
    businessRequiredKeys,
  });

  const getEventDetailDefinition = (key) => {
    if (key === "order_no") {
      return { label: `${selectedEventLabel} Order No`, type: "text" };
    }
    if (key === "order_date") {
      return { label: `${selectedEventLabel} Order Date`, type: "date" };
    }
    return schema.fieldDefinitions[key] || {
      label: key.replaceAll("_", " "),
      type: "text",
    };
  };

  useEffect(() => {
    if (!showEffectiveTo && effectiveTo) {
      setEffectiveTo("");
    }
  }, [showEffectiveTo, effectiveTo]);

  useEffect(() => {
    const allowedFromCpcValues = new Set(
      fromCpcOptions.map((option) => option.value).filter(Boolean)
    );

    setSelectedFromCpc((prev) => {
      if (prev && !allowedFromCpcValues.has(prev)) {
        return "";
      }
      if (!prev && currentPayContext?.cpc && allowedFromCpcValues.has(currentPayContext.cpc)) {
        return currentPayContext.cpc;
      }
      return prev;
    });
  }, [currentPayContext?.cpc, eventCategory, fromCpcOptions]);

  useEffect(() => {
    if (!currentPayMatchesSelectedCpc || cpcFields.length === 0) {
      return;
    }

    setCpcFieldValues((prev) => {
      let changed = false;
      const next = { ...prev };

      for (const [fieldKey, payContextKey] of Object.entries(CURRENT_PAY_CONTEXT_FIELD_MAP)) {
        if (!cpcFields.includes(fieldKey)) {
          continue;
        }
        if (isPresent(next[fieldKey]) || !isPresent(currentPayContext?.[payContextKey])) {
          continue;
        }
        next[fieldKey] = currentPayContext[payContextKey];
        changed = true;
      }

      return changed ? next : prev;
    });
  }, [
    cpcFields,
    currentPayContext?.payBand,
    currentPayContext?.payCellIndex,
    currentPayContext?.payLevel,
    currentPayContext?.payScale,
    currentPayContext?.gradePay,
    currentPayMatchesSelectedCpc,
  ]);

  const onFieldChange = (key, value) => {
    setFieldValues((prev) => ({ ...prev, [key]: value }));
    if (fieldErrors.has(key)) {
      setFieldErrors((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  const addCustomDetailRow = () => {
    setCustomDetailRows((prev) => [...prev, createEmptyCustomDetailRow()]);
    setCustomDetailError("");
  };

  const removeCustomDetailRow = (indexToRemove) => {
    setCustomDetailRows((prev) => {
      if (prev.length === 1) {
        return [createEmptyCustomDetailRow()];
      }
      return prev.filter((_, index) => index !== indexToRemove);
    });
    setCustomDetailError("");
  };

  const updateCustomDetailRow = (indexToUpdate, field, value) => {
    setCustomDetailRows((prev) => prev.map((row, index) => (
      index === indexToUpdate ? { ...row, [field]: value } : row
    )));
    setCustomDetailError("");
  };

  const onCpcFieldChange = (key, value) => {
    setCpcFieldValues((prev) => {
      const nextValues = { ...prev, [key]: value };

      if (key === "pay_band") {
        const allowed = GRADE_PAY_OPTIONS_BY_PAY_BAND[value] || [];
        if (nextValues.grade_pay && !allowed.includes(nextValues.grade_pay)) {
          nextValues.grade_pay = "";
        }
      }

      if (key === "from_pay_band") {
        const allowed = GRADE_PAY_OPTIONS_BY_PAY_BAND[value] || [];
        if (nextValues.from_grade_pay && !allowed.includes(nextValues.from_grade_pay)) {
          nextValues.from_grade_pay = "";
        }
      }

      if (key === "to_pay_band") {
        const allowed = GRADE_PAY_OPTIONS_BY_PAY_BAND[value] || [];
        if (nextValues.to_grade_pay && !allowed.includes(nextValues.to_grade_pay)) {
          nextValues.to_grade_pay = "";
        }
      }

      return nextValues;
    });

    if (fieldErrors.has(key)) {
      setFieldErrors((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  const handleFromCpcChange = (nextFromCpc) => {
    setSelectedFromCpc(nextFromCpc);
    const nextToCpc = getNextPayCommission(cpcOptions, nextFromCpc);
    if (nextToCpc) {
      setSelectedCpc(nextToCpc);
      setCpcFieldValues({});
    }
    if (fieldErrors.has("from_cpc")) {
      setFieldErrors((prev) => {
        const next = new Set(prev);
        next.delete("from_cpc");
        return next;
      });
    }
  };

  const handleSelectedCpcChange = (nextCpc, options = {}) => {
    setSelectedCpc(nextCpc);
    setCpcFieldValues({});
    if (options.clearToCpcError && fieldErrors.has("to_cpc")) {
      setFieldErrors((prev) => {
        const next = new Set(prev);
        next.delete("to_cpc");
        return next;
      });
    }
  };

  const getCpcSelectOptions = (key, def, cpcOverride = selectedCpc) => {
    const parentField = GRADE_PAY_PARENT_FIELD[key];
    if (parentField) {
      const selectedPayBand = cpcFieldValues[parentField]
        || getResolvedCpcFieldValue(parentField, cpcValueContext)
        || "";
      return GRADE_PAY_OPTIONS_BY_PAY_BAND[selectedPayBand] || [];
    }
    if (def?.optionsByCpc && typeof def.optionsByCpc === "object") {
      return def.optionsByCpc[cpcOverride] || [];
    }
    if (def?.options_by_cpc && typeof def.options_by_cpc === "object") {
      return def.options_by_cpc[cpcOverride] || [];
    }
    return def?.options || [];
  };

  const dynamicPayFixationValue = eventCategory === "CPC_PAY_FIXATION"
    ? getResolvedCpcFieldValue("to_basic_pay", cpcValueContext)
    : "";
  const { handleSubmit, saving } = useRecordServiceBookRecordSubmit({
    baseValidationContext,
    businessRequiredKeys,
    cpcFieldValues,
    cpcFields,
    cpcFixationFitmentFields,
    cpcValueContext,
    currentPayContext,
    currentPayMatchesSelectedCpc,
    currentPayMatchesSelectedFromCpc,
    customDetailRows,
    dynamicPayFixationValue,
    effectiveTo,
    employeeId,
    eventCategory,
    eventDetailKeys,
    fieldValues,
    isAppointmentEvent,
    isCpcPayFixationEvent,
    isCustomEvent,
    onSuccess,
    preRevisedBasicPay,
    selectedCpc,
    selectedFromCpc,
    selectedPartCode,
    setCustomDetailError,
    setFieldErrors,
    uploadCategory,
    uploadDocumentType,
    uploadFile,
  });

  return (
    <Sheet open onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" size="xl">
        <SheetHeader>
          <SheetTitle>Record Service Book Record</SheetTitle>
          <SheetDescription>
            Create a new Service Book record for this employee
          </SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="space-y-5">
          {usingFallbackSchema && <FallbackSchemaNotice />}

          <EventCategorySelect
            options={canonicalCategoryOptions}
            value={eventCategory}
            onChange={(nextEventCategory) => {
              setEventCategory(nextEventCategory);
              setFieldValues({});
              setCustomDetailRows([createEmptyCustomDetailRow()]);
              setCpcFieldValues({});
              setFieldErrors(new Set());
              setCustomDetailError("");
            }}
          />

          <RecordServiceBookRecordEventDetailsSection
            isCustomEvent={isCustomEvent}
            customDetailRows={customDetailRows}
            customDetailError={customDetailError}
            eventDetailKeys={eventDetailKeys}
            fieldErrors={fieldErrors}
            fieldValues={fieldValues}
            showEffectiveTo={showEffectiveTo}
            effectiveTo={effectiveTo}
            getEventDetailDefinition={getEventDetailDefinition}
            isRequiredField={isRequiredField}
            onFieldChange={onFieldChange}
            onEffectiveToChange={setEffectiveTo}
            onAddCustomDetailRow={addCustomDetailRow}
            onRemoveCustomDetailRow={removeCustomDetailRow}
            onUpdateCustomDetailRow={updateCustomDetailRow}
          />

          {authorityRequired && (
            <AuthorityField
              value={fieldValues.authority}
              required={isRequiredField("authority")}
              onChange={(value) => onFieldChange("authority", value)}
            />
          )}

          <RecordServiceBookRecordPayCommissionSection
            cpcFieldDefs={cpcFieldDefs}
            cpcFields={cpcFields}
            cpcFieldValues={cpcFieldValues}
            cpcFixationFitmentFields={cpcFixationFitmentFields}
            cpcFixationSourceFields={cpcFixationSourceFields}
            cpcOptions={cpcOptions}
            cpcValueContext={cpcValueContext}
            dynamicPayFixationValue={dynamicPayFixationValue}
            fieldErrors={fieldErrors}
            fromCpcOptions={fromCpcOptions}
            getCpcLabel={getCpcLabel}
            getCpcSelectOptions={getCpcSelectOptions}
            isCpcPayFixationEvent={isCpcPayFixationEvent}
            isCustomEvent={isCustomEvent}
            isRequiredField={isRequiredField}
            onCpcFieldChange={onCpcFieldChange}
            onFromCpcChange={handleFromCpcChange}
            onSelectedCpcChange={handleSelectedCpcChange}
            preRevisedBasicPay={preRevisedBasicPay}
            selectedCpc={selectedCpc}
            selectedCpcLabel={selectedCpcLabel}
            selectedFromCpc={selectedFromCpc}
          />

          <RemarksField
            value={fieldValues.remarks}
            onChange={(value) => onFieldChange("remarks", value)}
          />

          <RecordServiceBookRecordDocumentUploadSection
            selectedEventLabel={selectedEventLabel}
            uploadFile={uploadFile}
            uploadDocumentType={uploadDocumentType}
            uploadCategory={uploadCategory}
            saving={saving}
            onUploadFileChange={setUploadFile}
            onUploadDocumentTypeChange={setUploadDocumentType}
            onUploadCategoryChange={setUploadCategory}
          />

          <RecordDialogActions saving={saving} onCancel={onClose} />
        </form>
      </SheetContent>
    </Sheet>
  );
};

export default RecordServiceBookRecordDialog;
