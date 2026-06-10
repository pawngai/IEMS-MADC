import { useEffect, useState } from "react";
import { serviceBookRecordsAPI } from "@/contexts/service_book/records/api/serviceBookRecordsApi";
import {
  getFallbackServiceRecordSchema,
  normalizeServiceRecordSchema,
  buildAttachDocumentCommand,
  buildRecordCommand,
  buildCpcChangeFixationCommand,
} from "@/contexts/service_book/records/model/serviceBookRecordsModel";
import {
  AUTO_PAY_FIELDS,
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
  getAutoCalculatedPayValue,
  getBusinessRequiredKeys,
  getCurrentPayStructureValue,
  getEffectiveCpcFieldValues,
  getLatestPayContext,
  getMatchingSelectValue,
  getNextPayCommission,
  getResolvedCpcFieldValue,
  getSelectOptionLabel,
  getSelectOptionValue,
  isActuallyRequiredField,
  isPresent,
  isSystemManagedSourcePayField,
  pickNonEmptyValues,
  validateFormState,
} from "@/contexts/service_book/records/model/recordServiceBookRecordDialogModel";
import RecordServiceBookRecordDocumentUploadSection from "@/contexts/service_book/records/components/RecordServiceBookRecordDocumentUploadSection";
import RecordServiceBookRecordEventDetailsSection from "@/contexts/service_book/records/components/RecordServiceBookRecordEventDetailsSection";
import {
  AuthorityField,
  EventCategorySelect,
  FallbackSchemaNotice,
  RecordDialogActions,
  RemarksField,
} from "@/contexts/service_book/records/components/RecordServiceBookRecordFormControls";
import {
  getFieldLabel,
  getInputPlaceholder,
  getSelectPlaceholder,
} from "@/contexts/service_book/records/lib/recordServiceBookRecordDialogUiHelpers";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/shared/ui/sheet";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { formatDocumentMetadataErrorMessage, getApiErrorMessage } from "@/shared/lib/utils";
import { toast } from "sonner";

const RecordServiceBookRecordDialog = ({ employeeId, onSuccess, onClose }) => {
  const [schema, setSchema] = useState(() => getFallbackServiceRecordSchema());
  const [eventCategory, setEventCategory] = useState(() => getFallbackServiceRecordSchema().canonicalCategoryOptions[0].value);
  const [selectedFromCpc, setSelectedFromCpc] = useState("");
  const [selectedCpc, setSelectedCpc] = useState("7TH_CPC");
  const [effectiveTo, setEffectiveTo] = useState("");
  const [fieldValues, setFieldValues] = useState({});
  const [customDetailRows, setCustomDetailRows] = useState(() => [createEmptyCustomDetailRow()]);
  const [cpcFieldValues, setCpcFieldValues] = useState({});
  const [employeeEvents, setEmployeeEvents] = useState([]);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadDocumentType, setUploadDocumentType] = useState("ORDER");
  const [uploadCategory, setUploadCategory] = useState("");
  const [saving, setSaving] = useState(false);
  const [usingFallbackSchema, setUsingFallbackSchema] = useState(false);
  const [fieldErrors, setFieldErrors] = useState(new Set());
  const [customDetailError, setCustomDetailError] = useState("");

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

  const buildCpcFixationSections = () => {
    const preRevisedPay = pickNonEmptyValues({
      pay_scale: currentPayMatchesSelectedFromCpc ? currentPayContext?.payScale : "",
      pay_band: currentPayMatchesSelectedFromCpc ? currentPayContext?.payBand : "",
      grade_pay: currentPayMatchesSelectedFromCpc ? currentPayContext?.gradePay : "",
      pay_level: currentPayMatchesSelectedFromCpc ? currentPayContext?.payLevel : "",
      pay_cell_index: currentPayMatchesSelectedFromCpc ? currentPayContext?.payCellIndex : "",
      basic_pay: preRevisedBasicPay,
    });
    const fitment = pickNonEmptyValues(
      Object.fromEntries(cpcFixationFitmentFields.map((key) => [key, getResolvedCpcFieldValue(key, cpcValueContext)]))
    );
    const postRevisedPay = pickNonEmptyValues({
      ...fitment,
      basic_pay: dynamicPayFixationValue,
    });

    return {
      preRevisedPay,
      fitment,
      postRevisedPay,
    };
  };

  useEffect(() => {
    let active = true;

    const loadSchema = async () => {
      try {
        const response = await serviceBookRecordsAPI.getRecordSchema();
        const normalizedSchema = normalizeServiceRecordSchema(response?.data);
        if (!active) return;
        setSchema(normalizedSchema);
        setUsingFallbackSchema(false);
        if (!normalizedSchema.canonicalCategoryOptions.some((item) => item.value === eventCategory)) {
          setEventCategory(normalizedSchema.canonicalCategoryOptions[0]?.value || eventCategory);
        }
      } catch {
        // Keep local fallback schema.
        if (active) {
          setUsingFallbackSchema(true);
        }
      }
    };

    loadSchema();
    return () => {
      active = false;
    };
  }, []);

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

  useEffect(() => {
    let active = true;

    const loadEmployeeEvents = async () => {
      if (!employeeId) {
        setEmployeeEvents([]);
        return;
      }
      try {
        const response = await serviceBookRecordsAPI.getEventStream(employeeId);
        const data = response?.data || response;
        if (!active) return;
        setEmployeeEvents(Array.isArray(data) ? data : data.events || []);
      } catch {
        if (active) {
          setEmployeeEvents([]);
        }
      }
    };

    loadEmployeeEvents();
    return () => {
      active = false;
    };
  }, [employeeId]);

  const buildPayload = () => {
    const payload = {};

    if (!isCustomEvent && selectedCpc) {
      payload.cpc = selectedCpc;
    }

    if (eventCategory === "CPC_PAY_FIXATION" && selectedFromCpc) {
      payload.from_cpc = selectedFromCpc;
    }

    if (isCustomEvent) {
      customDetailRows.forEach((row) => {
        const key = String(row.key || "").trim();
        const value = String(row.value || "").trim();
        if (!key || !value) {
          return;
        }
        payload[key] = value;
      });
    }

    for (const key of eventDetailKeys) {
      if (key === "order_no" || key === "order_date") {
        continue;
      }
      const value = String(fieldValues[key] || "").trim();
      if (value) {
        payload[key] = value;
      }
    }

    // CPC-specific pay structure fields
    for (const key of cpcFields) {
      const value = getResolvedCpcFieldValue(key, cpcValueContext);
      if (value) {
        payload[key] = value;
      }
    }

    const optionalKeys = ["order_no", "order_date", "authority", "remarks"];
    for (const key of optionalKeys) {
      const value = String(fieldValues[key] || "").trim();
      if (value) {
        payload[key] = value;
      }
    }

    if (isAppointmentEvent) {
      const appointmentOrderNo = String(fieldValues.appointment_order_no || "").trim();
      const appointmentOrderDate = String(fieldValues.appointment_order_date || "").trim();
      const effectiveDate = String(fieldValues.effective_date || "").trim();
      if (appointmentOrderNo) {
        payload.order_no = appointmentOrderNo;
      }
      if (appointmentOrderDate) {
        payload.order_date = appointmentOrderDate;
      }
      if (effectiveDate) {
        payload.effective_date = effectiveDate;
      }
    }

    return payload;
  };

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isCustomEvent) {
      const populatedRows = customDetailRows
        .map((row) => ({
          key: String(row.key || "").trim(),
          value: String(row.value || "").trim(),
        }))
        .filter((row) => row.key || row.value);

      if (populatedRows.length === 0) {
        setCustomDetailError("Add at least one custom event detail field.");
        toast.error("Add at least one custom event detail field.");
        return;
      }

      if (populatedRows.some((row) => !row.key || !row.value)) {
        setCustomDetailError("Complete or remove any partially filled custom event detail rows.");
        toast.error("Complete or remove any partially filled custom event detail rows.");
        return;
      }

      setCustomDetailError("");
    }

    const validationResult = validateFormState({
      ...baseValidationContext,
      businessRequiredKeys,
      eventCategory,
      selectedPartCode,
      eventDetailKeys,
      fieldValues,
      cpcFieldValues,
      selectedCpc,
      selectedFromCpc,
      currentPayContext,
      currentPayMatchesSelectedCpc,
      currentPayMatchesSelectedFromCpc,
      preRevisedBasicPay,
      dynamicPayFixationValue,
    });
    setFieldErrors(validationResult.fieldErrors);
    if (validationResult.message) {
      toast.error(validationResult.message);
      return;
    }

    const payload = isCpcPayFixationEvent ? null : buildPayload();
    if (!isCpcPayFixationEvent && Object.keys(payload).length === 0) {
      toast.error("At least one payload field is required");
      return;
    }

    setSaving(true);
    try {
      const cmd = isCpcPayFixationEvent
        ? (() => {
            const { preRevisedPay, fitment, postRevisedPay } = buildCpcFixationSections();
            return buildCpcChangeFixationCommand({
              employeeId,
              partCode: selectedPartCode,
              effectiveDate: String(fieldValues.effective_date || "").trim(),
              orderNo: String(fieldValues.order_no || "").trim(),
              orderDate: String(fieldValues.order_date || "").trim(),
              fromCpc: selectedFromCpc,
              toCpc: selectedCpc,
              preRevisedPay,
              fitment,
              postRevisedPay,
              option: {},
              remarks: String(fieldValues.remarks || "").trim(),
            });
          })()
        : buildRecordCommand({
            employeeId,
            eventType: eventCategory,
            partCode: selectedPartCode,
            payload,
            effectiveFrom: null,
            effectiveTo: effectiveTo || null,
          });
      const recordResponse = await serviceBookRecordsAPI.recordEvent(cmd);
      const createdEvent = recordResponse?.data || recordResponse || {};
      const createdEventId = String(createdEvent.service_event_id || "").trim();

      if (uploadFile) {
        if (!createdEventId) {
          toast.error("Service Book record created, but document attachment could not start because the new record ID was unavailable.");
          onSuccess(createdEvent);
          return;
        }

        try {
          const uploadResponse = await serviceBookRecordsAPI.uploadLinkedDocument(uploadFile, {
            entity_type: "SERVICE_RECORD",
            entity_id: createdEventId,
            document_type: uploadDocumentType || undefined,
            category: uploadCategory || undefined,
            source_context: "service_book.records.attach",
          });
          const uploadData = uploadResponse?.data || {};
          const uploadedDocumentId = String(uploadData.document_id || uploadData.filename || "").trim();
          const uploadedDocumentType = String(
            uploadData?.metadata?.document_type || uploadDocumentType || ""
          ).trim() || null;

          if (!uploadedDocumentId) {
            throw new Error("Uploaded document did not return a document ID");
          }

          await serviceBookRecordsAPI.attachDocument(
            createdEventId,
            buildAttachDocumentCommand({
              serviceEventId: createdEventId,
              documentId: uploadedDocumentId,
              documentType: uploadedDocumentType,
            })
          );
        } catch (uploadError) {
          const metadataMessage = formatDocumentMetadataErrorMessage(uploadError);
          if (metadataMessage) {
            toast.error(`${metadataMessage} The Service Book record was recorded successfully.`);
          } else {
            toast.error(getApiErrorMessage(uploadError, "Service Book record recorded, but document upload or attachment failed"));
          }
          onSuccess(createdEvent);
          return;
        }
      }

      onSuccess(createdEvent);
    } catch (err) {
      const msg =
        err?.response?.data?.detail || err.message || "Failed to record event";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

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

          {!isCustomEvent && (isCpcPayFixationEvent ? (
            <div className="space-y-3">
              <p className="text-sm font-semibold">Pay Commission</p>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="fromCpc">{getFieldLabel("From Pay Commission (CPC)", isRequiredField("from_cpc"))}</Label>
                  <select
                    id="fromCpc"
                    className={`flex h-9 w-full rounded-md border ${fieldErrors.has("from_cpc") ? "border-destructive ring-1 ring-destructive" : "border-input"} bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring`}
                    value={selectedFromCpc}
                    onChange={(e) => {
                      const nextFromCpc = e.target.value;
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
                    }}
                  >
                    <option value="">Select from pay commission</option>
                    {fromCpcOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {fieldErrors.has("from_cpc") && (
                    <p className="text-xs text-destructive">This field is required.</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="cpcSelector">{getFieldLabel("To Pay Commission (CPC)", isRequiredField("to_cpc"))}</Label>
                  <select
                    id="cpcSelector"
                    className={`flex h-9 w-full rounded-md border ${fieldErrors.has("to_cpc") ? "border-destructive ring-1 ring-destructive" : "border-input"} bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring`}
                    value={selectedCpc}
                    onChange={(e) => {
                      setSelectedCpc(e.target.value);
                      setCpcFieldValues({});
                      if (fieldErrors.has("to_cpc")) {
                        setFieldErrors((prev) => {
                          const next = new Set(prev);
                          next.delete("to_cpc");
                          return next;
                        });
                      }
                    }}
                  >
                    {cpcOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {fieldErrors.has("to_cpc") && (
                    <p className="text-xs text-destructive">This field is required.</p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm font-semibold">Pay Commission</p>
              <div className="space-y-1.5">
                <Label htmlFor="cpcSelector">Pay Commission (CPC)</Label>
                <select
                  id="cpcSelector"
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  value={selectedCpc}
                  onChange={(e) => {
                    setSelectedCpc(e.target.value);
                    setCpcFieldValues({});
                  }}
                >
                  {cpcOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              {cpcFields.length > 0 && (
                <div className="space-y-3 rounded-md border border-border p-3">
                  <p className="text-sm font-semibold">Pay Structure · {selectedCpcLabel}</p>
                  <div className="grid grid-cols-2 gap-2">
                    {cpcFields.map((key) => {
                      const def = cpcFieldDefs[key] || {
                        label: key.replaceAll("_", " "),
                        type: "text",
                      };
                      const hasError = fieldErrors.has(key);
                      const isRequired = isRequiredField(key);
                      const isSystemManaged = isSystemManagedSourcePayField(key, cpcValueContext);
                      return (
                        <div key={key} className="space-y-1">
                          <Label htmlFor={`cpc_${key}`} className="text-xs text-muted-foreground">{getFieldLabel(def.label, isRequired)}</Label>
                          {def.type === "select" ? (
                            (() => {
                              const options = getCpcSelectOptions(key, def);
                                const resolvedValue = getMatchingSelectValue(
                                  key,
                                  getResolvedCpcFieldValue(key, cpcValueContext),
                                  options
                                );
                              return (
                                <select
                                  id={`cpc_${key}`}
                                  className={`flex h-9 w-full rounded-md border ${hasError ? "border-destructive ring-1 ring-destructive" : "border-input"} bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring`}
                                  value={resolvedValue}
                                  onChange={(e) => onCpcFieldChange(key, e.target.value)}
                                  disabled={isSystemManaged}
                                  required={isRequired}
                                >
                                  <option value="">{getSelectPlaceholder(def.label)}</option>
                                  {options.map((opt) => (
                                    <option key={getSelectOptionValue(opt)} value={getSelectOptionValue(opt)}>
                                      {getSelectOptionLabel(opt)}
                                    </option>
                                  ))}
                                </select>
                              );
                            })()
                          ) : (
                            <Input
                              id={`cpc_${key}`}
                              type={def.type === "number" ? "number" : "text"}
                              placeholder={getInputPlaceholder(key, def)}
                              value={getResolvedCpcFieldValue(key, cpcValueContext)}
                              onChange={(e) => onCpcFieldChange(key, e.target.value)}
                              required={isRequired}
                                readOnly={isSystemManaged || Boolean(getAutoCalculatedPayValue(key, cpcValueContext))}
                              className={hasError ? "border-destructive ring-1 ring-destructive" : undefined}
                            />
                          )}
                          {isSystemManaged && (
                            <p className="text-xs text-muted-foreground">Derived automatically from the employee's latest recorded pay structure.</p>
                          )}
                          {hasError && (
                            <p className="text-xs text-destructive">This field is required.</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ))}

          {isCpcPayFixationEvent && (
            <>
              <div className="space-y-3 rounded-md border border-border p-3">
                <p className="text-sm font-semibold">
                  Pre-Revised Pay{selectedFromCpc ? ` · ${getCpcLabel(selectedFromCpc)}` : ""}
                </p>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {cpcFixationSourceFields.map((key) => {
                    const def = cpcFieldDefs[key] || {
                      label: key.replaceAll("_", " "),
                      type: "text",
                    };
                    const resolvedValue = getResolvedCpcFieldValue(key, cpcValueContext);
                    const hasError = fieldErrors.has(key);
                    const options = getCpcSelectOptions(key, def, selectedFromCpc);

                    return (
                      <div key={`pre_${key}`} className="space-y-1">
                        <Label htmlFor={`pre_${key}`} className="text-xs text-muted-foreground">
                          {def.label}
                        </Label>
                        {def.type === "select" ? (
                          <select
                            id={`pre_${key}`}
                            className={`flex h-9 w-full rounded-md border ${hasError ? "border-destructive ring-1 ring-destructive" : "border-input"} bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring`}
                            value={getMatchingSelectValue(key, resolvedValue, options)}
                            disabled
                          >
                            <option value="">{getSelectPlaceholder(def.label)}</option>
                            {options.map((opt) => (
                              <option key={getSelectOptionValue(opt)} value={getSelectOptionValue(opt)}>
                                {getSelectOptionLabel(opt)}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <Input
                            id={`pre_${key}`}
                            type={def.type === "number" ? "number" : "text"}
                            value={resolvedValue}
                            readOnly
                            className={hasError ? "border-destructive ring-1 ring-destructive" : undefined}
                          />
                        )}
                      </div>
                    );
                  })}
                  <div className="space-y-1">
                    <Label htmlFor="cpc_from_basic_pay" className="text-xs text-muted-foreground">
                      {getFieldLabel("From Basic Pay", isRequiredField("from_basic_pay"))}
                    </Label>
                    <Input
                      id="cpc_from_basic_pay"
                      type="number"
                      placeholder="Derived from the latest recorded basic pay"
                      value={preRevisedBasicPay}
                      readOnly
                      required={isRequiredField("from_basic_pay")}
                      className={fieldErrors.has("from_basic_pay") ? "border-destructive ring-1 ring-destructive" : undefined}
                    />
                    <p className="text-xs text-muted-foreground">Derived automatically from the employee's latest recorded pay structure.</p>
                    {fieldErrors.has("from_basic_pay") && (
                      <p className="text-xs text-destructive">This field is required.</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="space-y-3 rounded-md border border-border p-3">
                <p className="text-sm font-semibold">Fitment · {selectedCpcLabel}</p>
                <div className="grid grid-cols-2 gap-2">
                  {cpcFixationFitmentFields.map((key) => {
                    const def = cpcFieldDefs[key] || {
                      label: key.replaceAll("_", " "),
                      type: "text",
                    };
                    const hasError = fieldErrors.has(key);
                    const isRequired = isRequiredField(key);
                    return (
                      <div key={key} className="space-y-1">
                        <Label htmlFor={`cpc_${key}`} className="text-xs text-muted-foreground">{getFieldLabel(def.label, isRequired)}</Label>
                        {def.type === "select" ? (
                          (() => {
                            const options = getCpcSelectOptions(key, def);
                            return (
                              <select
                                id={`cpc_${key}`}
                                className={`flex h-9 w-full rounded-md border ${hasError ? "border-destructive ring-1 ring-destructive" : "border-input"} bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring`}
                                value={cpcFieldValues[key] || ""}
                                onChange={(e) => onCpcFieldChange(key, e.target.value)}
                                required={isRequired}
                              >
                                <option value="">{getSelectPlaceholder(def.label)}</option>
                                {options.map((opt) => (
                                  <option key={getSelectOptionValue(opt)} value={getSelectOptionValue(opt)}>
                                    {getSelectOptionLabel(opt)}
                                  </option>
                                ))}
                              </select>
                            );
                          })()
                        ) : (
                          <Input
                            id={`cpc_${key}`}
                            type={def.type === "number" ? "number" : "text"}
                            placeholder={getInputPlaceholder(key, def)}
                            value={getResolvedCpcFieldValue(key, cpcValueContext)}
                            onChange={(e) => onCpcFieldChange(key, e.target.value)}
                            required={isRequired}
                            className={hasError ? "border-destructive ring-1 ring-destructive" : undefined}
                          />
                        )}
                        {hasError && (
                          <p className="text-xs text-destructive">This field is required.</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-3 rounded-md border border-border p-3">
                <p className="text-sm font-semibold">Post-Revised Pay · {selectedCpcLabel}</p>
                <div className="grid grid-cols-2 gap-2">
                  {cpcFixationFitmentFields.map((key) => {
                    const def = cpcFieldDefs[key] || {
                      label: key.replaceAll("_", " "),
                      type: "text",
                    };
                    return (
                      <div key={`post_${key}`} className="space-y-1">
                        <Label htmlFor={`post_${key}`} className="text-xs text-muted-foreground">{def.label}</Label>
                        <Input
                          id={`post_${key}`}
                          type={def.type === "number" ? "number" : "text"}
                          value={cpcFieldValues[key] || ""}
                          readOnly
                        />
                      </div>
                    );
                  })}
                  <div className="space-y-1 sm:col-span-2">
                    <Label htmlFor="dynamicPayFixation" className="text-xs text-muted-foreground">
                      {getFieldLabel("Basic Pay", isRequiredField("to_basic_pay"))}
                    </Label>
                    <Input
                      id="dynamicPayFixation"
                      value={dynamicPayFixationValue}
                      placeholder="Calculated automatically from the fitment values"
                      readOnly
                      required={isRequiredField("to_basic_pay")}
                      className={fieldErrors.has("to_basic_pay") ? "border-destructive ring-1 ring-destructive" : undefined}
                    />
                    <p className="text-xs text-muted-foreground">
                      The post-revised basic pay is calculated automatically from the fitment values.
                    </p>
                    {fieldErrors.has("to_basic_pay") && (
                      <p className="text-xs text-destructive">This field is required.</p>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}

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
