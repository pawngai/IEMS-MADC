import { cn } from "@/shared/lib/utils";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/shared/ui/tooltip";
import { SECTION_META, STAGE_COLORS } from "@/contexts/workflow/model/pipelineConstants";
import {
  CheckCircle2,
  Circle,
  XCircle,
  ArrowRight,
  AlertCircle,
  Clock,
  ShieldCheck,
  Lock,
} from "lucide-react";

/* ==================== SECTION COMPLETION CARD ==================== */

export const SectionCompletionCard = ({ sectionKey, data }) => {
  const meta = SECTION_META[sectionKey] || { label: sectionKey, icon: Circle, color: "slate" };
  const percent = data?.percent || 0;
  const filled = data?.filled || 0;
  const total = data?.total || 0;
  const isComplete = percent === 100;

  return (
    <div
      className={cn(
        "rounded-lg border p-3 transition-all duration-300",
        isComplete
          ? "bg-green-50/60 border-green-200"
          : percent > 0
          ? "bg-white border-slate-200"
          : "bg-slate-50/50 border-dashed border-slate-200"
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors",
            isComplete ? "bg-green-100" : `bg-${meta.color}-50`
          )}
        >
          {isComplete ? (
            <CheckCircle2 className="w-4 h-4 text-green-600" />
          ) : (
            <meta.icon className={cn("w-4 h-4", `text-${meta.color}-500`)} />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-700 truncate">{meta.label}</span>
            <span
              className={cn(
                "text-[10px] font-bold tabular-nums",
                isComplete ? "text-green-600" : percent > 0 ? "text-slate-600" : "text-slate-400"
              )}
            >
              {filled}/{total}
            </span>
          </div>
          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500 ease-out",
                isComplete ? "bg-green-500" : percent >= 50 ? "bg-blue-500" : "bg-amber-400"
              )}
              style={{ width: `${percent}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

/* ==================== PIPELINE STEP NODE ==================== */

export const PipelineStepNode = ({ stage, isActive, isCompleted, isRejected }) => {
  const colors = STAGE_COLORS[stage.color] || STAGE_COLORS.slate;
  const Icon = stage.icon;

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex flex-col items-center relative group cursor-default">
            <div
              className={cn(
                "w-10 h-10 rounded-full flex items-center justify-center relative z-10 transition-all duration-300 border-2",
                isCompleted && "border-transparent",
                isActive && !isRejected && cn("border-2 shadow-md", colors.ring, colors.bg),
                isActive && isRejected && "border-red-300 bg-red-50 shadow-md ring-2 ring-red-200",
                !isActive && isCompleted && cn(colors.bgSolid, "border-transparent shadow-sm"),
                !isActive && !isCompleted && "bg-slate-100 border-slate-200"
              )}
            >
              {isCompleted && !isActive ? (
                <CheckCircle2 className="w-5 h-5 text-white" />
              ) : isActive && isRejected ? (
                <XCircle className="w-5 h-5 text-red-500" />
              ) : (
                <Icon
                  className={cn(
                    "w-5 h-5 transition-colors",
                    isActive ? colors.text : isCompleted ? "text-white" : "text-slate-400"
                  )}
                />
              )}
              {isActive && !isRejected && (
                <span className={cn(
                  "absolute inset-0 rounded-full animate-ping opacity-20",
                  colors.bgSolid
                )} />
              )}
            </div>
            <span
              className={cn(
                "text-[10px] font-medium mt-1.5 text-center leading-tight transition-colors",
                isActive ? (isRejected ? "text-red-600 font-semibold" : cn(colors.text, "font-semibold")) : isCompleted ? "text-slate-700" : "text-slate-400"
              )}
            >
              {isRejected && isActive ? "Rejected" : stage.label}
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p className="font-medium">{stage.label}</p>
          <p className="text-[10px] opacity-80">{isRejected && isActive ? "Profile was returned for corrections" : stage.description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

/* ==================== CONNECTOR LINE ==================== */

export const ConnectorLine = ({ isCompleted, color = "slate" }) => {
  const colors = STAGE_COLORS[color] || STAGE_COLORS.slate;
  return (
    <div className="flex-1 flex items-center px-0.5 -mt-5">
      <div
        className={cn(
          "h-0.5 w-full rounded-full transition-all duration-500",
          isCompleted ? colors.bgSolid : "bg-slate-200"
        )}
      />
    </div>
  );
};

/* ==================== NEXT ACTION HINT ==================== */

export const NextActionHint = ({ workflowStatus, overallPercent, employeeSectionDone, dataEntrySectionDone }) => {
  let message = "";
  let icon = ArrowRight;
  let bgColor = "bg-blue-50 border-blue-200";
  let textColor = "text-blue-700";
  let iconColor = "text-blue-500";

  switch (workflowStatus) {
    case "DRAFT":
      if (overallPercent < 100) {
        message = `Complete all sections (${overallPercent}% done) before submitting for verification.`;
        icon = AlertCircle;
        bgColor = "bg-amber-50 border-amber-200";
        textColor = "text-amber-700";
        iconColor = "text-amber-500";
      } else if (!employeeSectionDone || !dataEntrySectionDone) {
        message = "All fields filled. Mark sections complete, then submit for verification.";
        icon = Clock;
      } else {
        message = "Profile is ready! Submit for verification to advance the pipeline.";
        icon = CheckCircle2;
        bgColor = "bg-green-50 border-green-200";
        textColor = "text-green-700";
        iconColor = "text-green-500";
      }
      break;
    case "SUBMITTED":
      message = "Profile submitted. Awaiting verification by an authorized officer.";
      icon = Clock;
      break;
    case "VERIFIED":
      message = "Verified by officer. Awaiting approval from the approving authority.";
      icon = ShieldCheck;
      bgColor = "bg-purple-50 border-purple-200";
      textColor = "text-purple-700";
      iconColor = "text-purple-500";
      break;
    case "APPROVED":
      message = "Approved! Ready to be locked as the immutable record.";
      icon = Lock;
      bgColor = "bg-green-50 border-green-200";
      textColor = "text-green-700";
      iconColor = "text-green-500";
      break;
    case "LOCKED":
      message = "Profile is locked and finalized. No further changes allowed.";
      icon = Lock;
      bgColor = "bg-green-50 border-green-200";
      textColor = "text-green-700";
      iconColor = "text-green-500";
      break;
    case "REJECTED":
      message = "Profile was rejected. Review the feedback and correct the issues, then resubmit.";
      icon = XCircle;
      bgColor = "bg-red-50 border-red-200";
      textColor = "text-red-700";
      iconColor = "text-red-500";
      break;
    default:
      message = "Update the profile to continue.";
  }

  const HintIcon = icon;
  return (
    <div className={cn("flex items-start gap-2.5 rounded-lg border px-3 py-2.5 transition-colors", bgColor)}>
      <HintIcon className={cn("w-4 h-4 mt-0.5 flex-shrink-0", iconColor)} />
      <p className={cn("text-xs leading-relaxed", textColor)}>{message}</p>
    </div>
  );
};
