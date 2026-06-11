import { cn } from "@/shared/lib/utils";
import {
  formatDirectoryEnumLabel,
  formatWorkflowStatusLabel,
  resolveReferenceLabel,
} from "@/contexts/employee_master/lib/directoryLabels";
import {
  determineEmploymentType,
  isNonRegularEmploymentType,
  isServiceBookEligible,
} from "@/contexts/service_book";
import { normalizeEmployeeRecord } from "@/contexts/employee_master/services/employeeDomainService";
import { Building2, Briefcase, Calendar, MapPin } from "lucide-react";

export const STATUS_STYLES = {
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
};

export const EMPLOYEE_STATUS_STYLES = {
  Draft: "bg-slate-100 text-slate-700 border-slate-200",
  Pending: "bg-blue-100 text-blue-700 border-blue-200",
  Active: "bg-green-100 text-green-700 border-green-200",
  Suspended: "bg-red-100 text-red-700 border-red-200",
  Retired: "bg-slate-200 text-slate-700 border-slate-300",
  Deputation: "bg-indigo-100 text-indigo-700 border-indigo-200",
};

const OFFICIAL_SERVICE_BOOK_STATES = new Set(["VERIFIED", "APPROVED", "LOCKED"]);

export const getVisibleEmployeeStatus = (profile) => {
  const identityWorkflowStatus = String(profile?.identity_workflow_status || "").trim().toUpperCase();
  const employeeStatus = String(profile?.employee_status || "").trim();

  if (employeeStatus) return formatDirectoryEnumLabel(employeeStatus);
  if (identityWorkflowStatus && identityWorkflowStatus !== "ACTIVE") {
    return identityWorkflowStatus === "DRAFT" ? "Draft" : "Pending";
  }
  return "Active";
};

export const formatDisplayDate = (value) => {
  if (!value) return null;
  const str = String(value);
  if (!/^\d{4}-\d{2}-\d{2}/.test(str)) return str;
  const d = new Date(str.slice(0, 10) + "T00:00:00");
  if (Number.isNaN(d.getTime())) return str;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "2-digit", year: "numeric" });
};

export const formatCurrency = (value) => {
  if (value === undefined || value === null || value === "") return null;
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) return String(value);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(numericValue);
};

const toTimestamp = (value) => {
  if (!value) return 0;
  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? 0 : parsed;
};

export const getCurrentServiceEntry = (serviceBook) => {
  const allEntries = Array.isArray(serviceBook?.part_iv?.entries) ? serviceBook.part_iv.entries : [];
  if (allEntries.length === 0) return null;

  const officialEntries = allEntries.filter((entry) =>
    OFFICIAL_SERVICE_BOOK_STATES.has(String(entry?._meta?.workflow_state || entry?._meta?.status || "").toUpperCase())
  );
  const candidateEntries = officialEntries.length > 0 ? officialEntries : allEntries;

  return [...candidateEntries].sort((left, right) => {
    const leftOpenEnded = left?.period_to ? 0 : 1;
    const rightOpenEnded = right?.period_to ? 0 : 1;
    if (leftOpenEnded !== rightOpenEnded) return rightOpenEnded - leftOpenEnded;

    const leftPeriodTo = toTimestamp(left?.period_to);
    const rightPeriodTo = toTimestamp(right?.period_to);
    if (leftPeriodTo !== rightPeriodTo) return rightPeriodTo - leftPeriodTo;

    const leftPeriodFrom = toTimestamp(left?.period_from);
    const rightPeriodFrom = toTimestamp(right?.period_from);
    if (leftPeriodFrom !== rightPeriodFrom) return rightPeriodFrom - leftPeriodFrom;

    const leftMeta = Math.max(
      toTimestamp(left?._meta?.locked_at),
      toTimestamp(left?._meta?.approved_at),
      toTimestamp(left?._meta?.verified_at),
      toTimestamp(left?._meta?.created_at)
    );
    const rightMeta = Math.max(
      toTimestamp(right?._meta?.locked_at),
      toTimestamp(right?._meta?.approved_at),
      toTimestamp(right?._meta?.verified_at),
      toTimestamp(right?._meta?.created_at)
    );
    return rightMeta - leftMeta;
  })[0];
};

export const hasDisplayValue = (value) => value !== undefined && value !== null && value !== "" && value !== "-";
export const normalizeCode = (value) => String(value || "").trim().toUpperCase().replace(/[-\s]+/g, "_");

export const Field = ({ label, value, mono = false, icon: Icon, className }) => {
  const isDateField = /\bdate\b/i.test(label);
  const display = value !== undefined && value !== null && value !== ""
    ? (isDateField ? formatDisplayDate(value) : String(value))
    : "-";
  return (
    <div className={cn("space-y-1", className)}>
      <p className="flex items-center gap-1 text-xs uppercase tracking-wider text-slate-500">
        {Icon && <Icon className="h-3 w-3" />}
        {label}
      </p>
      <p className={cn("font-medium text-slate-900", mono && "font-mono text-sm")}>
        {display}
      </p>
    </div>
  );
};

export const buildEmployeeProfileSummaryModel = ({ profile, serviceBook, serviceSummary, referenceLabelMaps = {} }) => {
  const normalizedProfile = normalizeEmployeeRecord(profile);
  const currentEmploymentSource = serviceSummary || normalizedProfile;
  const isRegular = isServiceBookEligible(currentEmploymentSource);
  const employmentType = determineEmploymentType(currentEmploymentSource) || "-";
  const contact = normalizedProfile?.contact || {};
  const identifiers = normalizedProfile?.identifiers || {};
  const workflowStatus = normalizedProfile.workflow_status || "DRAFT";
  const workflowStatusLabel = formatWorkflowStatusLabel(workflowStatus);
  const employeeStatus = getVisibleEmployeeStatus(normalizedProfile);
  const currentServiceEntry = getCurrentServiceEntry(serviceBook);
  const currentDesignation = resolveReferenceLabel(
    [
      currentServiceEntry?.post_name,
      currentServiceEntry?.post_held,
      profile.current_designation_name,
      profile.designation_name,
      profile.current_designation_id,
      profile.designation_code,
    ],
    referenceLabelMaps.designation,
  );
  const currentDepartment = resolveReferenceLabel(
    [
      profile.current_department_name,
      profile.department_name,
      profile.current_department_id,
      profile.department_code,
    ],
    referenceLabelMaps.department,
  );
  const currentOffice = resolveReferenceLabel(
    [
      currentServiceEntry?.office_name,
      currentServiceEntry?.office_station,
      profile.current_office_name,
      profile.office_name,
      profile.current_office_id,
      profile.office_code,
    ],
    referenceLabelMaps.office,
  );
  const currentPostingFrom = currentServiceEntry?.period_from || null;
  const currentPayLevel = resolveReferenceLabel(
    [
      currentServiceEntry?.pay_level_name,
      currentServiceEntry?.pay_level,
      profile.pay_level_name,
    ],
    referenceLabelMaps.payLevel,
  );
  const currentBasicPay = currentServiceEntry?.basic_pay ?? null;
  const currentServiceLabel = resolveReferenceLabel(
    [currentServiceEntry?.service_name, profile.service_name],
    referenceLabelMaps.service,
  );
  const serviceGroupLabel = resolveReferenceLabel(
    [currentServiceEntry?.service_group_name, profile.service_group_name],
    referenceLabelMaps.serviceGroup,
  );
  const modeOfRecruitmentLabel = formatDirectoryEnumLabel(currentServiceEntry?.mode_of_recruitment) || "-";
  const employmentTypeLabel = formatDirectoryEnumLabel(employmentType) || "-";
  const remunerationTypeLabel = formatDirectoryEnumLabel(profile.remuneration_type) || "-";
  const wageRateUnitLabel = formatDirectoryEnumLabel(profile.wage_rate_unit) || "-";
  const normalizedEmploymentType = normalizeCode(employmentType);
  const normalizedRemunerationType = normalizeCode(profile.remuneration_type);
  const nonRegularPayLevel = resolveReferenceLabel(
    [profile.pay_level_name, profile.pay_level],
    referenceLabelMaps.payLevel,
  );
  const monthlyRemunerationValue = formatCurrency(profile.fixed_monthly_amount ?? profile.consolidated_pay);
  const isWageBasedType = ["WAGES", "MUSTER_ROLL", "DAILY_WAGE"].includes(normalizedEmploymentType);
  const isFixedRemunerationType = ["FIXED_PAY", "CONTRACT", "CONTRACTUAL", "OUTSOURCED"].includes(normalizedEmploymentType);
  const isPayScaleType = ["CO_TERMINUS"].includes(normalizedEmploymentType);
  const showMonthlyRemuneration = isFixedRemunerationType || (!isWageBasedType && !isPayScaleType && normalizedRemunerationType === "FIXED_MONTHLY");
  const showWageRate = isWageBasedType || (!isPayScaleType && !showMonthlyRemuneration && normalizedRemunerationType === "DAILY_WAGE");
  const showRemunerationType = hasDisplayValue(remunerationTypeLabel)
    && !((showMonthlyRemuneration && normalizedRemunerationType === "FIXED_MONTHLY") || (showWageRate && normalizedRemunerationType === "DAILY_WAGE"));

  const completionFields = [
    profile.full_name,
    profile.gender,
    profile.date_of_birth,
    profile.father_name,
    profile.category,
    contact.mobile_primary || profile.mobile_primary,
    profile.current_department_id,
    profile.date_of_initial_engagement,
  ];
  const regularExtras = isRegular
    ? [
        profile.religion,
        profile.blood_group,
        profile.marital_status,
        identifiers.aadhaar_number,
        identifiers.pan_number,
        contact.address_line1,
        contact.city,
        contact.state,
        contact.emergency_name,
      ]
    : [];
  const allFields = [...completionFields, ...regularExtras];
  const filledCount = allFields.filter(Boolean).length;
  const completionPercent = profile.employee_section_completed && profile.data_entry_section_completed
    ? 100
    : allFields.length
      ? Math.round((filledCount / allFields.length) * 100)
      : 0;
  const genderLabel = formatDirectoryEnumLabel(profile.gender);
  const religionLabel = formatDirectoryEnumLabel(profile.religion);
  const categoryLabel = formatDirectoryEnumLabel(profile.category);
  const nationalityLabel = formatDirectoryEnumLabel(profile.nationality);
  const maritalStatusLabel = formatDirectoryEnumLabel(profile.marital_status);
  const nonRegularEngagementFields = [
    { label: "Current Designation / Post", value: currentDesignation, icon: Briefcase, always: true },
    { label: "Current Department", value: currentDepartment, icon: Building2, always: true },
    { label: "Current Office / Station", value: currentOffice, icon: MapPin },
    { label: "Employee Code", value: profile.employee_code, mono: true, always: true },
    { label: "Employment Type", value: employmentTypeLabel, always: true },
    { label: "Engagement Start Date", value: profile.date_of_initial_engagement, icon: Calendar, always: true },
    { label: "Engagement End Date", value: profile.engagement_end_date, icon: Calendar },
    { label: "Engagement Order No", value: profile.engagement_order_no, mono: true },
    { label: "Engagement Order Date", value: profile.engagement_order_date, icon: Calendar },
    { label: "Remuneration Type", value: showRemunerationType ? remunerationTypeLabel : "" },
    { label: "Monthly Remuneration", value: showMonthlyRemuneration ? monthlyRemunerationValue : "", mono: true },
    { label: "Wage Rate", value: showWageRate ? formatCurrency(profile.daily_wage_rate) : "", mono: true },
    { label: "Wage Rate Unit", value: showWageRate ? wageRateUnitLabel : "" },
    { label: "Pay Level", value: isPayScaleType ? nonRegularPayLevel : "" },
    { label: "Basic Pay", value: isPayScaleType ? formatCurrency(profile.basic_pay) : "", mono: true },
    { label: "Muster Roll Number", value: normalizedEmploymentType === "MUSTER_ROLL" ? profile.muster_roll_number : "", mono: true },
    { label: "Engagement Office", value: showWageRate ? profile.engagement_office : "" },
    { label: "Nature of Work", value: showWageRate ? profile.nature_of_work : "" },
    { label: "Notes", value: profile.engagement_remarks, className: "sm:col-span-2" },
  ].filter((field) => field.always || hasDisplayValue(field.value));
  const regularPersonalFields = [
    { label: "Full Name", value: profile.full_name, className: "sm:col-span-2" },
    { label: "Gender", value: genderLabel },
    { label: "Date of Birth", value: profile.date_of_birth, icon: Calendar },
    { label: "Father's Name", value: profile.father_name },
    { label: "Mother's Name", value: profile.mother_name },
    { label: "Religion", value: religionLabel },
    { label: "Blood Group", value: profile.blood_group },
    { label: "Category", value: categoryLabel },
    { label: "Nationality", value: nationalityLabel },
    { label: "Marital Status", value: maritalStatusLabel },
    ...(profile.marital_status === "MARRIED" ? [{ label: "Spouse Name", value: profile.spouse_name }] : []),
  ];
  const hadPriorEngagement = isRegular && isNonRegularEmploymentType(profile);
  const historicalEmploymentType = determineEmploymentType(normalizedProfile);
  const historicalEmploymentTypeLabel = formatDirectoryEnumLabel(historicalEmploymentType) || "-";
  const normalizedHistoricalEmploymentType = normalizeCode(historicalEmploymentType);
  const historicalRemunerationTypeLabel = formatDirectoryEnumLabel(profile.remuneration_type) || "-";
  const normalizedHistoricalRemunerationType = normalizeCode(profile.remuneration_type);
  const historicalIsWageBased = ["WAGES", "MUSTER_ROLL", "DAILY_WAGE"].includes(normalizedHistoricalEmploymentType);
  const historicalIsFixedRemuneration = ["FIXED_PAY", "CONTRACT", "CONTRACTUAL", "OUTSOURCED"].includes(normalizedHistoricalEmploymentType);
  const historicalIsPayScale = ["CO_TERMINUS"].includes(normalizedHistoricalEmploymentType);
  const showHistoricalMonthlyRemuneration = historicalIsFixedRemuneration
    || (!historicalIsWageBased && !historicalIsPayScale && normalizedHistoricalRemunerationType === "FIXED_MONTHLY");
  const showHistoricalWageRate = historicalIsWageBased
    || (!historicalIsPayScale && !showHistoricalMonthlyRemuneration && normalizedHistoricalRemunerationType === "DAILY_WAGE");
  const showHistoricalRemunerationType = hasDisplayValue(historicalRemunerationTypeLabel)
    && !((showHistoricalMonthlyRemuneration && normalizedHistoricalRemunerationType === "FIXED_MONTHLY")
      || (showHistoricalWageRate && normalizedHistoricalRemunerationType === "DAILY_WAGE"));
  const historicalMonthlyRemuneration = formatCurrency(profile.fixed_monthly_amount ?? profile.consolidated_pay);
  const historicalPayLevel = resolveReferenceLabel(
    [profile.pay_level_name, profile.pay_level],
    referenceLabelMaps.payLevel,
  );
  const priorEngagementFields = [
    { label: "Employment Type", value: historicalEmploymentTypeLabel, always: true },
    { label: "Engagement Start Date", value: profile.date_of_initial_engagement, icon: Calendar, always: true },
    { label: "Engagement End Date", value: profile.engagement_end_date, icon: Calendar },
    { label: "Engagement Order No", value: profile.engagement_order_no, mono: true },
    { label: "Engagement Order Date", value: profile.engagement_order_date, icon: Calendar },
    { label: "Contract Order No", value: profile.contract_order_no, mono: true },
    { label: "Contract Start Date", value: profile.contract_start_date, icon: Calendar },
    { label: "Contract End Date", value: profile.contract_end_date, icon: Calendar },
    { label: "Remuneration Type", value: showHistoricalRemunerationType ? historicalRemunerationTypeLabel : "" },
    { label: "Monthly Remuneration", value: showHistoricalMonthlyRemuneration ? historicalMonthlyRemuneration : "", mono: true },
    { label: "Wage Rate", value: showHistoricalWageRate ? formatCurrency(profile.daily_wage_rate) : "", mono: true },
    { label: "Wage Rate Unit", value: showHistoricalWageRate ? formatDirectoryEnumLabel(profile.wage_rate_unit) : "" },
    { label: "Pay Level", value: historicalIsPayScale ? historicalPayLevel : "" },
    { label: "Basic Pay", value: historicalIsPayScale ? formatCurrency(profile.basic_pay) : "", mono: true },
    { label: "Muster Roll Number", value: normalizedHistoricalEmploymentType === "MUSTER_ROLL" ? profile.muster_roll_number : "", mono: true },
    { label: "Engagement Office", value: profile.engagement_office },
    { label: "Nature of Work", value: profile.nature_of_work },
    { label: "Notes", value: profile.engagement_remarks, className: "sm:col-span-2" },
  ].filter((field) => field.always || hasDisplayValue(field.value));
  const nonRegularPersonalFields = [
    { label: "Full Name", value: profile.full_name, className: "sm:col-span-2", always: true },
    { label: "Gender", value: genderLabel, always: true },
    { label: "Date of Birth", value: profile.date_of_birth, icon: Calendar, always: true },
    { label: "Father's Name", value: profile.father_name },
    { label: "Mother's Name", value: profile.mother_name },
    { label: "Religion", value: religionLabel },
    { label: "Blood Group", value: profile.blood_group },
    { label: "Category", value: categoryLabel },
    { label: "Nationality", value: nationalityLabel },
    { label: "Marital Status", value: maritalStatusLabel },
    { label: "Spouse Name", value: profile.marital_status === "MARRIED" ? profile.spouse_name : "" },
  ].filter((field) => field.always || hasDisplayValue(field.value));

  return {
    normalizedProfile,
    contact,
    identifiers,
    isRegular,
    workflowStatus,
    workflowStatusLabel,
    employeeStatus,
    currentDesignation,
    currentDepartment,
    currentOffice,
    currentPostingFrom,
    currentPayLevel,
    currentBasicPay,
    currentServiceLabel,
    serviceGroupLabel,
    modeOfRecruitmentLabel,
    employmentTypeLabel,
    completionPercent,
    nonRegularEngagementFields,
    regularPersonalFields,
    nonRegularPersonalFields,
    hadPriorEngagement,
    priorEngagementFields,
  };
};
