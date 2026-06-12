import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { OPENING_STEPS } from "@/modules/service_book/opening/model/openingSteps";

const OpeningReviewPanel = ({ completion }) => (
  <Card data-testid="opening-review-panel">
    <CardHeader><CardTitle className="text-lg">Review</CardTitle></CardHeader>
    <CardContent className="space-y-2">
      {OPENING_STEPS.map((step) => (
        <div key={step.id} className="flex items-center justify-between gap-3 text-sm">
          <span className="text-slate-600">{`${step.label} - ${step.title}`}</span>
          <span className={completion?.byStep?.[step.id] ? "font-medium text-emerald-700" : "font-medium text-red-700"}>
            {completion?.byStep?.[step.id] ? "Complete" : "Incomplete"}
          </span>
        </div>
      ))}
    </CardContent>
  </Card>
);

export default OpeningReviewPanel;
