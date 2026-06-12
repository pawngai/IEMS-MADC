import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Separator } from "@/shared/ui/separator";
import { Progress } from "@/shared/ui/progress";
import { AuthImage } from "@/platform/auth/AuthImage";
import {
  AlertCircle,
  BookOpen,
  Building2,
  Briefcase,
  Calendar,
  CreditCard,
  FileText,
  Mail,
  MapPin,
  PenLine,
  Phone,
  User,
} from "lucide-react";
import {
  EMPLOYEE_STATUS_STYLES,
  Field,
  STATUS_STYLES,
  formatCurrency,
  formatDisplayDate,
} from "@/modules/employee_master/components/EmployeeProfileSummary.model";

export const EmployeeProfileHeaderCard = ({
  profile,
  currentDesignation,
  currentDepartment,
  workflowStatus,
  workflowStatusLabel,
  employmentTypeLabel,
  isRegular,
  employeeStatus,
  completionPercent,
}) => (
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
);

export const EmployeeProfileServiceCard = ({
  isRegular,
  currentDesignation,
  currentDepartment,
  currentOffice,
  profile,
  employmentTypeLabel,
  currentServiceLabel,
  serviceGroupLabel,
  modeOfRecruitmentLabel,
  currentPostingFrom,
  currentPayLevel,
  currentBasicPay,
  nonRegularEngagementFields,
}) => (
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
);

export const EmployeeProfilePersonalCard = ({ isRegular, regularPersonalFields, nonRegularPersonalFields }) => (
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
);

export const EmployeeProfilePriorEngagementCard = ({ fields }) => (
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
        {fields.map((field) => (
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
);

export const EmployeeProfileIdsCard = ({ identifiers }) => (
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
);

export const EmployeeProfileContactCard = ({ profile, contact }) => (
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
);

export const EmployeeProfileQualificationsCard = ({ profile }) => {
  if (!(profile.education_at_appointment || profile.professional_qualifications || profile.height_cm || profile.identification_mark_1)) {
    return null;
  }

  return (
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
  );
};

export const EmployeeProfileServiceBookNotice = () => (
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
);
