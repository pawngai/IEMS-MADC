import { AlertCircle, CheckCircle2 } from "lucide-react";
import { Card, CardContent } from "@/shared/ui/card";

const OpeningEligibilityCard = ({ eligibility }) => {
  const eligible = eligibility?.eligible !== false;
  const Icon = eligible ? CheckCircle2 : AlertCircle;
  return (
    <Card className={eligible ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50"} data-testid="opening-eligibility-card">
      <CardContent className="py-4 flex items-start gap-3">
        <Icon className={`w-5 h-5 mt-0.5 ${eligible ? "text-emerald-600" : "text-red-600"}`} />
        <div>
          <p className={`text-sm font-semibold ${eligible ? "text-emerald-900" : "text-red-900"}`}>
            {eligible ? "Eligible for Service Book Opening" : "Service Book Opening Not Applicable"}
          </p>
          <p className={`text-sm mt-1 ${eligible ? "text-emerald-700" : "text-red-700"}`}>
            {eligibility?.reason}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default OpeningEligibilityCard;
