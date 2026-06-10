import { Authorities, Permissions, WorkflowStages } from "@/platform/permissions";

const unique = (values) => [...new Set(values)];

const clone = (value) => JSON.parse(JSON.stringify(value));

const toTitle = (value) =>
  String(value || "")
    .toLowerCase()
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

const toTrimmedString = (value) => String(value || "").trim();

const toUpperCode = (value) => toTrimmedString(value).toUpperCase();

const toOptionalNumber = (value) => {
  if (value === "" || value === null || value === undefined) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const dedupeOptions = (values) => unique((values || []).map(toTrimmedString).filter(Boolean));

export const DOCUMENT_CONTENT_TYPE_OPTIONS = [
  { value: "application/pdf", label: "PDF" },
  { value: "image/jpeg", label: "JPEG" },
  { value: "image/png", label: "PNG" },
  { value: "image/webp", label: "WebP" },
  { value: "application/msword", label: "DOC" },
  {
    value: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    label: "DOCX",
  },
  { value: "application/vnd.ms-excel", label: "XLS" },
  {
    value: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    label: "XLSX",
  },
];

export const QUALIFICATION_LEVEL_OPTIONS = [
  { value: "SECONDARY", label: "Secondary" },
  { value: "HIGHER_SECONDARY", label: "Higher Secondary" },
  { value: "DIPLOMA", label: "Diploma" },
  { value: "BACHELOR", label: "Bachelor" },
  { value: "MASTER", label: "Master" },
  { value: "DOCTORATE", label: "Doctorate" },
  { value: "CERTIFICATION", label: "Certification" },
];

export const ROLE_PERMISSION_OPTIONS = unique(Object.values(Permissions)).map((value) => ({
  value,
  label: toTitle(value),
}));

export const AUTHORITY_OPTIONS = unique(Object.values(Authorities)).map((value) => ({
  value,
  label: toTitle(value),
}));

export const WORKFLOW_STAGE_OPTIONS = unique(Object.values(WorkflowStages)).map((value) => ({
  value,
  label: toTitle(value),
}));

const MASTER_IDENTITY_FIELDS = {
  employment_type: {
    codePlaceholder: "e.g., TEMP",
    namePlaceholder: "e.g., Temporary",
    descriptionPlaceholder: "Employment type description",
  },
  pay_level: {
    codePlaceholder: "e.g., L15",
    namePlaceholder: "e.g., Level 15",
    descriptionPlaceholder: "7th CPC pay matrix label",
  },
  service_event_type: {
    codePlaceholder: "e.g., PROM",
    namePlaceholder: "e.g., Promotion",
    descriptionPlaceholder: "Service event description",
  },
  leave_type: {
    codePlaceholder: "e.g., ML",
    namePlaceholder: "e.g., Maternity Leave",
    descriptionPlaceholder: "Leave type description",
  },
  department: {
    codePlaceholder: "e.g., GAD",
    namePlaceholder: "e.g., General Administration Department",
    descriptionPlaceholder: "Optional notes about the department",
  },
  designation: {
    codePlaceholder: "e.g., UDC",
    namePlaceholder: "e.g., Upper Division Clerk",
    descriptionPlaceholder: "Designation description",
  },
  caste_category: {
    codePlaceholder: "e.g., OBC",
    namePlaceholder: "e.g., Other Backward Class",
    descriptionPlaceholder: "Reservation category description",
  },
  service_group: {
    codePlaceholder: "e.g., GRP-E",
    namePlaceholder: "e.g., Group E",
    descriptionPlaceholder: "Service group description",
  },
  service: {
    codePlaceholder: "e.g., ACCOUNTS",
    namePlaceholder: "e.g., Accounts Service",
    descriptionPlaceholder: "Service description",
  },
  document_type: {
    codePlaceholder: "e.g., LICENSE",
    namePlaceholder: "e.g., License",
    descriptionPlaceholder: "Document type description",
  },
  qualification: {
    codePlaceholder: "e.g., BPHARM",
    namePlaceholder: "e.g., Bachelor of Pharmacy",
    descriptionPlaceholder: "Qualification description",
  },
  role: {
    codePlaceholder: "e.g., RECORD_OFFICER",
    namePlaceholder: "e.g., Record Officer",
    descriptionPlaceholder: "Role description",
  },
  workflow_stage: {
    codePlaceholder: "e.g., REVIEWED",
    namePlaceholder: "e.g., Reviewed",
    descriptionPlaceholder: "Workflow stage description",
  },
};

const DEFAULTS = {
  employment_type: {
    has_pension: true,
    has_gpf: true,
    has_leave_account: true,
    has_increment: true,
    can_be_promoted: true,
    can_be_transferred: true,
  },
  pay_level: {
    pay_band: "",
    grade_pay: "",
    basic_min: "",
    basic_max: "",
    annual_increment_rate: "3",
  },
  leave_type: {
    max_days_per_year: "",
    min_days_per_spell: "",
    max_days_per_spell: "",
    max_days_lifetime: "",
    is_encashable: false,
    is_accumulative: false,
    applicable_employment_types: [],
  },
  department: {
    parent_department_code: "",
  },
  designation: {
    pay_level_code: "",
    service_group_code: "",
    is_gazetted: false,
    is_supervisory: false,
  },
  caste_category: {
    reservation_percentage: "0",
  },
  service_group: {
    group_code: "",
    is_gazetted: false,
  },
  service: {},
  document_type: {
    supported_content_types: [],
  },
  qualification: {
    level: "",
    discipline: "",
  },
  role: {
    permissions: [],
  },
  workflow_stage: {
    next_stages: [],
    required_authority: [],
    can_edit: false,
  },
};

export const createEmptyMasterMetadata = (masterType) => clone(DEFAULTS[masterType] || {});

export const getPolicyMasterIdentityFields = (masterType) => (
  MASTER_IDENTITY_FIELDS[masterType] || {
    codePlaceholder: "e.g., MASTER_CODE",
    namePlaceholder: "e.g., Master Name",
    descriptionPlaceholder: "Optional description",
  }
);

export const getPolicyMasterCreateFields = (masterType, referenceOptions = {}) => {
  switch (masterType) {
    case "employment_type":
      return [
        { key: "has_pension", label: "Has Pension", type: "switch" },
        { key: "has_gpf", label: "Has PCF", type: "switch" },
        { key: "has_leave_account", label: "Has Leave Account", type: "switch" },
        { key: "has_increment", label: "Has Increment", type: "switch" },
        { key: "can_be_promoted", label: "Can Be Promoted", type: "switch" },
        { key: "can_be_transferred", label: "Can Be Transferred", type: "switch" },
      ];
    case "pay_level":
      return [
        { key: "pay_band", label: "Pay Band *", type: "text", placeholder: "e.g., PB-2" },
        { key: "grade_pay", label: "Grade Pay", type: "number", placeholder: "Optional" },
        { key: "basic_min", label: "Basic Min *", type: "number", placeholder: "e.g., 35400" },
        { key: "basic_max", label: "Basic Max *", type: "number", placeholder: "e.g., 112400" },
        { key: "annual_increment_rate", label: "Annual Increment Rate", type: "number", placeholder: "3" },
      ];
    case "leave_type":
      return [
        { key: "max_days_per_year", label: "Max Days Per Year", type: "number", placeholder: "Optional" },
        { key: "min_days_per_spell", label: "Min Days Per Spell", type: "number", placeholder: "Optional" },
        { key: "max_days_per_spell", label: "Max Days Per Spell", type: "number", placeholder: "Optional" },
        { key: "max_days_lifetime", label: "Max Days Lifetime", type: "number", placeholder: "Optional" },
        { key: "is_encashable", label: "Is Encashable", type: "switch" },
        { key: "is_accumulative", label: "Is Accumulative", type: "switch" },
        {
          key: "applicable_employment_types",
          label: "Applicable Employment Types",
          type: "multiselect",
          options: referenceOptions.employmentTypeOptions || [],
          fullWidth: true,
        },
      ];
    case "department":
      return [
        {
          key: "parent_department_code",
          label: "Parent Department (Optional)",
          type: "select",
          options: referenceOptions.departmentOptions || [],
          placeholder: "Leave blank for a top-level department",
          helperText: "Department masters now only capture an optional parent department link.",
        },
      ];
    case "designation":
      return [
        {
          key: "pay_level_code",
          label: "Pay Level *",
          type: "select",
          options: referenceOptions.payLevelOptions || [],
          placeholder: "Select pay level",
        },
        {
          key: "service_group_code",
          label: "Service Group *",
          type: "select",
          options: referenceOptions.serviceGroupOptions || [],
          placeholder: "Select service group",
        },
        { key: "is_gazetted", label: "Gazetted", type: "switch" },
        { key: "is_supervisory", label: "Supervisory", type: "switch" },
      ];
    case "caste_category":
      return [
        { key: "reservation_percentage", label: "Reservation Percentage", type: "number", placeholder: "e.g., 27" },
      ];
    case "service_group":
      return [
        { key: "group_code", label: "Group Code", type: "text", placeholder: "e.g., A" },
        { key: "is_gazetted", label: "Gazetted", type: "switch" },
      ];
    case "document_type":
      return [
        {
          key: "supported_content_types",
          label: "Supported Content Types",
          type: "multiselect",
          options: DOCUMENT_CONTENT_TYPE_OPTIONS,
          fullWidth: true,
        },
      ];
    case "qualification":
      return [
        { key: "level", label: "Level *", type: "select", options: QUALIFICATION_LEVEL_OPTIONS, placeholder: "Select level" },
        { key: "discipline", label: "Discipline", type: "text", placeholder: "Optional" },
      ];
    case "role":
      return [
        {
          key: "permissions",
          label: "Permissions *",
          type: "multiselect",
          options: ROLE_PERMISSION_OPTIONS,
          fullWidth: true,
        },
      ];
    case "workflow_stage":
      return [
        {
          key: "next_stages",
          label: "Next Stages",
          type: "multiselect",
          options: WORKFLOW_STAGE_OPTIONS,
          fullWidth: true,
        },
        {
          key: "required_authority",
          label: "Required Authorities",
          type: "multiselect",
          options: AUTHORITY_OPTIONS,
          fullWidth: true,
        },
        { key: "can_edit", label: "Can Edit", type: "switch" },
      ];
    default:
      return [];
  }
};

export const validateMasterMetadata = (masterType, formState, recordCode = "") => {
  const normalizedCode = toUpperCode(recordCode);

  switch (masterType) {
    case "pay_level": {
      const basicMin = toOptionalNumber(formState.basic_min);
      const basicMax = toOptionalNumber(formState.basic_max);
      const annualIncrementRate = toOptionalNumber(formState.annual_increment_rate);
      const gradePay = toOptionalNumber(formState.grade_pay);

      if (!toTrimmedString(formState.pay_band) || basicMin === undefined || basicMax === undefined) {
        return "Pay Band, Basic Min, and Basic Max are required";
      }
      if (basicMax < basicMin) return "Basic Max must be greater than or equal to Basic Min";
      if (annualIncrementRate !== undefined && annualIncrementRate < 0) return "Annual Increment Rate cannot be negative";
      if (gradePay !== undefined && gradePay < 0) return "Grade Pay cannot be negative";
      return null;
    }
    case "leave_type": {
      const maxDays = toOptionalNumber(formState.max_days_per_year);
      const minDaysPerSpell = toOptionalNumber(formState.min_days_per_spell);
      const maxDaysPerSpell = toOptionalNumber(formState.max_days_per_spell);
      const maxDaysLifetime = toOptionalNumber(formState.max_days_lifetime);
      if (maxDays !== undefined && maxDays < 0) return "Max Days Per Year cannot be negative";
      if (minDaysPerSpell !== undefined && minDaysPerSpell < 0) return "Min Days Per Spell cannot be negative";
      if (maxDaysPerSpell !== undefined && maxDaysPerSpell < 0) return "Max Days Per Spell cannot be negative";
      if (maxDaysLifetime !== undefined && maxDaysLifetime < 0) return "Max Days Lifetime cannot be negative";
      if (
        minDaysPerSpell !== undefined
        && maxDaysPerSpell !== undefined
        && maxDaysPerSpell < minDaysPerSpell
      ) {
        return "Max Days Per Spell must be greater than or equal to Min Days Per Spell";
      }
      return null;
    }
    case "department":
      if (normalizedCode && toUpperCode(formState.parent_department_code) === normalizedCode) {
        return "Parent Department cannot be the same as the record code";
      }
      return null;
    case "designation":
      if (!toTrimmedString(formState.pay_level_code) || !toTrimmedString(formState.service_group_code)) {
        return "Pay Level and Service Group are required";
      }
      return null;
    case "caste_category": {
      const reservationPercentage = toOptionalNumber(formState.reservation_percentage) ?? 0;
      if (reservationPercentage < 0 || reservationPercentage > 100) {
        return "Reservation Percentage must be between 0 and 100";
      }
      return null;
    }
    case "service_group":
      if (!toTrimmedString(formState.group_code)) {
        return "Group Code is required";
      }
      return null;
    case "qualification":
      if (!toTrimmedString(formState.level)) {
        return "Qualification level is required";
      }
      return null;
    case "role":
      if (!Array.isArray(formState.permissions) || formState.permissions.length === 0) {
        return "Select at least one permission";
      }
      return null;
    case "workflow_stage":
      if (normalizedCode && dedupeOptions(formState.next_stages).includes(normalizedCode)) {
        return "Next Stages cannot include the current record code";
      }
      return null;
    default:
      return null;
  }
};

export const buildMasterMetadata = (masterType, formState, recordCode = "") => {
  const normalizedCode = toUpperCode(recordCode);

  switch (masterType) {
    case "employment_type":
      return {
        type_code: normalizedCode,
        rules: {
          has_pension: !!formState.has_pension,
          has_gpf: !!formState.has_gpf,
          has_leave_account: !!formState.has_leave_account,
          has_increment: !!formState.has_increment,
          can_be_promoted: !!formState.can_be_promoted,
          can_be_transferred: !!formState.can_be_transferred,
        },
      };
    case "pay_level": {
      const metadata = {
        pay_band: toTrimmedString(formState.pay_band),
        basic_min: toOptionalNumber(formState.basic_min),
        basic_max: toOptionalNumber(formState.basic_max),
        annual_increment_rate: toOptionalNumber(formState.annual_increment_rate) ?? 3,
      };
      const gradePay = toOptionalNumber(formState.grade_pay);
      if (gradePay !== undefined) metadata.grade_pay = gradePay;
      return metadata;
    }
    case "leave_type": {
      const metadata = {
        leave_code: normalizedCode,
        is_encashable: !!formState.is_encashable,
        is_accumulative: !!formState.is_accumulative,
        applicable_employment_types: unique((formState.applicable_employment_types || []).map(toUpperCode).filter(Boolean)),
      };
      const maxDays = toOptionalNumber(formState.max_days_per_year);
      const minDaysPerSpell = toOptionalNumber(formState.min_days_per_spell);
      const maxDaysPerSpell = toOptionalNumber(formState.max_days_per_spell);
      const maxDaysLifetime = toOptionalNumber(formState.max_days_lifetime);
      if (maxDays !== undefined) metadata.max_days_per_year = maxDays;
      if (minDaysPerSpell !== undefined) metadata.min_days_per_spell = minDaysPerSpell;
      if (maxDaysPerSpell !== undefined) metadata.max_days_per_spell = maxDaysPerSpell;
      if (maxDaysLifetime !== undefined) metadata.max_days_lifetime = maxDaysLifetime;
      return metadata;
    }
    case "department":
      return {
        ...(toTrimmedString(formState.parent_department_code) ? { parent_department_code: toUpperCode(formState.parent_department_code) } : {}),
      };
    case "designation":
      return {
        pay_level_code: toUpperCode(formState.pay_level_code),
        service_group_code: toUpperCode(formState.service_group_code),
        is_gazetted: !!formState.is_gazetted,
        is_supervisory: !!formState.is_supervisory,
      };
    case "caste_category":
      return {
        category_code: normalizedCode,
        reservation_percentage: toOptionalNumber(formState.reservation_percentage) ?? 0,
      };
    case "service_group":
      return {
        group_code: toUpperCode(formState.group_code),
        is_gazetted: !!formState.is_gazetted,
      };
    case "document_type":
      return {
        supported_content_types: dedupeOptions(formState.supported_content_types),
      };
    case "qualification":
      return {
        level: toTrimmedString(formState.level),
        ...(toTrimmedString(formState.discipline) ? { discipline: toTrimmedString(formState.discipline) } : {}),
      };
    case "role":
      return {
        permissions: dedupeOptions(formState.permissions),
      };
    case "workflow_stage":
      return {
        next_stages: dedupeOptions(formState.next_stages),
        required_authority: dedupeOptions(formState.required_authority),
        can_edit: !!formState.can_edit,
      };
    default:
      return {};
  }
};