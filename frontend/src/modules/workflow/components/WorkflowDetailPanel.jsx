import { useEffect, useMemo, useState } from "react";
import {
  getEmployeeIdentitySummary,
  getEmployeeProfileSummary,
} from "@/modules/workflow/model/workQueueGateway";
import { cn, getApiErrorMessage } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Separator } from "@/shared/ui/separator";
import { SheetHeader, SheetTitle } from "@/shared/ui/sheet";
import { Skeleton } from "@/shared/ui/skeleton";
import { Textarea } from "@/shared/ui/textarea";
import {
  ACTION_ICONS,
  STATUS_STYLE,
  TYPE_META,
  formatAge,
  formatWorkflowStatusLabel,
} from "@/modules/workflow/model/workQueue.constants";
import { SlaDot } from "@/modules/workflow/components/workflowQueuePrimitives";
import {
  ArrowUpRight,
  BookOpen,
  Check,
  Clock,
  Edit3,
  RefreshCw,
  Send,
  UserRound,
} from "lucide-react";

const DetailField = ({ label, value, mono = false, colSpan = false }) => (
  <div className={cn("p-2.5 bg-slate-50 rounded-lg border border-slate-100", colSpan && "col-span-2")}>
    <p className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</p>
    <p className={cn("text-sm font-medium text-slate-900 mt-0.5 truncate", mono && "font-mono text-xs")}>
      {value ?? "-"}
    </p>
  </div>
);

const formatDetailValue = (value) => {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) {
    if (value.length === 0) return "-";
    return value.map((item) => (typeof item === "object" ? Object.values(item).filter(Boolean).join(" | ") : String(item))).join(", ");
  }
  if (typeof value === "object") {
    const values = Object.entries(value)
      .filter(([, itemValue]) => itemValue !== null && itemValue !== undefined && itemValue !== "")
      .map(([key, itemValue]) => `${key}: ${itemValue}`);
    return values.length ? values.join(", ") : "-";
  }
  return String(value);
};

const hasDetailValue = (value) => {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim() !== "";
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "object") return Object.values(value).some(hasDetailValue);
  return true;
};

const maskAadhaar = (value) => {
  const digits = String(value || "").replace(/\D/g, "");
  if (!digits) return "-";
  if (digits.length <= 4) return digits;
  return `XXXX XXXX ${digits.slice(-4)}`;
};

const IdentityDetailGrid = ({ fields }) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
    {fields.map((field) => (
      <DetailField
        key={field.label}
        label={field.label}
        value={field.mask === "aadhaar" ? maskAadhaar(field.value) : formatDetailValue(field.value)}
        mono={field.mono}
        colSpan={field.colSpan}
      />
    ))}
  </div>
);

const PROFILE_EXTENSION_GROUPS = [
  {
    title: "Personal Profile",
    fields: [
      ["father_name", "Father's Name"],
      ["mother_name", "Mother's Name"],
      ["nationality", "Nationality"],
      ["religion", "Religion"],
      ["blood_group", "Blood Group"],
      ["category", "Category"],
      ["sub_caste", "Sub Caste"],
      ["date_of_birth_saka", "Date of Birth (Saka)"],
      ["place_of_birth", "Place of Birth"],
      ["height_cm", "Height (cm)"],
      ["identification_marks", "Identification Marks"],
      ["marital_status", "Marital Status"],
      ["spouse_name", "Spouse Name"],
      ["educational_qualifications_initial", "Initial Educational Qualifications"],
      ["educational_qualifications_acquired", "Acquired Educational Qualifications"],
      ["professional_qualifications", "Professional Qualifications"],
    ],
  },
  {
    title: "Contact",
    fields: [
      ["mobile_primary", "Primary Mobile"],
      ["mobile_alternate", "Alternate Mobile"],
      ["email_personal", "Personal Email"],
      ["email_official", "Official Email"],
    ],
  },
  {
    title: "Permanent Address",
    fields: [
      ["address_line1", "Address Line 1"],
      ["address_line2", "Address Line 2"],
      ["city", "City"],
      ["district", "District"],
      ["state", "State"],
      ["pincode", "Pincode"],
    ],
  },
  {
    title: "Present Address",
    fields: [
      ["present_address_line1", "Address Line 1"],
      ["present_address_line2", "Address Line 2"],
      ["present_city", "City"],
      ["present_district", "District"],
      ["present_state", "State"],
      ["present_pincode", "Pincode"],
    ],
  },
  {
    title: "Emergency Contact",
    fields: [
      ["emergency_name", "Name"],
      ["emergency_phone", "Phone"],
      ["emergency_relation", "Relation"],
    ],
  },
  {
    title: "Media",
    fields: [
      ["photo_url", "Photo"],
      ["signature_url", "Signature"],
      ["thumb_impression_url", "Thumb Impression"],
    ],
  },
  {
    title: "Employment Extension",
    fields: [
      ["contract_order_no", "Contract Order No."],
      ["contract_start_date", "Contract Start"],
      ["contract_end_date", "Contract End"],
      ["consolidated_pay", "Consolidated Pay"],
      ["contract_authority", "Contract Authority"],
      ["vendor_agency", "Vendor / Agency"],
      ["renewal_allowed", "Renewal Allowed"],
      ["engagement_order_no", "Engagement Order No."],
      ["muster_roll_number", "Muster Roll Number"],
      ["daily_wage_rate", "Daily Wage Rate"],
      ["engagement_office", "Engagement Office"],
      ["nature_of_work", "Nature of Work"],
      ["expected_duration_days", "Expected Duration"],
      ["deputation_order_no", "Deputation Order No."],
      ["parent_department", "Parent Department"],
      ["parent_designation", "Parent Designation"],
      ["lien_status", "Lien Status"],
      ["deputation_start_date", "Deputation Start"],
      ["deputation_end_date", "Deputation End"],
      ["deputation_allowance_percent", "Deputation Allowance %"],
      ["outsourcing_order_no", "Outsourcing Order No."],
      ["agency_name", "Agency Name"],
      ["agency_contract_number", "Agency Contract Number"],
      ["sla_reference", "SLA Reference"],
      ["monthly_billing_rate", "Monthly Billing Rate"],
      ["role_description", "Role Description"],
    ],
  },
];

const getProfileValue = (profile, fieldName) => (
  profile?.[fieldName]
  ?? profile?.contact?.[fieldName]
  ?? profile?.identifiers?.[fieldName]
);

const ProfileExtensionGroup = ({ title, fields, profile }) => {
  const visibleFields = fields
    .map(([fieldName, label]) => ({ fieldName, label, value: getProfileValue(profile, fieldName) }))
    .filter((field) => hasDetailValue(field.value));

  if (visibleFields.length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">{title}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {visibleFields.map((field) => (
          <DetailField key={field.fieldName} label={field.label} value={formatDetailValue(field.value)} mono={field.fieldName.endsWith("_url")} />
        ))}
      </div>
    </div>
  );
};

const CompletionFlag = ({ label, done }) => (
  <div className="flex items-center gap-1.5 text-xs">
    <div className={cn("w-4 h-4 rounded-full flex items-center justify-center", done ? "bg-green-100 text-green-600" : "bg-slate-100 text-slate-400")}>
      {done ? <Check className="w-2.5 h-2.5" /> : <Clock className="w-2.5 h-2.5" />}
    </div>
    <span className={done ? "text-green-700" : "text-slate-500"}>{label}</span>
  </div>
);

const AuditTimelineSkeleton = () => (
  <div className="space-y-3">
    {Array.from({ length: 4 }).map((_, index) => (
      <div key={index} className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-3 w-28 rounded" />
        </div>
        <Skeleton className="mt-2 h-3 w-32 rounded" />
        <div className="mt-2 flex flex-wrap gap-1.5">
          <Skeleton className="h-4 w-16 rounded-full" />
          <Skeleton className="h-4 w-20 rounded-full" />
          <Skeleton className="h-4 w-14 rounded-full" />
        </div>
      </div>
    ))}
  </div>
);

const WorkflowDetailPanel = ({
  item,
  actions,
  remarks,
  setRemarks,
  onAction,
  actionBusy,
  auditTrail,
  auditLoading,
  onOpenPrimary,
  onOpenSecondary,
  primaryOpenLabel = "Open",
  secondaryOpenLabel = "Open Related",
  showActions,
  onEditPrimary,
  editPrimaryLabel = "Edit",
}) => {
  const meta = TYPE_META[item.type] || TYPE_META.profile;
  const Icon = meta.icon;
  const detail = item.raw || {};
  const safeArr = (v) => (Array.isArray(v) ? v : []);
  const [identityDetails, setIdentityDetails] = useState(null);
  const [identityLoading, setIdentityLoading] = useState(false);
  const [identityError, setIdentityError] = useState("");
  const [profileDetails, setProfileDetails] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState("");

  useEffect(() => {
    if (item.type !== "identity" || !item.employeeId) {
      setIdentityDetails(null);
      setIdentityError("");
      setIdentityLoading(false);
      return undefined;
    }

    let active = true;
    setIdentityLoading(true);
    setIdentityError("");

    getEmployeeIdentitySummary(item.employeeId)
      .then((data) => {
        if (!active) return;
        setIdentityDetails(data || null);
      })
      .catch((error) => {
        if (!active) return;
        setIdentityDetails(null);
        setIdentityError(getApiErrorMessage(error, "Failed to load complete identity details"));
      })
      .finally(() => {
        if (active) setIdentityLoading(false);
      });

    return () => {
      active = false;
    };
  }, [item.employeeId, item.type]);

  useEffect(() => {
    if (item.type !== "profile" || !item.employeeId) {
      setProfileDetails(null);
      setProfileError("");
      setProfileLoading(false);
      return undefined;
    }

    let active = true;
    setProfileLoading(true);
    setProfileError("");

    getEmployeeProfileSummary(item.employeeId)
      .then((data) => {
        if (!active) return;
        setProfileDetails(data || null);
      })
      .catch((error) => {
        if (!active) return;
        setProfileDetails(null);
        setProfileError(getApiErrorMessage(error, "Failed to load complete profile details"));
      })
      .finally(() => {
        if (active) setProfileLoading(false);
      });

    return () => {
      active = false;
    };
  }, [item.employeeId, item.type]);

  const fullIdentity = useMemo(() => {
    if (item.type !== "identity") return detail;
    return { ...detail, ...(identityDetails || {}) };
  }, [detail, identityDetails, item.type]);

  const fullProfile = useMemo(() => {
    if (item.type !== "profile") return detail;
    return { ...detail, ...(profileDetails || {}) };
  }, [detail, item.type, profileDetails]);

  return (
    <div className="space-y-5">
      <SheetHeader>
        <div className="flex items-center gap-3">
          <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center text-white", meta.color)}>
            <Icon className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <SheetTitle className="text-lg truncate">{item.title}</SheetTitle>
            <div className="flex items-center gap-2 mt-1">
              <Badge className={cn("text-[10px] border", STATUS_STYLE[item.statusLabel])}>
                {formatWorkflowStatusLabel(item.statusLabel)}
              </Badge>
              <SlaDot sla={item.sla} />
              <span className="text-xs text-slate-500">{formatAge(item.ageHours)}</span>
            </div>
          </div>
        </div>
      </SheetHeader>

      {showActions && (onEditPrimary || onOpenPrimary || onOpenSecondary) && (
        <div className="flex flex-wrap gap-2">
          {onEditPrimary ? (
            <Button className="flex-1 gap-2 sm:flex-none" onClick={onEditPrimary}>
              <Edit3 className="w-4 h-4" /> {editPrimaryLabel}
            </Button>
          ) : null}
          {onOpenPrimary ? (
            <Button variant="outline" className="flex-1 gap-2 sm:flex-none" onClick={onOpenPrimary}>
              <ArrowUpRight className="w-4 h-4" /> {primaryOpenLabel}
            </Button>
          ) : null}
          {onOpenSecondary ? (
            <Button variant="outline" className="flex-1 gap-2 sm:flex-none" onClick={onOpenSecondary}>
              <BookOpen className="w-4 h-4" /> {secondaryOpenLabel}
            </Button>
          ) : null}
        </div>
      )}

      <Separator />

      {item.type === "identity" && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Identity Details</h4>
          {identityLoading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2" data-testid="identity-details-loading">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={index} className="h-16 rounded-lg" />
              ))}
            </div>
          )}
          {identityError && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
              {identityError}. Showing queued identity summary.
            </div>
          )}
          {!identityLoading && (
            <div className="space-y-3" data-testid="identity-details-complete">
              <IdentityDetailGrid
                fields={[
                  { label: "Employee Code", value: fullIdentity.employee_code, mono: true },
                  { label: "Full Name", value: item.displayName || fullIdentity.full_name, colSpan: true },
                  { label: "Gender", value: fullIdentity.gender },
                  { label: "Date of Birth", value: fullIdentity.date_of_birth },
                  { label: "Aadhaar", value: fullIdentity.aadhaar_number, mask: "aadhaar" },
                ]}
              />

              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Appointment</p>
                <IdentityDetailGrid
                  fields={[
                    { label: "Employment Type", value: fullIdentity.employment_type },
                    { label: "Initial Engagement", value: fullIdentity.date_of_initial_engagement },
                    { label: "Department", value: fullIdentity.current_department_id },
                    { label: "Designation", value: fullIdentity.current_designation_id },
                  ]}
                />
              </div>
            </div>
          )}

          <div className="rounded-lg border border-slate-200 p-3 bg-slate-50/50">
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <UserRound className="w-3.5 h-3.5" />
              Employee identity workflow remains separate from profile extension and service book flows.
            </div>
          </div>
        </div>
      )}

      {/* Profile details */}
      {item.type === "profile" && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Profile Details</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <DetailField label="Name" value={item.displayName || fullProfile.full_name} />
            <DetailField label="Code" value={fullProfile.employee_code} mono />
            <DetailField label="Type" value={fullProfile.employment_type} />
            <DetailField label="Department" value={fullProfile.current_department_id} />
            <DetailField label="Designation" value={fullProfile.current_designation_id} />
            <DetailField label="Office" value={fullProfile.current_office_id} />
          </div>

          {profileLoading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2" data-testid="profile-details-loading">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={index} className="h-16 rounded-lg" />
              ))}
            </div>
          )}
          {profileError && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
              {profileError}. Showing queued profile summary.
            </div>
          )}
          {!profileLoading && (
            <div className="space-y-3" data-testid="profile-extension-details-complete">
              {PROFILE_EXTENSION_GROUPS.map((group) => (
                <ProfileExtensionGroup key={group.title} title={group.title} fields={group.fields} profile={fullProfile} />
              ))}
            </div>
          )}

          <div className="rounded-lg border border-slate-200 p-3 bg-slate-50/50">
            <p className="text-xs font-semibold text-slate-500 mb-2">Completion Status</p>
            <div className="flex gap-3">
              <CompletionFlag label="Employee Section" done={!!fullProfile.employee_section_completed} />
              <CompletionFlag label="Data Entry Section" done={!!fullProfile.data_entry_section_completed} />
            </div>
          </div>
        </div>
      )}

      {/* Service book details */}
      {item.type === "service" && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Service Book Entry</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <DetailField label="Employee" value={item.displayName || detail.full_name} />
            <DetailField label="Code / ID" value={item.employeeCode || detail.employee_code || item.employeeId || detail.employee_id} mono />
            <DetailField label="Entry ID" value={detail.id} mono />
            <DetailField label="Event Type" value={detail.event_type || detail.event_code} />
            <DetailField label="Effective" value={detail.effective_date || detail.effective_from} />
            <DetailField label="Order No." value={detail.order_number} mono />
          </div>
        </div>
      )}

      {/* Leave details */}
      {item.type === "leave" && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Leave Request</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <DetailField label="Leave Type" value={detail.leave_type_code} />
            <DetailField label="Days" value={detail.days_applied} />
            <DetailField label="From" value={detail.from_date} />
            <DetailField label="To" value={detail.to_date} />
            <DetailField label="Reason" value={detail.reason} colSpan />
          </div>
        </div>
      )}

      {/* ESS */}
      {item.type === "ess" && (
        <div className="rounded-lg border border-slate-200 p-3 bg-slate-50/50">
          <p className="text-sm text-slate-700">{item.subtitle}</p>
        </div>
      )}

      {/* Audit Timeline */}
      {item.type === "profile" && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Audit Timeline</h4>
          {auditLoading ? (
            <AuditTimelineSkeleton />
          ) : auditTrail.length === 0 ? (
            <p className="text-xs text-slate-400">No audit entries.</p>
          ) : (
            <div className="relative pl-4 space-y-3 border-l-2 border-slate-200">
              {auditTrail.slice(0, 10).map((entry, i) => {
                const ts = entry.timestamp ? new Date(entry.timestamp).toLocaleString() : "";
                const changed = safeArr(entry.changed_fields);
                return (
                  <div key={i} className="relative">
                    <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-white border-2 border-blue-400" />
                    <div className="text-xs">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-[10px] font-mono">{entry.action}</Badge>
                        <span className="text-slate-400">{ts}</span>
                      </div>
                      {entry.actor_email && (
                        <p className="text-slate-500 mt-0.5">by {entry.actor_email}</p>
                      )}
                      {changed.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {changed.slice(0, 5).map((f) => (
                            <span key={f} className="px-1.5 py-0.5 rounded bg-slate-100 text-[10px] text-slate-600 font-mono">{f}</span>
                          ))}
                          {changed.length > 5 && (
                            <span className="text-[10px] text-slate-400">+{changed.length - 5} more</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      <Separator />

      {/* Action Bar */}
      {actions.length > 0 && (
        <div className="space-y-3">
          {actions.some((a) => a.requiresRemarks) && (
            <div>
              <label className="text-xs font-medium text-slate-700">Remarks *</label>
              <Textarea
                className="mt-1"
                rows={3}
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="Add remarks for this action..."
              />
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            {actions.map((action) => {
              const ActionIcon = ACTION_ICONS[action.id] || Send;
              return (
                <Button
                  key={action.id}
                  variant={action.variant === "destructive" ? "outline" : "default"}
                  className={cn(
                    "gap-1.5 flex-1 min-w-[100px]",
                    action.variant === "destructive" && "text-red-600 hover:text-red-700 border-red-200"
                  )}
                  onClick={() => onAction(item, action.id)}
                  disabled={actionBusy || action.disabled}
                  title={action.disabledReason || ""}
                >
                  <ActionIcon className="w-4 h-4" />
                  {action.label}
                </Button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowDetailPanel;
