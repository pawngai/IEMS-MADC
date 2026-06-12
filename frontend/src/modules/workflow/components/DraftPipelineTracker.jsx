import { useState, useEffect, useMemo } from "react";
import { cn } from "@/shared/lib/utils";
import { getProfileCompletion } from "@/modules/workflow/model/workQueueGateway";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileText,
  Loader2,
} from "lucide-react";

import { PIPELINE_STAGES } from "@/modules/workflow/model/pipelineConstants";
import {
  SectionCompletionCard,
  PipelineStepNode,
  ConnectorLine,
  NextActionHint,
} from "@/modules/workflow/components/pipelinePrimitives";

/**
 * DraftPipelineTracker - Progressive UI showing the profile workflow pipeline
 * and section-level completion for DRAFT profiles.
 */
const DraftPipelineTracker = ({ profile, className, compact = false, onNavigateToSection }) => {
  const [completion, setCompletion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const workflowStatus = profile?.workflow_status || "DRAFT";
  const employeeId = profile?.employee_id || profile?.id;
  const isRejected = workflowStatus === "REJECTED";

  const activeStageIndex = useMemo(() => {
    if (isRejected) return 0;
    const idx = PIPELINE_STAGES.findIndex((s) => s.key === workflowStatus);
    return idx >= 0 ? idx : 0;
  }, [workflowStatus, isRejected]);

  useEffect(() => {
    if (!employeeId) return;
    if (workflowStatus !== "DRAFT" && workflowStatus !== "REJECTED") {
      setCompletion(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const data = await getProfileCompletion(employeeId);
        if (!cancelled) setCompletion(data);
      } catch {
        if (!cancelled) setCompletion(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [employeeId, workflowStatus]);

  const overallPercent = completion?.overall_percent ?? 0;
  const sections = completion?.sections || {};
  const employeeSectionDone = completion?.employee_section_completed ?? !!profile?.employee_section_completed;
  const dataEntrySectionDone = completion?.data_entry_section_completed ?? !!profile?.data_entry_section_completed;
  const showSectionBreakdown = (workflowStatus === "DRAFT" || isRejected) && !compact;

  if (!profile) return null;

  return (
    <Card className={cn("overflow-hidden", className)} data-testid="draft-pipeline-tracker">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="w-5 h-5 text-slate-600" />
            Profile Pipeline
          </CardTitle>
          <Badge
            className={cn(
              "text-xs",
              isRejected
                ? "bg-red-100 text-red-700"
                : workflowStatus === "LOCKED"
                ? "bg-green-100 text-green-700"
                : "bg-slate-100 text-slate-700"
            )}
          >
            {workflowStatus}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Pipeline Stepper */}
        <div className="flex items-start justify-between gap-0">
          {PIPELINE_STAGES.map((stage, idx) => (
            <div key={stage.key} className="contents">
              <PipelineStepNode
                stage={stage}
                isActive={idx === activeStageIndex}
                isCompleted={idx < activeStageIndex}
                isRejected={isRejected && idx === 0}
              />
              {idx < PIPELINE_STAGES.length - 1 && (
                <ConnectorLine
                  isCompleted={idx < activeStageIndex}
                  color={PIPELINE_STAGES[Math.min(idx + 1, activeStageIndex)].color}
                />
              )}
            </div>
          ))}
        </div>

        {/* Overall Progress (for DRAFT/REJECTED) */}
        {(workflowStatus === "DRAFT" || isRejected) && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-600">Overall Completion</span>
              {loading ? (
                <Loader2 className="w-3.5 h-3.5 text-slate-400 animate-spin" />
              ) : (
                <span
                  className={cn(
                    "text-sm font-bold tabular-nums",
                    overallPercent === 100
                      ? "text-green-600"
                      : overallPercent >= 60
                      ? "text-blue-600"
                      : "text-amber-600"
                  )}
                >
                  {overallPercent}%
                </span>
              )}
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-700 ease-out",
                  overallPercent === 100
                    ? "bg-green-500"
                    : overallPercent >= 60
                    ? "bg-blue-500"
                    : "bg-amber-400"
                )}
                style={{ width: `${overallPercent}%` }}
              />
            </div>

            {/* Section Tracking Badges */}
            <div className="flex gap-2 flex-wrap">
              <div className="flex items-center gap-1.5">
                <span className={cn("w-2 h-2 rounded-full", employeeSectionDone ? "bg-green-500" : "bg-amber-400")} />
                <span className="text-[10px] text-slate-500">Employee Section: {employeeSectionDone ? "Done" : "Pending"}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={cn("w-2 h-2 rounded-full", dataEntrySectionDone ? "bg-green-500" : "bg-amber-400")} />
                <span className="text-[10px] text-slate-500">Data Entry Section: {dataEntrySectionDone ? "Done" : "Pending"}</span>
              </div>
            </div>
          </div>
        )}

        {/* Section Breakdown (Expandable) */}
        {showSectionBreakdown && Object.keys(sections).length > 0 && (
          <div>
            <button
              onClick={() => setExpanded((v) => !v)}
              className="flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 transition-colors w-full"
            >
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              {expanded ? "Hide" : "Show"} Section Details
              {!expanded && (
                <span className="ml-auto text-[10px] text-slate-400">
                  {Object.values(sections).filter((s) => s.percent === 100).length}/{Object.keys(sections).length} complete
                </span>
              )}
            </button>

            {expanded && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3 animate-in slide-in-from-top-2 duration-200">
                {Object.entries(sections).map(([key, data]) => (
                  <div
                    key={key}
                    className={cn(
                      onNavigateToSection && data.percent < 100 && "cursor-pointer hover:ring-1 hover:ring-blue-300 rounded-lg transition-all"
                    )}
                    onClick={() => {
                      if (onNavigateToSection && data.percent < 100) {
                        onNavigateToSection(key);
                      }
                    }}
                  >
                    <SectionCompletionCard sectionKey={key} data={data} />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Next Action Hint */}
        <NextActionHint
          workflowStatus={workflowStatus}
          overallPercent={overallPercent}
          employeeSectionDone={employeeSectionDone}
          dataEntrySectionDone={dataEntrySectionDone}
        />

        {/* Timestamps (for non-DRAFT) */}
        {workflowStatus !== "DRAFT" && (
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-slate-400 pt-1 border-t border-slate-100">
            {profile.submitted_at && (
              <span>Submitted: {new Date(profile.submitted_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</span>
            )}
            {profile.verified_at && (
              <span>Verified: {new Date(profile.verified_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</span>
            )}
            {profile.approved_at && (
              <span>Approved: {new Date(profile.approved_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</span>
            )}
            {profile.locked_at && (
              <span>Locked: {new Date(profile.locked_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DraftPipelineTracker;
