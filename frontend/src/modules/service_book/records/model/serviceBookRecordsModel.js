/**
 * Service Book records domain model - category-driven schema for recording and displaying official records.
 */

import {
  FALLBACK_CANONICAL_CATEGORY_OPTIONS,
  FALLBACK_REQUIRED_PAYLOAD_KEYS_BY_CATEGORY,
  FALLBACK_FIELD_DEFINITIONS,
  FALLBACK_CPC_OPTIONS,
  FALLBACK_CPC_FIELD_DEFINITIONS,
  FALLBACK_CPC_PAYLOAD_KEYS_BY_CATEGORY,
} from "@/modules/service_book/records/model/serviceBookRecordsSchemaFallback";

export const CanonicalCategory = {
  APPOINTMENT: "APPOINTMENT",
  CONFIRMATION: "CONFIRMATION",
  PROMOTION: "PROMOTION",
  TRANSFER: "TRANSFER",
  PAY: "PAY",
  INCREMENT: "INCREMENT",
  DEPUTATION: "DEPUTATION",
  SUSPENSION: "SUSPENSION",
  REINSTATEMENT: "REINSTATEMENT",
  RETIREMENT: "RETIREMENT",
  DISCIPLINARY: "DISCIPLINARY",
  CUSTOM: "CUSTOM",
  GENERIC: "GENERIC",
  FINANCIAL_UPGRADATION: "FINANCIAL_UPGRADATION",
  CPC_PAY_FIXATION: "CPC_PAY_FIXATION",
};

export const EventType = CanonicalCategory;
export const ExternalEventType = {
  CPC_CHANGE_FIXATION: CanonicalCategory.CPC_PAY_FIXATION,
};

export const CATEGORY_TO_PART_CODE = Object.fromEntries(
  FALLBACK_CANONICAL_CATEGORY_OPTIONS.map((option) => [option.value, option.partCode])
);

export const CANONICAL_CATEGORY_OPTIONS = FALLBACK_CANONICAL_CATEGORY_OPTIONS.map(({ value, label }) => ({ value, label }));

export const getFallbackServiceRecordSchema = () => ({
  canonicalCategoryOptions: CANONICAL_CATEGORY_OPTIONS,
  categoryToPartCode: CATEGORY_TO_PART_CODE,
  requiredPayloadKeysByCategory: FALLBACK_REQUIRED_PAYLOAD_KEYS_BY_CATEGORY,
  fieldDefinitions: FALLBACK_FIELD_DEFINITIONS,
  payChange: {
    enabled: true,
    requiredWhenAffectsPay: ["old_basic", "new_basic", "effective_from"],
  },
  cpcOptions: FALLBACK_CPC_OPTIONS,
  cpcFieldDefinitions: FALLBACK_CPC_FIELD_DEFINITIONS,
  cpcPayloadKeysByCategory: FALLBACK_CPC_PAYLOAD_KEYS_BY_CATEGORY,
});

export const normalizeServiceRecordSchema = (raw) => {
  const fallback = getFallbackServiceRecordSchema();
  const source = raw || {};

  const canonicalCategoryOptions = Array.isArray(source.canonical_category_options)
    ? source.canonical_category_options
        .map((item) => {
          const value = String(item?.value || "").trim();
          const label = String(item?.label || value).trim().replace(/\bCpc\b/g, "CPC");
          return { value, label };
        })
        .filter((item) => item.value)
    : fallback.canonicalCategoryOptions;

  const categoryToPartCode =
    source.category_to_part_code && typeof source.category_to_part_code === "object"
      ? Object.fromEntries(
          Object.entries(source.category_to_part_code).map(([category, partCode]) => [
            String(category),
            String(partCode),
          ])
        )
      : fallback.categoryToPartCode;

  const requiredPayloadKeysByCategory =
    source.required_payload_keys_by_category &&
    typeof source.required_payload_keys_by_category === "object"
      ? Object.fromEntries(
          Object.entries(source.required_payload_keys_by_category).map(([category, keys]) => [
            String(category),
            Array.isArray(keys) ? keys.map((key) => String(key)) : [],
          ])
        )
      : fallback.requiredPayloadKeysByCategory;

  const fieldDefinitions =
    source.field_definitions && typeof source.field_definitions === "object"
      ? source.field_definitions
      : fallback.fieldDefinitions;

  const payChange = {
    enabled: Boolean(source.pay_change?.enabled ?? fallback.payChange.enabled),
    requiredWhenAffectsPay: Array.isArray(source.pay_change?.required_when_affects_pay)
      ? source.pay_change.required_when_affects_pay
      : fallback.payChange.requiredWhenAffectsPay,
  };

  const cpcOptions = Array.isArray(source.cpc_options)
    ? source.cpc_options
        .map((item) => ({
          value: String(item?.value || "").trim(),
          label: String(item?.label || item?.value || "").trim(),
        }))
        .filter((item) => item.value)
    : fallback.cpcOptions;

  const cpcFieldDefinitions =
    source.cpc_field_definitions && typeof source.cpc_field_definitions === "object"
      ? source.cpc_field_definitions
      : fallback.cpcFieldDefinitions;

  const cpcPayloadKeysByCategory =
    source.cpc_payload_keys_by_category && typeof source.cpc_payload_keys_by_category === "object"
      ? Object.fromEntries(
          Object.entries(source.cpc_payload_keys_by_category).map(([cpc, catMap]) => [
            String(cpc),
            Object.fromEntries(
              Object.entries(catMap || {}).map(([cat, keys]) => [
                String(cat),
                Array.isArray(keys) ? keys.map(String) : [],
              ])
            ),
          ])
        )
      : fallback.cpcPayloadKeysByCategory;

  return {
    canonicalCategoryOptions,
    categoryToPartCode,
    requiredPayloadKeysByCategory,
    fieldDefinitions,
    payChange,
    cpcOptions,
    cpcFieldDefinitions,
    cpcPayloadKeysByCategory,
  };
};

export const EVENT_TYPE_LABELS = {
  [CanonicalCategory.APPOINTMENT]: "Appointment",
  [CanonicalCategory.CONFIRMATION]: "Confirmation",
  [CanonicalCategory.PROMOTION]: "Promotion",
  [CanonicalCategory.TRANSFER]: "Transfer",
  [CanonicalCategory.PAY]: "Pay",
  [CanonicalCategory.INCREMENT]: "Increment",
  [CanonicalCategory.DEPUTATION]: "Deputation",
  [CanonicalCategory.SUSPENSION]: "Suspension",
  [CanonicalCategory.REINSTATEMENT]: "Reinstatement",
  [CanonicalCategory.RETIREMENT]: "Retirement",
  [CanonicalCategory.DISCIPLINARY]: "Disciplinary",
  [CanonicalCategory.CUSTOM]: "Custom",
  [CanonicalCategory.GENERIC]: "Custom",
  [CanonicalCategory.FINANCIAL_UPGRADATION]: "Financial Upgradation",
  [CanonicalCategory.CPC_PAY_FIXATION]: "CPC Pay Fixation",
};

export const EVENT_TYPE_COLORS = {
  [CanonicalCategory.APPOINTMENT]: "bg-emerald-100 text-emerald-700 border-emerald-300",
  [CanonicalCategory.CONFIRMATION]: "bg-sky-100 text-sky-700 border-sky-300",
  [CanonicalCategory.PROMOTION]: "bg-blue-100 text-blue-700 border-blue-300",
  [CanonicalCategory.TRANSFER]: "bg-cyan-100 text-cyan-700 border-cyan-300",
  [CanonicalCategory.PAY]: "bg-amber-100 text-amber-700 border-amber-300",
  [CanonicalCategory.INCREMENT]: "bg-orange-100 text-orange-700 border-orange-300",
  [CanonicalCategory.DEPUTATION]: "bg-indigo-100 text-indigo-700 border-indigo-300",
  [CanonicalCategory.SUSPENSION]: "bg-orange-100 text-orange-700 border-orange-300",
  [CanonicalCategory.REINSTATEMENT]: "bg-lime-100 text-lime-700 border-lime-300",
  [CanonicalCategory.RETIREMENT]: "bg-neutral-100 text-neutral-700 border-neutral-300",
  [CanonicalCategory.DISCIPLINARY]: "bg-red-100 text-red-700 border-red-300",
  [CanonicalCategory.CUSTOM]: "bg-gray-100 text-gray-700 border-gray-300",
  [CanonicalCategory.GENERIC]: "bg-gray-100 text-gray-700 border-gray-300",
  [CanonicalCategory.FINANCIAL_UPGRADATION]: "bg-yellow-100 text-yellow-700 border-yellow-300",
  [CanonicalCategory.CPC_PAY_FIXATION]: "bg-lime-100 text-lime-700 border-lime-300",
};

export const isLegacyIncrementEvent = (event, eventType = event?.event_type || event?.type) => {
  if (eventType !== CanonicalCategory.PAY) return false;

  const payload = event?.payload || {};
  const remarks = String(payload.remarks || event?.remarks || "").trim().toLowerCase();

  return Boolean(
    payload.increment_type
      || payload.increment_date
      || payload.next_increment_date
      || /\bincrement\b/.test(remarks)
  );
};

export const getServiceRecordDisplayType = (event) => {
  const eventType = event?.event_type || event?.type || CanonicalCategory.GENERIC;
  return isLegacyIncrementEvent(event, eventType) ? CanonicalCategory.INCREMENT : eventType;
};

export const getServiceRecordDisplayLabel = (event) => {
  const displayType = getServiceRecordDisplayType(event);
  return EVENT_TYPE_LABELS[displayType] || EVENT_TYPE_LABELS[CanonicalCategory.GENERIC];
};

/**
 * Builds a RecordServiceEventCommand payload for the backend
 */
export const buildRecordCommand = ({
  employeeId,
  eventType,
  partCode,
  payload = {},
  effectiveFrom = null,
  effectiveTo = null,
}) => ({
  employee_id: employeeId,
  event_type: eventType || CanonicalCategory.GENERIC,
  part_code: partCode || CATEGORY_TO_PART_CODE[eventType] || null,
  payload,
  effective_from: effectiveFrom,
  effective_to: effectiveTo,
});

export const buildCpcChangeFixationCommand = ({
  employeeId,
  partCode,
  effectiveDate,
  orderNo,
  orderDate,
  fromCpc,
  toCpc,
  preRevisedPay = {},
  fitment = {},
  postRevisedPay = {},
  option = {},
  remarks,
}) => ({
  employee_id: employeeId,
  event_type: ExternalEventType.CPC_CHANGE_FIXATION,
  part_code: partCode || CATEGORY_TO_PART_CODE[CanonicalCategory.CPC_PAY_FIXATION] || null,
  effective_from: effectiveDate || null,
  effective_to: null,
  payload: {
    effective_date: effectiveDate || "",
    order_no: orderNo || "",
    order_date: orderDate || "",
    from_cpc: fromCpc || "",
    to_cpc: toCpc || "",
    pre_revised_pay: preRevisedPay,
    fitment,
    post_revised_pay: postRevisedPay,
    option,
    remarks: remarks || "",
  },
});

/**
 * Builds a CorrectServiceEventCommand payload
 */
export const buildCorrectCommand = ({
  serviceEventId,
  correctedPayload,
  reason,
}) => ({
  service_event_id: serviceEventId,
  corrected_payload: correctedPayload,
  reason,
});

/**
 * Builds a VoidServiceEventCommand payload
 */
export const buildVoidCommand = ({ serviceEventId, reason }) => ({
  service_event_id: serviceEventId,
  reason,
});

/**
 * Builds an AttachDocumentCommand payload
 */
export const buildAttachDocumentCommand = ({
  serviceEventId,
  documentId,
  documentType = null,
}) => ({
  service_event_id: serviceEventId,
  document_id: documentId,
  document_type: documentType,
});
