import { useState } from "react";
import { AlertCircle, User } from "lucide-react";
import { Card, CardContent } from "@/shared/ui/card";
import { CardSkeleton } from "@/shared/ui/skeletons";
import { isOpeningEditable } from "@/contexts/service_book/opening/model/openingStatus";
import { OPENING_STEPS } from "@/contexts/service_book/opening/model/openingSteps";
import { useServiceBookOpeningPageState } from "@/contexts/service_book/opening/hooks/useServiceBookOpeningPageState";
import OpeningHeader from "@/contexts/service_book/opening/components/OpeningHeader";
import OpeningStepper from "@/contexts/service_book/opening/components/OpeningStepper";
import OpeningEligibilityCard from "@/contexts/service_book/opening/components/OpeningEligibilityCard";
import OpeningPartIForm from "@/contexts/service_book/opening/components/OpeningPartIForm";
import OpeningPartIIAForm from "@/contexts/service_book/opening/components/OpeningPartIIAForm";
import OpeningPartIIBForm from "@/contexts/service_book/opening/components/OpeningPartIIBForm";
import OpeningPartIIIForm from "@/contexts/service_book/opening/components/OpeningPartIIIForm";
import OpeningReviewPanel from "@/contexts/service_book/opening/components/OpeningReviewPanel";
import OpeningWorkflowActions from "@/contexts/service_book/opening/components/OpeningWorkflowActions";

const ServiceBookOpeningPage = () => {
  const [activeStepId, setActiveStepId] = useState(OPENING_STEPS[0].id);
  const state = useServiceBookOpeningPageState();
  const {
    targetEmployeeId,
    employeeName,
    employeeCode,
    employeeFileId,
    draft,
    loading,
    saving,
    uploadingDocument,
    acting,
    error,
    eligibility,
    status,
    completion,
    permissions,
    remarks,
    setRemarks,
    updatePart,
    saveDraft,
    runWorkflowAction,
    uploadDocument,
    reload,
  } = state;

  if (!targetEmployeeId) {
    return (
      <>
        <div className="text-center py-12">
          <User className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50" />
          <h2 className="text-xl font-semibold mb-2">No Employee Profile Linked</h2>
          <p className="text-muted-foreground">Your account is not linked to an employee profile.</p>
        </div>
      </>
    );
  }

  const disabled = !permissions.canUpdate || !isOpeningEditable(status);
  const isFinalStep = activeStepId === OPENING_STEPS[OPENING_STEPS.length - 1]?.id;
  const formProps = {
    documents: draft?.documents || [],
    uploading: uploadingDocument,
    onUpload: uploadDocument,
  };

  const renderActiveForm = () => {
    if (activeStepId === "part_iia") {
      return <OpeningPartIIAForm value={draft?.parts?.part_iia} onChange={(values) => updatePart("part_iia", values)} disabled={disabled} {...formProps} />;
    }

    if (activeStepId === "part_iib") {
      return <OpeningPartIIBForm value={draft?.parts?.part_iib} onChange={(values) => updatePart("part_iib", values)} disabled={disabled} {...formProps} />;
    }

    if (activeStepId === "part_iii") {
      return <OpeningPartIIIForm value={draft?.parts?.part_iii} onChange={(values) => updatePart("part_iii", values)} disabled={disabled} {...formProps} />;
    }

    return <OpeningPartIForm value={draft?.parts?.part_i} onChange={(values) => updatePart("part_i", values)} disabled={disabled} {...formProps} />;
  };

  const renderActiveTabPanel = () => (
    <div id={`opening-panel-${activeStepId}`} role="tabpanel" aria-labelledby={`opening-tab-${activeStepId}`} className="space-y-4">
      {renderActiveForm()}
    </div>
  );

  return (
    <>
      <div className="max-w-5xl mx-auto space-y-6 animate-fade-in" data-testid="service-book-opening-page">
        <OpeningHeader
          employeeId={loading ? employeeFileId : employeeFileId || targetEmployeeId}
          employeeName={employeeName}
          employeeCode={employeeCode}
          status={status}
          loading={loading}
          onRefresh={reload}
        />

        {loading && (
          <div className="space-y-4">
            <CardSkeleton lines={3} />
            <CardSkeleton lines={4} />
          </div>
        )}

        {error && !loading && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="py-6 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <p className="text-sm text-red-700">{error}</p>
            </CardContent>
          </Card>
        )}

        {!loading && !error && (
          <>
            <OpeningEligibilityCard eligibility={eligibility} />
            {eligibility.eligible && (
              <>
                <OpeningStepper completion={completion} activeStepId={activeStepId} onStepSelect={setActiveStepId} />
                {renderActiveTabPanel()}
                {isFinalStep && (
                  <div className="space-y-4">
                    <OpeningReviewPanel completion={completion} />
                    <OpeningWorkflowActions
                      completion={completion}
                      permissions={permissions}
                      saving={saving}
                      acting={acting}
                      remarks={remarks}
                      onRemarksChange={setRemarks}
                      onSave={saveDraft}
                      onSubmit={() => runWorkflowAction("submit")}
                      onVerify={() => runWorkflowAction("verify")}
                      onApprove={() => runWorkflowAction("approve")}
                    />
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </>
  );
};

export default ServiceBookOpeningPage;
