import { useState } from "react";
import { serviceBookRecordsAPI } from "@/contexts/service_book/records/api/serviceBookRecordsApi";
import {
  buildAttachDocumentCommand,
  buildCpcChangeFixationCommand,
  buildRecordCommand,
} from "@/contexts/service_book/records/model/serviceBookRecordsModel";
import {
  getResolvedCpcFieldValue,
  pickNonEmptyValues,
  validateFormState,
} from "@/contexts/service_book/records/model/recordServiceBookRecordDialogModel";
import { formatDocumentMetadataErrorMessage, getApiErrorMessage } from "@/shared/lib/utils";
import { toast } from "sonner";

export const useRecordServiceBookRecordSubmit = ({
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
}) => {
  const [saving, setSaving] = useState(false);

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

  return { handleSubmit, saving };
};
