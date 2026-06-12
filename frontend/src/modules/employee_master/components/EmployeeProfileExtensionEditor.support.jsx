import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Checkbox } from "@/shared/ui/checkbox";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { SearchableSelect } from "@/shared/ui/searchable-select";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Textarea } from "@/shared/ui/textarea";
import { resolveEmployeeProfileMediaUrl } from "../api/mediaUrls";
import { FileText, Loader2, Upload } from "lucide-react";

export const RENEWAL_OPTIONS = [
  { value: "YES", label: "Yes" },
  { value: "NO", label: "No" },
];

export const LIEN_STATUS_OPTIONS = [
  { value: "RETAINED", label: "Lien Retained" },
  { value: "SUSPENDED", label: "Lien Suspended" },
];

export const MARITAL_STATUS_OPTIONS = [
  { value: "SINGLE", label: "Single" },
  { value: "MARRIED", label: "Married" },
  { value: "WIDOWED", label: "Widowed" },
  { value: "DIVORCED", label: "Divorced" },
  { value: "SEPARATED", label: "Separated" },
];

export const BLOOD_GROUP_OPTIONS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((value) => ({
  value,
  label: value,
}));

export const MODERN_NON_REGULAR_TYPES = new Set(["CONTRACT", "MUSTER_ROLL", "FIXED_PAY", "CO_TERMINUS", "WAGES"]);
export const FIXED_ENGAGEMENT_DOCUMENT_TYPES = new Set(["CONTRACT", "FIXED_PAY", "CO_TERMINUS"]);
export const NON_REGULAR_HIDDEN_PROFILE_FIELDS = new Set(["vendor_agency"]);
export const LIST_FIELDS = new Set(["document_ids"]);
export const NUMBER_FIELDS = new Set([
  "consolidated_pay",
  "daily_wage_rate",
  "expected_duration_days",
  "deputation_allowance_percent",
  "monthly_billing_rate",
  "fixed_monthly_amount",
  "basic_pay",
]);
export const BOOLEAN_FIELDS = new Set();
export const ESS_FIELD_IDS = [
  "mobile_primary",
  "mobile_alternate",
  "email_personal",
  "address_line1",
  "address_line2",
  "city",
  "district",
  "state",
  "pincode",
  "present_address_line1",
  "present_address_line2",
  "present_city",
  "present_district",
  "present_state",
  "present_pincode",
  "emergency_name",
  "emergency_phone",
  "emergency_relation",
  "photo_url",
  "signature_url",
];
export const ADDRESS_FIELD_PAIRS = [
  ["address_line1", "present_address_line1"],
  ["address_line2", "present_address_line2"],
  ["city", "present_city"],
  ["district", "present_district"],
  ["state", "present_state"],
  ["pincode", "present_pincode"],
];
export const REMUNERATION_TYPE_OPTIONS = ["DAILY_WAGE", "FIXED_MONTHLY"].map((value) => ({ value, label: titleCase(value) }));
export const WAGE_RATE_UNIT_OPTIONS = ["PER_DAY", "PER_MONTH", "PER_HOUR"].map((value) => ({ value, label: titleCase(value) }));
export const DOCUMENT_ACCEPT = ".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx,.xls,.xlsx";
export const DOCUMENT_SOURCE_CONTEXT = "employee_profile.non_regular_profile";
export const DEFAULT_DOCUMENT_PURPOSE = "GENERAL_SUPPORTING";
export const DOCUMENT_REQUIREMENTS = {
  ENGAGEMENT_ORDER: {
    key: "ENGAGEMENT_ORDER",
    label: "Engagement order",
    helper: "Office order, joining memo, or sanction order for the engagement.",
    documentType: "ORDER",
  },
  IDENTITY_PROOF: {
    key: "IDENTITY_PROOF",
    label: "Identity proof",
    helper: "Aadhaar, voter ID, PAN, or another government-issued identity document.",
    documentType: "CERTIFICATE",
  },
  ADDRESS_PROOF: {
    key: "ADDRESS_PROOF",
    label: "Address proof",
    helper: "Residence proof for the current correspondence address.",
    documentType: "CERTIFICATE",
  },
  EDUCATIONAL_CERTIFICATE: {
    key: "EDUCATIONAL_CERTIFICATE",
    label: "Educational certificate",
    helper: "Qualification evidence used to support the selected post or engagement.",
    documentType: "CERTIFICATE",
  },
  CONTRACT_AGREEMENT: {
    key: "CONTRACT_AGREEMENT",
    label: "Contract agreement",
    helper: "Signed contract or engagement agreement for the appointment period.",
    documentType: "MEMORANDUM",
  },
  BANK_DETAILS: {
    key: "BANK_DETAILS",
    label: "Bank details",
    helper: "Cancelled cheque, passbook copy, or account verification proof.",
    documentType: "REPORT",
  },
  GENERAL_SUPPORTING: {
    key: "GENERAL_SUPPORTING",
    label: "General supporting document",
    helper: "Use this for any attachment that does not match the recommended list.",
    documentType: "REPORT",
  },
};

export function titleCase(value) {
  return String(value || "")
    .toLowerCase()
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export const createEmptyForm = () => ({
  employment_type: "",
  date_of_initial_engagement: "",
  current_department_id: "",
  current_designation_id: "",
  father_name: "",
  mother_name: "",
  nationality: "",
  category: "",
  religion: "",
  blood_group: "",
  marital_status: "",
  spouse_name: "",
  contract_order_no: "",
  contract_start_date: "",
  contract_end_date: "",
  consolidated_pay: "",
  contract_authority: "",
  vendor_agency: "",
  renewal_allowed: "",
  engagement_order_no: "",
  engagement_order_date: "",
  engagement_end_date: "",
  remuneration_type: "",
  muster_roll_number: "",
  daily_wage_rate: "",
  wage_rate_unit: "PER_DAY",
  engagement_office: "",
  nature_of_work: "",
  expected_duration_days: "",
  fixed_monthly_amount: "",
  pay_level: "",
  basic_pay: "",
  engagement_remarks: "",
  document_ids: [],
  deputation_order_no: "",
  parent_department: "",
  parent_designation: "",
  lien_status: "",
  deputation_start_date: "",
  deputation_end_date: "",
  deputation_allowance_percent: "",
  outsourcing_order_no: "",
  agency_name: "",
  agency_contract_number: "",
  sla_reference: "",
  monthly_billing_rate: "",
  role_description: "",
  mobile_primary: "",
  mobile_alternate: "",
  email_personal: "",
  email_official: "",
  address_line1: "",
  address_line2: "",
  city: "",
  district: "",
  state: "",
  pincode: "",
  present_address_line1: "",
  present_address_line2: "",
  present_city: "",
  present_district: "",
  present_state: "",
  present_pincode: "",
  emergency_name: "",
  emergency_phone: "",
  emergency_relation: "",
  photo_url: "",
  signature_url: "",
});

export const trimValue = (value) => {
  if (typeof value !== "string") return value;
  const trimmed = value.trim();
  return trimmed || "";
};

export const normalizeCode = (value) => String(value || "").trim().toUpperCase().replace(/[-\s]+/g, "_");
export const isModernNonRegularType = (value) => MODERN_NON_REGULAR_TYPES.has(normalizeCode(value));

export const resolveMediaUrl = (path) => {
  return resolveEmployeeProfileMediaUrl(path);
};

export const toOptions = (items = [], valueKeys, labelKeys) =>
  items
    .map((item) => {
      const value = valueKeys.map((key) => item?.[key]).find(Boolean);
      if (!value) return null;
      const label = labelKeys.map((key) => item?.[key]).find(Boolean) || value;
      return { value: String(value), label: String(label), search: `${label} ${value}` };
    })
    .filter(Boolean);

export const getDocumentRecommendations = (employmentType) => {
  if (!employmentType) return [];
  const code = normalizeCode(employmentType.employment_type_code || employmentType.code || employmentType.value);
  const keys = [];
  if (employmentType.requires_engagement_order) keys.push("ENGAGEMENT_ORDER");
  keys.push("IDENTITY_PROOF", "ADDRESS_PROOF");
  if (FIXED_ENGAGEMENT_DOCUMENT_TYPES.has(code)) keys.push("EDUCATIONAL_CERTIFICATE");
  if (code === "CONTRACT") keys.push("CONTRACT_AGREEMENT");
  keys.push("BANK_DETAILS");
  return [...new Set(keys)].map((key) => DOCUMENT_REQUIREMENTS[key]).filter(Boolean);
};

export const getDocumentRefId = (document) => String(document?.document_id || document?.documentId || document?.filename || "").trim();

export const mapProfileToForm = (profile) => {
  const contact = profile?.contact || {};
  return {
    ...createEmptyForm(),
    employment_type: normalizeCode(profile?.employment_type || profile?.employment_type_code),
    date_of_initial_engagement: profile?.date_of_initial_engagement || "",
    current_department_id: profile?.current_department_id || "",
    current_designation_id: profile?.current_designation_id || "",
    father_name: profile?.father_name || "",
    mother_name: profile?.mother_name || "",
    nationality: profile?.nationality || "",
    category: profile?.category || "",
    religion: profile?.religion || "",
    blood_group: profile?.blood_group || "",
    marital_status: profile?.marital_status || "",
    spouse_name: profile?.spouse_name || "",
    contract_order_no: profile?.contract_order_no || "",
    contract_start_date: profile?.contract_start_date || "",
    contract_end_date: profile?.contract_end_date || "",
    consolidated_pay:
      profile?.consolidated_pay !== undefined && profile?.consolidated_pay !== null
        ? String(profile.consolidated_pay)
        : "",
    contract_authority: profile?.contract_authority || "",
    vendor_agency: profile?.vendor_agency || "",
    renewal_allowed: profile?.renewal_allowed || "",
    engagement_order_no: profile?.engagement_order_no || "",
    engagement_order_date: profile?.engagement_order_date || "",
    engagement_end_date: profile?.engagement_end_date || "",
    remuneration_type: profile?.remuneration_type || "",
    muster_roll_number: profile?.muster_roll_number || "",
    daily_wage_rate:
      profile?.daily_wage_rate !== undefined && profile?.daily_wage_rate !== null
        ? String(profile.daily_wage_rate)
        : "",
    wage_rate_unit: profile?.wage_rate_unit || "PER_DAY",
    engagement_office: profile?.engagement_office || "",
    nature_of_work: profile?.nature_of_work || "",
    expected_duration_days:
      profile?.expected_duration_days !== undefined && profile?.expected_duration_days !== null
        ? String(profile.expected_duration_days)
        : "",
    fixed_monthly_amount:
      profile?.fixed_monthly_amount !== undefined && profile?.fixed_monthly_amount !== null
        ? String(profile.fixed_monthly_amount)
        : "",
    pay_level: profile?.pay_level || "",
    basic_pay:
      profile?.basic_pay !== undefined && profile?.basic_pay !== null
        ? String(profile.basic_pay)
        : "",
    engagement_remarks: profile?.engagement_remarks || "",
    document_ids: Array.isArray(profile?.document_ids) ? profile.document_ids.filter(Boolean) : [],
    deputation_order_no: profile?.deputation_order_no || "",
    parent_department: profile?.parent_department || "",
    parent_designation: profile?.parent_designation || "",
    lien_status: profile?.lien_status || "",
    deputation_start_date: profile?.deputation_start_date || "",
    deputation_end_date: profile?.deputation_end_date || "",
    deputation_allowance_percent:
      profile?.deputation_allowance_percent !== undefined && profile?.deputation_allowance_percent !== null
        ? String(profile.deputation_allowance_percent)
        : "",
    outsourcing_order_no: profile?.outsourcing_order_no || "",
    agency_name: profile?.agency_name || "",
    agency_contract_number: profile?.agency_contract_number || "",
    sla_reference: profile?.sla_reference || "",
    monthly_billing_rate:
      profile?.monthly_billing_rate !== undefined && profile?.monthly_billing_rate !== null
        ? String(profile.monthly_billing_rate)
        : "",
    role_description: profile?.role_description || "",
    mobile_primary: profile?.mobile_primary || contact?.mobile_primary || "",
    mobile_alternate: profile?.mobile_alternate || contact?.mobile_alternate || "",
    email_personal: profile?.email_personal || contact?.email_personal || "",
    email_official: profile?.email_official || contact?.email_official || "",
    address_line1: profile?.address_line1 || contact?.address_line1 || "",
    address_line2: profile?.address_line2 || contact?.address_line2 || "",
    city: profile?.city || contact?.city || "",
    district: profile?.district || contact?.district || "",
    state: profile?.state || contact?.state || "",
    pincode: profile?.pincode || contact?.pincode || "",
    present_address_line1: profile?.present_address_line1 || contact?.present_address_line1 || "",
    present_address_line2: profile?.present_address_line2 || contact?.present_address_line2 || "",
    present_city: profile?.present_city || contact?.present_city || "",
    present_district: profile?.present_district || contact?.present_district || "",
    present_state: profile?.present_state || contact?.present_state || "",
    present_pincode: profile?.present_pincode || contact?.present_pincode || "",
    emergency_name: profile?.emergency_name || contact?.emergency_name || "",
    emergency_phone: profile?.emergency_phone || contact?.emergency_phone || "",
    emergency_relation: profile?.emergency_relation || contact?.emergency_relation || "",
    photo_url: profile?.photo_url || "",
    signature_url: profile?.signature_url || "",
  };
};

export const buildAdminPayload = (formData, employmentType) => {
  const payload = {};
  const isRegular = employmentType === "REGULAR";

  Object.entries(formData).forEach(([field, value]) => {
    if (BOOLEAN_FIELDS.has(field)) {
      payload[field] = Boolean(value);
      return;
    }
    if (typeof value === "boolean") return;
    if (!isRegular && NON_REGULAR_HIDDEN_PROFILE_FIELDS.has(field)) return;

    if (LIST_FIELDS.has(field)) {
      if (!Array.isArray(value) || value.length === 0) return;
      payload[field] = value.map((item) => String(item || "").trim()).filter(Boolean);
      return;
    }

    if (NUMBER_FIELDS.has(field)) {
      if (value === "") return;
      payload[field] = Number(value);
      return;
    }

    const trimmed = trimValue(value);
    if (trimmed === "") return;
    payload[field] = trimmed;
  });

  return payload;
};

export const buildEssPayload = (formData, employmentType) => {
  const payload = {};
  const isRegular = employmentType === "REGULAR";

  ESS_FIELD_IDS.forEach((field) => {
    if (!isRegular && NON_REGULAR_HIDDEN_PROFILE_FIELDS.has(field)) return;
    const value = formData[field];
    if (BOOLEAN_FIELDS.has(field)) {
      payload[field] = Boolean(value);
      return;
    }
    if (typeof value === "boolean") return;
    if (NUMBER_FIELDS.has(field)) {
      if (value === "") return;
      payload[field] = Number(value);
      return;
    }
    const trimmed = trimValue(value);
    if (trimmed === "") return;
    payload[field] = trimmed;
  });

  return payload;
};

export const validateForm = ({ formData, employmentType, essMode, typeSpecificFields, modernRequiredFields }) => {
  const nextErrors = {};

  if (formData.mobile_primary && formData.mobile_primary.replace(/\D/g, "").length < 10) {
    nextErrors.mobile_primary = "Primary mobile number must be at least 10 digits";
  }

  if (essMode) return nextErrors;

  if (modernRequiredFields) {
    modernRequiredFields.forEach((field) => {
      const value = LIST_FIELDS.has(field) ? formData[field] : trimValue(formData[field]);
      const hasValue = LIST_FIELDS.has(field) ? Array.isArray(value) && value.length > 0 : Boolean(value);
      if (!hasValue) nextErrors[field] = "Required";
    });

    if (
      formData.date_of_initial_engagement &&
      formData.engagement_end_date &&
      formData.engagement_end_date < formData.date_of_initial_engagement
    ) {
      nextErrors.engagement_end_date = "End date must be on or after engagement start date";
    }

    return nextErrors;
  }

  typeSpecificFields.forEach((field) => {
    if (!field.required) return;
    if (!trimValue(formData[field.id])) {
      nextErrors[field.id] = `${field.label} is required`;
    }
  });

  return nextErrors;
};

export const FieldError = ({ message, helper }) => {
  if (message) return <p className="text-xs text-red-500">{message}</p>;
  if (helper) return <p className="text-xs text-slate-500">{helper}</p>;
  return null;
};

export const TextField = ({ id, label, value, onChange, error, helper, type = "text", placeholder, disabled, min }) => (
  <div className="space-y-2">
    <Label htmlFor={id}>{label}</Label>
    <Input
      id={id}
      type={type}
      min={min}
      value={value}
      onChange={(event) => onChange(id, event.target.value)}
      placeholder={placeholder}
      disabled={disabled}
    />
    <FieldError message={error} helper={helper} />
  </div>
);

export const TextAreaField = ({ id, label, value, onChange, error, helper, placeholder }) => (
  <div className="space-y-2">
    <Label htmlFor={id}>{label}</Label>
    <Textarea id={id} value={value} onChange={(event) => onChange(id, event.target.value)} placeholder={placeholder} />
    <FieldError message={error} helper={helper} />
  </div>
);

export const SelectField = ({ id, label, value, onChange, options, error, helper, placeholder }) => (
  <div className="space-y-2">
    <Label>{label}</Label>
    <Select value={value || undefined} onValueChange={(nextValue) => onChange(id, nextValue)}>
      <SelectTrigger>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
    <FieldError message={error} helper={helper} />
  </div>
);

export const SearchableSelectField = ({ id, label, value, onChange, options, error, helper, placeholder }) => (
  <div className="space-y-2">
    <Label>{label}</Label>
    <SearchableSelect value={value} onValueChange={(nextValue) => onChange(id, nextValue)} options={options} placeholder={placeholder} />
    <FieldError message={error} helper={helper} />
  </div>
);

export const MediaUploadField = ({
  id,
  label,
  value,
  icon: Icon,
  uploading,
  onUpload,
  buttonLabel,
  previewClassName = "h-24 w-24 object-cover",
}) => (
  <div className="space-y-3 rounded-lg border border-slate-200 p-3">
    <div className="flex items-center justify-between gap-3">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
        <Icon className="h-4 w-4 text-slate-500" />
        {label}
      </div>
      <Button type="button" variant="outline" size="sm" onClick={() => document.getElementById(id)?.click()} disabled={uploading}>
        {uploading ? "Uploading..." : buttonLabel}
      </Button>
    </div>
    <input id={id} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={onUpload} />
    {value ? (
      <div className="rounded-md border border-slate-200 bg-white p-2">
        <img src={resolveMediaUrl(value)} alt={label} className={previewClassName} />
      </div>
    ) : (
      <div className="rounded-md border border-dashed border-slate-300 bg-slate-50 px-3 py-6 text-center text-xs text-slate-500">
        No file uploaded
      </div>
    )}
  </div>
);

export const EmploymentTypeRadioField = ({ label, value, onChange, options, error, helper }) => (
  <div className="space-y-3">
    <Label>{label}</Label>
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3" role="radiogroup" aria-label={label}>
      {options.map((option) => {
        const optionId = `profile-employment-type-${option.value}`;
        return (
          <Label
            key={option.value}
            htmlFor={optionId}
            className={`flex cursor-pointer items-start gap-3 rounded-lg border px-4 py-3 text-sm ${value === option.value ? "border-slate-900 bg-slate-50" : "border-slate-200 bg-white hover:border-slate-300"}`}
          >
            <input
              id={optionId}
              type="radio"
              name="employment_type"
              value={option.value}
              checked={value === option.value}
              onChange={(event) => onChange(event.target.value)}
              className="mt-0.5 h-4 w-4 accent-slate-900"
            />
            <div className="space-y-1">
              <div className="font-medium text-slate-900">{option.label}</div>
              <div className="text-xs uppercase tracking-wide text-slate-500">{titleCase(option.value)}</div>
            </div>
          </Label>
        );
      })}
    </div>
    <FieldError message={error} helper={helper} />
  </div>
);

export const renderTypeSpecificField = ({ field, value, onChange, error, payLevelOptions }) => {
  if (field.id === "pay_level") {
    return (
      <SearchableSelectField
        key={field.id}
        id={field.id}
        label={field.label}
        value={value}
        onChange={onChange}
        options={payLevelOptions}
        error={error}
        placeholder="Select pay level"
      />
    );
  }

  if (field.id === "renewal_allowed") {
    return (
      <SelectField
        key={field.id}
        id={field.id}
        label={field.label}
        value={value}
        onChange={onChange}
        options={RENEWAL_OPTIONS}
        error={error}
        placeholder="Select renewal status"
      />
    );
  }

  if (field.id === "lien_status") {
    return (
      <SelectField
        key={field.id}
        id={field.id}
        label={field.label}
        value={value}
        onChange={onChange}
        options={LIEN_STATUS_OPTIONS}
        error={error}
        placeholder="Select lien status"
      />
    );
  }

  return (
    <TextField
      key={field.id}
      id={field.id}
      label={field.label}
      type={field.type === "number" ? "number" : field.type}
      value={value}
      onChange={onChange}
      error={error}
      placeholder={field.placeholder}
    />
  );
};

