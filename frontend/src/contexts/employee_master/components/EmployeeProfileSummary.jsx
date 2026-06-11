import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Separator } from "@/shared/ui/separator";
import { Progress } from "@/shared/ui/progress";
import { AuthImage } from "@/platform/auth/AuthImage";
import {
  User,
  BookOpen,
  Building2,
  MapPin,
  Phone,
  Mail,
  CreditCard,
  Calendar,
  Briefcase,
  AlertCircle,
  FileText,
  PenLine,
} from "lucide-react";
import {
  normalizeEmployeeRecord,
} from "@/contexts/employee_master/services/employeeDomainService";
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

const STATUS_STYLES = {
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
};

const EMPLOYEE_STATUS_STYLES = {
  Draft: "bg-slate-100 text-slate-700 border-slate-200",
  Pending: "bg-blue-100 text-blue-700 border-blue-200",
  Active: "bg-green-100 text-green-700 border-green-200",
  Suspended: "bg-red-100 text-red-700 border-red-200",
  Retired: "bg-slate-200 text-slate-700 border-slate-300",
  Deputation: "bg-indigo-100 text-indigo-700 border-indigo-200",
};

const getVisibleEmployeeStatus = (profile) => {
  const identityWorkflowStatus = String(profile?.identity_workflow_status || "").trim().toUpperCase();
  const employeeStatus = String(profile?.employee_status || "").trim();

  if (employeeStatus) return formatDirectoryEnumLabel(employeeStatus);
  if (identityWorkflowStatus && identityWorkflowStatus !== "ACTIVE") {
    return identityWorkflowStatus === "DRAFT" ? "Draft" : "Pending";
  }
  return "Active";
};

const formatDisplayDate = (value) => {
  if (!value) return null;
  const str = String(value);
  if (!/^\d{4}-\d{2}-\d{2}/.test(str)) return str;
  const d = new Date(str.slice(0, 10) + "T00:00:00");
  if (Number.isNaN(d.getTime())) return str;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "2-digit", year: "numeric" });
};

const formatCurrency = (value) => {
  if (value === undefined || value === null || value === "") return null;
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) return String(value);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(numericValue);
};

const OFFICIAL_SERVICE_BOOK_STATES = new Set(["VERIFIED", "APPROVED", "LOCKED"]);

const toTimestamp = (value) => {
  if (!value) return 0;
  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? 0 : parsed;
};

const getCurrentServiceEntry = (serviceBook) => {
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

const Field = ({ label, value, mono = false, icon: Icon, className }) => {
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

const hasDisplayValue = (value) => value !== undefined && value !== null && value !== "" && value !== "-";
const normalizeCode = (value) => String(value || "").trim().toUpperCase().replace(/[-\s]+/g, "_");

const resolvePhotoUrl = (photoUrl) => {
  if (!photoUrl) return "";
  if (photoUrl.startsWith("http")) return photoUrl;

  const runtimeHost = typeof window !== "undefined" ? window.location.hostname : "localhost";
  const envBackend = process.env.REACT_APP_BACKEND_URL || "";
  const isRuntimeLocalhost = runtimeHost === "localhost" || runtimeHost === "127.0.0.1";
  let envBackendHost = "";

  if (envBackend) {
    try {
      envBackendHost = new URL(envBackend).hostname;
    } catch {
      envBackendHost = "";
    }
  }

  const isEnvLocalhost = envBackendHost === "localhost" || envBackendHost === "127.0.0.1";
  const backendBase =
    envBackend && !(isEnvLocalhost && !isRuntimeLocalhost)
      ? envBackend
      : `http://${runtimeHost}:8000`;

  return `${backendBase}${photoUrl.startsWith("/") ? "" : "/"}${photoUrl}`;
};

const EmployeeProfile = ({ profile, serviceBook = null, serviceSummary = null, compact = false, className, referenceLabelMaps = {} }) => {
  if (!profile) return null;

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

  return (
    <div className={cn("space-y-6", className)} data-testid="employee-profile">
      {!compact && (
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col gap-5 md:flex-row">
            <div className="flex shrink-0 flex-col gap-3 sm:flex-row">
              <div>
                {profile.photo_url ? (
                  <AuthImage
                    path={profile.photo_url}
                    alt={profile.full_name}
                    className="h-28 w-24 rounded-xl border-2 border-slate-200 object-cover shadow-sm"
                    fallback={
                      <div className="flex h-28 w-24 items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50">
                        <User className="h-10 w-10 text-slate-300" />
                      </div>
                    }
                  />
                ) : (
                  <div className="flex h-28 w-24 items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50">
                    <User className="h-10 w-10 text-slate-300" />
                  </div>
                )}
                <p className="mt-1 text-center text-[10px] uppercase tracking-wider text-slate-400">Photo</p>
              </div>
              {profile.signature_url && (
                <div>
                  <AuthImage
                    path={profile.signature_url}
                    alt="Signature"
                    className="h-28 w-24 rounded-xl border-2 border-slate-200 object-contain bg-white shadow-sm p-1"
                    fallback={
                      <div className="flex h-28 w-24 items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50">
                        <PenLine className="h-8 w-8 text-slate-300" />
                      </div>
                    }
                  />
                  <p className="mt-1 text-center text-[10px] uppercase tracking-wider text-slate-400">Signature</p>
                </div>
              )}
              {!profile.signature_url && (
                <div>
                  <div className="flex h-28 w-24 items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50">
                    <PenLine className="h-8 w-8 text-slate-300" />
                  </div>
                  <p className="mt-1 text-center text-[10px] uppercase tracking-wider text-slate-400">Signature</p>
                </div>
              )}
            </div>

              <div className="min-w-0 flex-1">
                <h2 className="truncate text-2xl font-bold text-slate-900">{profile.full_name}</h2>
                <p className="mt-0.5 text-sm text-slate-500">
                  {currentDesignation !== "-" ? currentDesignation : "No designation"}
                  {" in "}
                  {currentDepartment !== "-" ? currentDepartment : "No department"}
                </p>

                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {profile.employee_code && (
                    <Badge variant="outline" className="font-mono text-xs">
                      {profile.employee_code}
                    </Badge>
                  )}
                  <Badge className={STATUS_STYLES[workflowStatus] || STATUS_STYLES.DRAFT}>
                    {workflowStatusLabel}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {employmentTypeLabel}
                  </Badge>
                  {isRegular && (
                    <Badge className={EMPLOYEE_STATUS_STYLES[employeeStatus] || EMPLOYEE_STATUS_STYLES.Active}>
                      {employeeStatus}
                    </Badge>
                  )}
                </div>

                <div className="mt-4 space-y-1">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Profile Completion</span>
                    <span className="font-medium">{completionPercent}%</span>
                  </div>
                  <Progress value={completionPercent} className="h-1.5" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Briefcase className="h-5 w-5 text-slate-600" />
              {isRegular ? "Current Service Details" : "Current Engagement Details"}
            </CardTitle>
            <CardDescription>
              {isRegular
                ? "Official service position and pay snapshot."
                : "Current non-regular engagement and remuneration snapshot."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isRegular ? (
              <>
                <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
                  <Field label="Current Designation / Post" value={currentDesignation} icon={Briefcase} />
                  <Field label="Current Department" value={currentDepartment} icon={Building2} />
                  <Field label="Current Office / Station" value={currentOffice} icon={MapPin} />
                  <Field label="Employee Code" value={profile.employee_code} mono />
                  <Field label="Employment Type" value={employmentTypeLabel} />
                  <Field label="Service / Cadre" value={currentServiceLabel} />
                  <Field label="Service Group" value={serviceGroupLabel} />
                  <Field label="Mode of Recruitment" value={modeOfRecruitmentLabel} />
                  <Field label="Date of Initial Appointment" value={profile.date_of_initial_engagement} icon={Calendar} />
                  <Field label="Current Posting From" value={formatDisplayDate(currentPostingFrom)} icon={Calendar} />
                </div>

                <Separator />

                <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
                  <Field label="Pay Level" value={currentPayLevel} />
                  <Field label="Current Pay" value={formatCurrency(currentBasicPay)} mono />
                </div>
              </>
            ) : (
              <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
                {nonRegularEngagementFields.map((field) => (
                  <Field
                    key={field.label}
                    label={field.label}
                    value={field.value}
                    icon={field.icon}
                    mono={field.mono}
                    className={field.className}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <User className="h-5 w-5 text-slate-600" />
              Personal Profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
              {(isRegular ? regularPersonalFields : nonRegularPersonalFields).map((field) => (
                <Field
                  key={field.label}
                  label={field.label}
                  value={field.value}
                  icon={field.icon}
                  className={field.className}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {hadPriorEngagement && (
        <Card data-testid="employee-profile-prior-engagement">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Briefcase className="h-5 w-5 text-slate-600" />
              Prior Engagement
            </CardTitle>
            <CardDescription>
              Original non-regular engagement details captured before regularisation.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
              {priorEngagementFields.map((field) => (
                <Field
                  key={field.label}
                  label={field.label}
                  value={field.value}
                  icon={field.icon}
                  mono={field.mono}
                  className={field.className}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <CreditCard className="h-5 w-5 text-slate-600" />
              Official IDs
            </CardTitle>
            <CardDescription>
              Reference identifiers linked to your employee record.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
              <Field
                label="Aadhaar Number"
                value={identifiers.aadhaar_number ? `XXXX-XXXX-${identifiers.aadhaar_number.slice(-4)}` : undefined}
                mono
              />
              <Field label="PAN Number" value={identifiers.pan_number} mono />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Phone className="h-5 w-5 text-slate-600" />
              Contact & Address
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
              <Field label="Mobile (Primary)" value={contact.mobile_primary || profile.mobile_primary} icon={Phone} mono />
              <Field label="Mobile (Alternate)" value={contact.mobile_alternate} icon={Phone} mono />
              <Field label="Email (Official)" value={contact.email_official} icon={Mail} />
              <Field label="Email (Personal)" value={contact.email_personal} icon={Mail} />
            </div>

            {(contact.address_line1 || contact.city || contact.state) && (
              <>
                <Separator />
                <div>
                  <p className="mb-1.5 flex items-center gap-1 text-xs uppercase tracking-wider text-slate-500">
                    <MapPin className="h-3 w-3" />
                    Current Address
                  </p>
                  <p className="font-medium text-slate-900">
                    {[contact.address_line1, contact.address_line2].filter(Boolean).join(", ")}
                  </p>
                  <p className="text-sm text-slate-600">
                    {[contact.city, contact.district, contact.state, contact.pincode].filter(Boolean).join(", ")}
                  </p>
                </div>
              </>
            )}

            {(contact.emergency_name || contact.emergency_phone) && (
              <>
                <Separator />
                <div>
                  <p className="mb-1.5 flex items-center gap-1 text-xs uppercase tracking-wider text-slate-500">
                    <AlertCircle className="h-3 w-3 text-red-500" />
                    Emergency Contact
                  </p>
                  <p className="font-medium text-slate-900">{contact.emergency_name || "-"}</p>
                  <p className="text-sm text-slate-600">
                    {contact.emergency_relation && <span>{contact.emergency_relation} | </span>}
                    {contact.emergency_phone || "-"}
                  </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {(profile.education_at_appointment || profile.professional_qualifications || profile.height_cm || profile.identification_mark_1) && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-5 w-5 text-slate-600" />
              Qualifications & Physical Attributes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2 md:grid-cols-3">
              <Field label="Education at Appointment" value={profile.education_at_appointment} />
              <Field label="Subsequently Acquired" value={profile.education_subsequently_acquired} />
              <Field label="Professional Qualifications" value={profile.professional_qualifications} />
              <Field label="Height" value={profile.height_cm ? `${profile.height_cm} cm` : undefined} />
              <Field label="Identification Mark 1" value={profile.identification_mark_1} />
              <Field label="Identification Mark 2" value={profile.identification_mark_2} />
            </div>
          </CardContent>
        </Card>
      )}

      {isRegular && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <BookOpen className="h-5 w-5 text-slate-600" />
              Service Book Records
            </CardTitle>
            <CardDescription>
              Official service-book entries, family sheet, nominations, and prior service are maintained separately.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-600">
            <p>
              Employee profile edits do not update existing Service Book Part I, II-A, II-B, or III snapshots.
            </p>
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900">
              The current Service Book UI does not expose a correction workflow for Part I, II-A, II-B, or III. Treat those sections as official read-only snapshots; Service Book Records currently handles service-history changes only.
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default EmployeeProfile;
