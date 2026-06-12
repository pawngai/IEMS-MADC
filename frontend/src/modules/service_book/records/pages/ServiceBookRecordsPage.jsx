import { Link } from "react-router-dom";
import { useServiceBookRecordsPageState } from "@/modules/service_book/records/hooks/useServiceBookRecordsPageState";
import ServiceRecordTimeline from "@/modules/service_book/records/components/ServiceRecordTimeline";
import RecordServiceBookRecordDialog from "@/modules/service_book/records/components/RecordServiceBookRecordDialog";
import CorrectServiceBookRecordDialog from "@/modules/service_book/records/components/CorrectServiceBookRecordDialog";
import VoidServiceBookRecordDialog from "@/modules/service_book/records/components/VoidServiceBookRecordDialog";
import AttachDocumentDialog from "@/modules/service_book/records/components/AttachDocumentDialog";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { CardSkeleton } from "@/shared/ui/skeletons";
import {
  GitBranch,
  Plus,
  RefreshCw,
  User,
  AlertCircle,
  ArrowLeft,
} from "lucide-react";

const ServiceBookRecordsPage = () => {
  const {
    targetEmployeeId,
    employeeName,
    employeeCode,
    events,
    loading,
    error,
    loadEvents,
    showRecordDialog,
    setShowRecordDialog,
    correctTarget,
    setCorrectTarget,
    voidTarget,
    setVoidTarget,
    attachTarget,
    setAttachTarget,
    canCreate,
    canCorrectOrVoid,
    canAttachDoc,
    serviceBookRecordsEligible,
    handleRecordSuccess,
    handleCorrectSuccess,
    handleVoidSuccess,
    handleAttachSuccess,
  } = useServiceBookRecordsPageState();

  const headerEmployeeName = employeeName || targetEmployeeId;
  const headerEmployeeCode = employeeCode || (employeeName ? targetEmployeeId : null);

  if (!targetEmployeeId) {
    return (
      <>
        <div className="text-center py-12">
          <User className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50" />
          <h2 className="text-xl font-semibold mb-2">No Employee Profile Linked</h2>
          <p className="text-muted-foreground">
            Your account is not linked to an employee profile.
          </p>
        </div>
      </>
    );
  }

  if (serviceBookRecordsEligible === false) {
    return (
      <>
        <div className="max-w-4xl mx-auto space-y-6 animate-fade-in" data-testid="service-records-not-applicable">
          <Card>
            <CardHeader className="pb-3">
              <Link
                to={`/employees/${targetEmployeeId}`}
                className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-2 w-fit"
              >
                <ArrowLeft className="w-3 h-3" />
                Back to Employee
              </Link>
              <CardTitle className="text-2xl font-bold text-foreground">Service Book Records Not Applicable</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>Service Book records are only maintained for REGULAR employees.</p>
              <p>Use the employee file to manage identity and profile extension for this employment type.</p>
            </CardContent>
          </Card>
        </div>
      </>
    );
  }

  return (
    <>
      <div
        className="max-w-5xl mx-auto space-y-6 animate-fade-in"
        data-testid="service-records-page"
      >
        {/* Header */}
        <Card>
          <CardHeader className="pb-3">
            <Link
              to={`/employees/${targetEmployeeId}`}
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-2 w-fit"
            >
              <ArrowLeft className="w-3 h-3" />
              Back to Employee
            </Link>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                  Event Stream
                </p>
                <CardTitle className="text-2xl font-bold text-foreground flex items-center gap-2">
                  <GitBranch className="w-5 h-5" />
                  Service Book Records
                </CardTitle>
                <p className="text-sm font-medium text-foreground mt-1">
                  {headerEmployeeName}
                </p>
                {headerEmployeeCode && (
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <Badge variant="outline" className="bg-surface-container-low font-mono text-xs">
                      {headerEmployeeCode}
                    </Badge>
                  </div>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadEvents}
                  disabled={loading}
                  className="gap-1"
                >
                  <RefreshCw
                    className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
                  />
                  Refresh
                </Button>
                {canCreate && (
                  <Button
                    size="sm"
                    onClick={() => setShowRecordDialog(true)}
                    className="gap-1"
                    data-testid="record-service-record-btn"
                  >
                    <Plus className="w-4 h-4" />
                    Record Event
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {events.length > 0 && (
              <div className="flex gap-2 flex-wrap">
                <Badge variant="outline" className="bg-surface-container-low">
                  {events.length} event{events.length !== 1 ? "s" : ""}
                </Badge>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Content */}
        {loading && (
          <div className="space-y-4">
            <CardSkeleton lines={3} />
            <CardSkeleton lines={4} />
            <CardSkeleton lines={2} />
          </div>
        )}

        {error && !loading && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="py-6">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <div>
                  <p className="font-medium text-red-800">
                    Failed to load Service Book records
                  </p>
                  <p className="text-sm text-red-600 mt-1">{error}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadEvents}
                  className="ml-auto"
                >
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {!loading && !error && events.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <GitBranch className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
              <h3 className="font-semibold text-foreground mb-1">
                No Service Book Records
              </h3>
              <p className="text-sm text-muted-foreground">
                No Service Book records have been recorded for this employee yet.
              </p>
              {canCreate && (
                <Button
                  className="mt-4 gap-1"
                  onClick={() => setShowRecordDialog(true)}
                >
                  <Plus className="w-4 h-4" />
                  Record First Event
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {!loading && !error && events.length > 0 && (
          <ServiceRecordTimeline
            events={events}
            canCorrect={canCorrectOrVoid}
            canVoid={canCorrectOrVoid}
            canAttach={canAttachDoc}
            onCorrect={setCorrectTarget}
            onVoid={setVoidTarget}
            onAttach={setAttachTarget}
          />
        )}
      </div>

      {/* Dialogs */}
      {showRecordDialog && (
        <RecordServiceBookRecordDialog
          employeeId={targetEmployeeId}
          onSuccess={handleRecordSuccess}
          onClose={() => setShowRecordDialog(false)}
        />
      )}
      {correctTarget && (
        <CorrectServiceBookRecordDialog
          event={correctTarget}
          onSuccess={handleCorrectSuccess}
          onClose={() => setCorrectTarget(null)}
        />
      )}
      {voidTarget && (
        <VoidServiceBookRecordDialog
          event={voidTarget}
          onSuccess={handleVoidSuccess}
          onClose={() => setVoidTarget(null)}
        />
      )}
      {attachTarget && (
        <AttachDocumentDialog
          event={attachTarget}
          employeeCode={employeeCode}
          onSuccess={handleAttachSuccess}
          onClose={() => setAttachTarget(null)}
        />
      )}
    </>
  );
};

export default ServiceBookRecordsPage;
