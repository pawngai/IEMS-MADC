import { CheckCircle2, Circle } from "lucide-react";
import { OPENING_STEPS } from "@/contexts/service_book/opening/model/openingSteps";
import { cn } from "@/shared/lib/utils";

const OpeningStepper = ({ completion, activeStepId, onStepSelect }) => (
  <div className="grid grid-cols-1 md:grid-cols-4 gap-2" data-testid="opening-stepper" role="tablist" aria-label="Service Book opening parts">
    {OPENING_STEPS.map((step) => {
      const done = Boolean(completion?.byStep?.[step.id]);
      const selected = step.id === activeStepId;
      const Icon = done ? CheckCircle2 : Circle;
      return (
        <button
          key={step.id}
          type="button"
          id={`opening-tab-${step.id}`}
          role="tab"
          aria-selected={selected}
          aria-controls={`opening-panel-${step.id}`}
          data-testid={`opening-step-tab-${step.id}`}
          className={cn(
            "rounded-md border bg-white px-3 py-2 flex items-start gap-2 text-left transition-colors",
            selected ? "border-slate-900 ring-1 ring-slate-900" : "border-slate-200 hover:border-slate-300"
          )}
          onClick={() => onStepSelect?.(step.id)}
        >
          <Icon className={`w-4 h-4 mt-0.5 ${done ? "text-emerald-600" : "text-slate-400"}`} />
          <div>
            <p className="text-sm font-semibold text-slate-900">{step.label}</p>
            <p className="text-xs text-slate-500">{step.title}</p>
          </div>
        </button>
      );
    })}
  </div>
);

export default OpeningStepper;
