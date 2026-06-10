export const DURATION_BASED_EVENT_CATEGORIES = new Set(["DEPUTATION", "SUSPENSION"]);
export const AUTO_PAY_FIELDS = new Set(["basic_pay", "from_basic_pay", "to_basic_pay"]);
export const CPC_PAY_FIXATION_EVENT_DETAIL_EXCLUSIONS = new Set(["to_level", "to_basic_pay"]);
export const FINANCIAL_UPGRADATION_EVENT_DETAIL_EXCLUSIONS = new Set(["to_level"]);
export const CPC_PAY_FIXATION_PAY_STRUCTURE_EXCLUSIONS = new Set(["to_basic_pay"]);
export const CPC_PAY_FIXATION_FITMENT_EXCLUSIONS = new Set(["from_basic_pay"]);
export const OPTIONAL_EVENT_DETAIL_KEYS_BY_CATEGORY = {
  APPOINTMENT: ["service", "grade"],
  PROMOTION: ["to_service", "to_service_group", "to_grade"],
};

export const GRADE_PAY_OPTIONS_BY_PAY_BAND = {
  "PB-1 (5200-20200)": ["1800", "1900", "2000", "2400", "2800"],
  "PB-2 (9300-34800)": ["4200", "4400", "4600", "4800", "5400"],
  "PB-3 (15600-39100)": ["5400", "6600", "7600"],
  "PB-4 (37400-67000)": ["8700", "8900", "10000"],
};

export const GRADE_PAY_PARENT_FIELD = {
  grade_pay: "pay_band",
  from_grade_pay: "from_pay_band",
  to_grade_pay: "to_pay_band",
};

export const CURRENT_PAY_CONTEXT_FIELD_MAP = {
  pay_scale: "payScale",
  from_pay_scale: "payScale",
  pay_band: "payBand",
  from_pay_band: "payBand",
  grade_pay: "gradePay",
  from_grade_pay: "gradePay",
  pay_level: "payLevel",
  from_pay_level: "payLevel",
  pay_cell_index: "payCellIndex",
  from_pay_cell_index: "payCellIndex",
};

export const CPC_SOURCE_STRUCTURE_KEYS_BY_CPC = {
  "4TH_CPC": ["from_pay_scale"],
  "5TH_CPC": ["from_pay_scale"],
  "6TH_CPC": ["from_pay_band", "from_grade_pay"],
  "7TH_CPC": ["from_pay_level", "from_pay_cell_index"],
};

export const PAY_BAND_MIN_BY_LABEL = {
  "PB-1 (5200-20200)": 5200,
  "PB-2 (9300-34800)": 9300,
  "PB-3 (15600-39100)": 15600,
  "PB-4 (37400-67000)": 37400,
};

export const PAY_LEVEL_MIN_BY_LABEL = {
  "Level 1": 17400,
  "Level 1A": 18000,
  "Level 2": 19900,
  "Level 3": 21700,
  "Level 4": 25500,
  "Level 5": 29200,
  "Level 6": 35400,
  "Level 7": 39100,
  "Level 8": 44900,
  "Level 9": 47600,
  "Level 10": 56100,
  "Level 10A": 64700,
  "Level 11": 67700,
  "Level 11A": 75100,
  "Level 12": 78800,
  "Level 13": 123100,
  "Level 13A": 131100,
  "Level 14": 140200,
};

export const EFFECTIVE_PAYLOAD_DATE_KEYS = [
  "effective_date",
  "increment_date",
  "promotion_date",
  "upgradation_date",
  "confirmation_date",
  "transfer_date",
  "reinstatement_date",
  "retirement_date",
  "suspension_date",
  "penalty_date",
];

export const DOCUMENT_TYPE_OPTIONS = ["ORDER", "NOTIFICATION", "MEMORANDUM", "CERTIFICATE", "REPORT"];

export const pickNonEmptyValues = (value) => Object.fromEntries(
  Object.entries(value || {}).filter(([, item]) => {
    if (item === null || item === undefined) {
      return false;
    }
    if (typeof item === "string") {
      return item.trim().length > 0;
    }
    return true;
  })
);

export const parseLeadingNumber = (value) => {
  const match = String(value || "").match(/\d+/);
  return match ? Number(match[0]) : null;
};

export const toReadableOptionLabel = (value) => {
  const text = String(value || "").trim();
  if (!text) {
    return "";
  }
  if (text !== text.toLowerCase() && !/[_-]/.test(text)) {
    return text;
  }
  return text
    .replace(/[_-]+/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

export const getSelectOptionValue = (option) => {
  if (option && typeof option === "object") {
    return option.value ?? option.label ?? "";
  }
  return option;
};

export const getSelectOptionLabel = (option) => {
  if (option && typeof option === "object") {
    return String(option.label || option.value || "").trim();
  }
  return toReadableOptionLabel(option);
};

export const normalizePayScaleValue = (value) => String(value || "")
  .replace(/\s*[-–]\s*/g, " ")
  .replace(/\s+/g, " ")
  .trim();

export const getPayScaleStages = (value) => {
  const normalized = normalizePayScaleValue(value)
    .replace(/\/\s*\(fixed\)/gi, "")
    .replace(/\(fixed\)/gi, "")
    .trim();

  if (!normalized) {
    return [];
  }

  const numbers = normalized.match(/\d+/g)?.map(Number).filter(Number.isFinite) || [];
  if (numbers.length === 0) {
    return [];
  }

  if (numbers.length === 1) {
    return numbers;
  }

  const stages = [numbers[0]];
  let current = numbers[0];

  for (let index = 1; index + 1 < numbers.length; index += 2) {
    const increment = numbers[index];
    const stop = numbers[index + 1];

    if (!increment || stop <= current) {
      continue;
    }

    while (current + increment <= stop) {
      current += increment;
      stages.push(current);
    }
  }

  return [...new Set(stages)].sort((left, right) => left - right);
};

export const getNextHigherPayScaleStage = (value, amount) => {
  const numericAmount = Number(amount);
  if (!Number.isFinite(numericAmount)) {
    return null;
  }

  const stages = getPayScaleStages(value);
  return stages.find((stage) => stage > numericAmount) ?? null;
};

export const getPromotionToBasicPay = (context) => {
  if (!["PROMOTION", "FINANCIAL_UPGRADATION"].includes(context.eventCategory)) {
    return "";
  }
  if (!["4TH_CPC", "5TH_CPC"].includes(context.selectedCpc)) {
    return "";
  }

  const fromBasicPay = Number(
    context.currentPayMatchesSelectedCpc
      ? context.currentPayContext?.basicPay
      : context.cpcFieldValues.from_basic_pay
  );
  if (!Number.isFinite(fromBasicPay)) {
    return "";
  }

  const toScale = context.cpcFieldValues.to_pay_scale || "";
  if (!toScale) {
    return "";
  }

  const promotedPay = getNextHigherPayScaleStage(toScale, fromBasicPay);
  return promotedPay ? String(promotedPay) : "";
};

export const getMatchingSelectValue = (key, value, options) => {
  if (!value) {
    return value;
  }

  if (!["pay_scale", "from_pay_scale", "to_pay_scale"].includes(key)) {
    return value;
  }

  const normalizedValue = normalizePayScaleValue(value);
  const matchingOption = (options || []).find(
    (option) => normalizePayScaleValue(getSelectOptionValue(option)) === normalizedValue
  );

  return matchingOption ? getSelectOptionValue(matchingOption) : value;
};

export const FIELD_PLACEHOLDER_EXAMPLES = {
  appointment_order_no: "e.g., MADC/Est/2020/1234",
  order_no: "e.g., MADC/Est/2026/0123",
  post_name: "e.g., Lower Division Clerk (LDC)",
  to_post: "e.g., Upper Division Clerk (UDC)",
  office_name: "e.g., MADC Secretariat, Kolasib",
  to_office: "e.g., MADC Secretariat, Kolasib",
  service: "e.g., General service",
  service_group: "e.g., Group A",
  grade: "e.g., Senior Grade",
  to_service: "e.g., General service",
  to_service_group: "e.g., Group B",
  to_grade: "e.g., Selection Grade",
  borrowing_department: "e.g., Finance Department, MADC",
  authority: "e.g., Chief Executive Member, MADC",
  remarks: "Optional notes shown with this event",
};

export const CUSTOM_EVENT_CATEGORY = "CUSTOM";

export const createEmptyCustomDetailRow = () => ({ key: "", value: "" });

export const normalizeDocumentCategoryValue = (value) => String(value || "")
  .trim()
  .toUpperCase()
  .replaceAll(" ", "_")
  .replaceAll("-", "_");

export const calculateSeventhCpcBasicPay = (payLevelLabel, cellIndexValue) => {
  const basePay = PAY_LEVEL_MIN_BY_LABEL[payLevelLabel] || null;
  if (!basePay) {
    return "";
  }

  if (cellIndexValue === undefined || cellIndexValue === null || String(cellIndexValue).trim() === "") {
    return String(basePay);
  }

  const cellIndex = Number(cellIndexValue);
  if (!Number.isFinite(cellIndex) || cellIndex < 1) {
    return "";
  }

  let amount = basePay;
  for (let currentCell = 1; currentCell < cellIndex; currentCell += 1) {
    amount = Math.round((amount * 1.03) / 100) * 100;
  }

  return String(amount);
};

export const calculateSixthCpcFixationBasicPay = (preRevisedBasicPayValue, payBandLabel, gradePayValue) => {
  const preRevisedBasicPay = Number(preRevisedBasicPayValue);
  const payBandMinimum = PAY_BAND_MIN_BY_LABEL[payBandLabel] || null;
  const gradePay = parseLeadingNumber(gradePayValue);

  if (!Number.isFinite(preRevisedBasicPay) || !payBandMinimum || !gradePay) {
    return "";
  }

  const fitmentPay = Math.ceil((preRevisedBasicPay * 1.86) / 10) * 10;
  const minimumRevisedBasicPay = payBandMinimum + gradePay;
  return String(Math.max(fitmentPay + gradePay, minimumRevisedBasicPay));
};

export const inferPayCommissionFromPayload = (payload) => {
  const postRevisedPay = payload?.post_revised_pay || {};
  const cpc = String(payload?.to_cpc || payload?.cpc || "").trim().toUpperCase();
  if (cpc) {
    return cpc;
  }
  if (
    postRevisedPay?.pay_level
    || payload?.pay_level
    || payload?.from_pay_level
    || payload?.to_pay_level
    || payload?.to_level
    || payload?.pay_change?.old_level
    || payload?.pay_change?.new_level
  ) {
    return "7TH_CPC";
  }
  if (postRevisedPay?.pay_band || payload?.pay_band || payload?.from_pay_band || payload?.to_pay_band) {
    return "6TH_CPC";
  }
  return null;
};

export const getEventEffectiveDateValue = (event) => {
  const payload = event?.payload || {};

  for (const key of EFFECTIVE_PAYLOAD_DATE_KEYS) {
    if (payload?.[key]) {
      return payload[key];
    }
  }

  return event?.effective_from || event?.effective_to || "";
};

export const getEventEffectiveTimestamp = (event) => {
  const effectiveValue = getEventEffectiveDateValue(event);
  return effectiveValue ? new Date(effectiveValue).getTime() : 0;
};

export const getEventRecordedTimestamp = (event) =>
  new Date(event?.recorded_at || event?.created_at || 0).getTime();

export const getLatestPayContext = (events) => {
  const sortedEvents = [...(events || [])].sort((left, right) => {
    const effectiveDelta = getEventEffectiveTimestamp(right) - getEventEffectiveTimestamp(left);
    if (effectiveDelta !== 0) {
      return effectiveDelta;
    }
    return getEventRecordedTimestamp(right) - getEventRecordedTimestamp(left);
  });

  for (const event of sortedEvents) {
    const payload = event?.payload || {};
    const postRevisedPay = payload.post_revised_pay || {};
    const cpc = inferPayCommissionFromPayload(payload);
    const payLevel = String(
      postRevisedPay.pay_level
        || payload.to_pay_level
        || payload.pay_level
        || payload.to_level
        || payload.pay_change?.new_level
        || payload.pay_change?.old_level
        || ""
    ).trim();
    const payScale = String(postRevisedPay.pay_scale || payload.to_pay_scale || payload.pay_scale || "").trim();
    const payBand = String(postRevisedPay.pay_band || payload.to_pay_band || payload.pay_band || "").trim();
    const gradePay = String(postRevisedPay.grade_pay || payload.to_grade_pay || payload.grade_pay || "").trim();
    const payCellIndex = String(postRevisedPay.pay_cell_index || payload.pay_cell_index || "").trim();
    const basicPay = String(
      postRevisedPay.basic_pay
        || payload.to_basic_pay
        || payload.basic_pay
        || payload.pay_change?.new_basic
        || payload.pay_change?.old_basic
        || calculateBasicPayFromSelection(cpc, {
          pay_scale: payScale,
          pay_band: payBand,
          grade_pay: gradePay,
          pay_level: payLevel,
          pay_cell_index: payCellIndex,
        })
        || ""
    ).trim();
    const payContext = {
      basicPay,
      cpc,
      payScale,
      payBand,
      gradePay,
      payLevel,
      payCellIndex,
    };

    if (basicPay || payContext.payScale || payContext.payBand || payContext.payLevel) {
      return payContext;
    }
  }

  return null;
};

export const calculateBasicPayFromSelection = (cpc, values, prefix = "") => {
  if (cpc === "4TH_CPC" || cpc === "5TH_CPC") {
    const pay = parseLeadingNumber(values[`${prefix}pay_scale`]);
    return pay ? String(pay) : "";
  }

  if (cpc === "6TH_CPC") {
    const payBandMinimum = PAY_BAND_MIN_BY_LABEL[values[`${prefix}pay_band`]] || null;
    const gradePay = parseLeadingNumber(values[`${prefix}grade_pay`]);
    if (!payBandMinimum || !gradePay) {
      return "";
    }
    return String(payBandMinimum + gradePay);
  }

  if (cpc === "7TH_CPC") {
    return calculateSeventhCpcBasicPay(values[`${prefix}pay_level`], values[`${prefix}pay_cell_index`] || values.pay_cell_index);
  }

  return "";
};

export const getNextPayCommission = (options, currentValue) => {
  const values = Array.isArray(options) ? options.map((option) => option.value).filter(Boolean) : [];
  const currentIndex = values.indexOf(currentValue);
  if (currentIndex === -1) {
    return "";
  }
  return values[currentIndex + 1] || values[currentIndex] || "";
};

export const isPresent = (value) => {
  if (value === null || value === undefined) {
    return false;
  }
  if (typeof value === "string") {
    return value.trim().length > 0;
  }
  return true;
};

export const getCurrentPayStructureValue = (key, context) => {
  const payContextKey = CURRENT_PAY_CONTEXT_FIELD_MAP[key];
  const isSourceField = String(key || "").startsWith("from_");
  const hasMatchingCurrentPay = isSourceField
    ? Boolean(context.currentPayMatchesSelectedFromCpc)
    : Boolean(context.currentPayMatchesSelectedCpc);

  if (!payContextKey || !hasMatchingCurrentPay) {
    return "";
  }
  return context.currentPayContext?.[payContextKey] || "";
};

export const isSystemManagedSourcePayField = (key, context) => {
  if (!String(key || "").startsWith("from_")) {
    return false;
  }
  return isPresent(getCurrentPayStructureValue(key, context)) || Boolean(getAutoCalculatedPayValue(key, context));
};

export const getEffectiveCpcFieldValues = (context) => {
  const nextValues = { ...(context.cpcFieldValues || {}) };

  if (!context.currentPayMatchesSelectedCpc) {
    return nextValues;
  }

  for (const [fieldKey, payContextKey] of Object.entries(CURRENT_PAY_CONTEXT_FIELD_MAP)) {
    if (!isPresent(nextValues[fieldKey]) && isPresent(context.currentPayContext?.[payContextKey])) {
      nextValues[fieldKey] = context.currentPayContext[payContextKey];
    }
  }

  return nextValues;
};

export const getAutoCalculatedPayValue = (key, context) => {
  const {
    cpcFieldValues,
    selectedCpc,
    selectedFromCpc,
    currentPayContext,
    currentPayMatchesSelectedCpc,
    currentPayMatchesSelectedFromCpc,
    isCpcPayFixationEvent,
  } = context;
  const effectiveCpcFieldValues = currentPayMatchesSelectedCpc
    ? getEffectiveCpcFieldValues(context)
    : cpcFieldValues;

  if (!AUTO_PAY_FIELDS.has(key)) {
    return "";
  }

  if (key === "basic_pay") {
    return calculateBasicPayFromSelection(selectedCpc, effectiveCpcFieldValues);
  }

  if (key === "from_basic_pay") {
    if (currentPayMatchesSelectedFromCpc) {
      return currentPayContext?.basicPay || "";
    }
    const derivedFromSelection = calculateBasicPayFromSelection(selectedFromCpc, cpcFieldValues, "from_");
    if (derivedFromSelection) {
      return derivedFromSelection;
    }
    return "";
  }

  if (key === "to_basic_pay") {
    if (!isCpcPayFixationEvent) {
      return getPromotionToBasicPay(context);
    }
    if (selectedCpc === "6TH_CPC") {
      return calculateSixthCpcFixationBasicPay(
        currentPayMatchesSelectedFromCpc
          ? currentPayContext?.basicPay
          : cpcFieldValues.from_basic_pay,
        effectiveCpcFieldValues.pay_band,
        effectiveCpcFieldValues.grade_pay
      );
    }
    return (
      calculateBasicPayFromSelection(selectedCpc, effectiveCpcFieldValues, "to_")
      || calculateBasicPayFromSelection(selectedCpc, effectiveCpcFieldValues)
    );
  }

  return "";
};

export const getResolvedCpcFieldValue = (key, context) => {
  const autoValue = getAutoCalculatedPayValue(key, context);
  if (isPresent(autoValue)) {
    return String(autoValue).trim();
  }
  const currentPayValue = getCurrentPayStructureValue(key, context);
  if (isPresent(currentPayValue)) {
    return String(currentPayValue).trim();
  }
  return String(context.cpcFieldValues[key] || "").trim();
};

export const getBusinessRequiredKeys = (context) => {
  const {
    isAppointmentEvent,
    authorityRequired,
    isCpcPayFixationEvent,
    cpcFields,
    cpcFixationFitmentFields,
  } = context;
  const keys = new Set();

  if (!isAppointmentEvent) {
    keys.add("order_no");
    keys.add("order_date");
  }

  if (authorityRequired) {
    keys.add("authority");
  }

  if (isCpcPayFixationEvent) {
    keys.add("from_cpc");
    keys.add("to_cpc");
    keys.add("from_basic_pay");
    keys.add("to_basic_pay");
    for (const key of cpcFixationFitmentFields) {
      keys.add(key);
    }
    return keys;
  }

  if (cpcFields.length > 0) {
    for (const key of cpcFields) {
      keys.add(key);
    }
  }

  return keys;
};

export const isActuallyRequiredField = (key, context) => (
  context.requiredFields.includes(key) || context.businessRequiredKeys.has(key)
);

export const validateFormState = (context) => {
  const {
    eventCategory,
    selectedPartCode,
    eventDetailKeys,
    fieldValues,
    selectedFromCpc,
    selectedCpc,
    preRevisedBasicPay,
    dynamicPayFixationValue,
    cpcFields,
    isCpcPayFixationEvent,
    cpcFixationFitmentFields,
  } = context;

  if (!eventCategory) {
    return {
      fieldErrors: new Set(),
      message: "Select an event category",
    };
  }

  if (!selectedPartCode) {
    return {
      fieldErrors: new Set(),
      message: "No service-book part is configured for the selected event category",
    };
  }

  const fieldErrors = new Set();

  for (const key of eventDetailKeys) {
    if (isActuallyRequiredField(key, context) && !isPresent(fieldValues[key])) {
      fieldErrors.add(key);
    }
  }

  if (isCpcPayFixationEvent) {
    if (!isPresent(selectedFromCpc)) {
      fieldErrors.add("from_cpc");
    }
    if (!isPresent(selectedCpc)) {
      fieldErrors.add("to_cpc");
    }
    if (!isPresent(preRevisedBasicPay)) {
      fieldErrors.add("from_basic_pay");
    }
    for (const key of cpcFixationFitmentFields) {
      if (!isPresent(getResolvedCpcFieldValue(key, context))) {
        fieldErrors.add(key);
      }
    }
    if (!isPresent(dynamicPayFixationValue)) {
      fieldErrors.add("to_basic_pay");
    }

    return {
      fieldErrors,
      message: fieldErrors.size > 0
        ? "Complete the CPC change fixation details before recording the event"
        : null,
    };
  }

  if (cpcFields.length > 0) {
    for (const key of cpcFields) {
      if (!isPresent(getResolvedCpcFieldValue(key, context))) {
        fieldErrors.add(key);
      }
    }
  }

  if (fieldErrors.size === 0) {
    return {
      fieldErrors,
      message: null,
    };
  }

  const hasOnlyEventDetailErrors = [...fieldErrors].every((key) => eventDetailKeys.includes(key));
  return {
    fieldErrors,
    message: hasOnlyEventDetailErrors
      ? "Fill all required fields for the selected subtype"
      : "Complete all required pay structure fields before recording the event",
  };
};

