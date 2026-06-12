import { cn } from "@/shared/lib/utils";
import { buildEmployeeProfileSummaryModel } from "@/modules/employee_master/components/EmployeeProfileSummary.model";
import {
  EmployeeProfileContactCard,
  EmployeeProfileHeaderCard,
  EmployeeProfileIdsCard,
  EmployeeProfilePersonalCard,
  EmployeeProfilePriorEngagementCard,
  EmployeeProfileQualificationsCard,
  EmployeeProfileServiceBookNotice,
  EmployeeProfileServiceCard,
} from "@/modules/employee_master/components/EmployeeProfileSummary.sections";

const EmployeeProfile = ({ profile, serviceBook = null, serviceSummary = null, compact = false, className, referenceLabelMaps = {} }) => {
  if (!profile) return null;

  const summary = buildEmployeeProfileSummaryModel({
    profile,
    serviceBook,
    serviceSummary,
    referenceLabelMaps,
  });

  return (
    <div className={cn("space-y-6", className)} data-testid="employee-profile">
      {!compact && (
        <EmployeeProfileHeaderCard
          profile={profile}
          currentDesignation={summary.currentDesignation}
          currentDepartment={summary.currentDepartment}
          workflowStatus={summary.workflowStatus}
          workflowStatusLabel={summary.workflowStatusLabel}
          employmentTypeLabel={summary.employmentTypeLabel}
          isRegular={summary.isRegular}
          employeeStatus={summary.employeeStatus}
          completionPercent={summary.completionPercent}
        />
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <EmployeeProfileServiceCard
          isRegular={summary.isRegular}
          currentDesignation={summary.currentDesignation}
          currentDepartment={summary.currentDepartment}
          currentOffice={summary.currentOffice}
          profile={profile}
          employmentTypeLabel={summary.employmentTypeLabel}
          currentServiceLabel={summary.currentServiceLabel}
          serviceGroupLabel={summary.serviceGroupLabel}
          modeOfRecruitmentLabel={summary.modeOfRecruitmentLabel}
          currentPostingFrom={summary.currentPostingFrom}
          currentPayLevel={summary.currentPayLevel}
          currentBasicPay={summary.currentBasicPay}
          nonRegularEngagementFields={summary.nonRegularEngagementFields}
        />

        <EmployeeProfilePersonalCard
          isRegular={summary.isRegular}
          regularPersonalFields={summary.regularPersonalFields}
          nonRegularPersonalFields={summary.nonRegularPersonalFields}
        />
      </div>

      {summary.hadPriorEngagement && (
        <EmployeeProfilePriorEngagementCard fields={summary.priorEngagementFields} />
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <EmployeeProfileIdsCard identifiers={summary.identifiers} />
        <EmployeeProfileContactCard profile={profile} contact={summary.contact} />
      </div>

      <EmployeeProfileQualificationsCard profile={profile} />

      {summary.isRegular && <EmployeeProfileServiceBookNotice />}
    </div>
  );
};

export default EmployeeProfile;
