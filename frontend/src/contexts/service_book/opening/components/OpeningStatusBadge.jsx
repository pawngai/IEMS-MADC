import { Badge } from "@/shared/ui/badge";
import { OPENING_STATUS_LABELS, normalizeOpeningStatus } from "@/contexts/service_book/opening/model/openingStatus";

const STATUS_CLASSES = {
  NOT_STARTED: "bg-slate-100 text-slate-700",
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-emerald-100 text-emerald-700",
  REJECTED: "bg-red-100 text-red-700",
};

const OpeningStatusBadge = ({ status }) => {
  const normalized = normalizeOpeningStatus(status);
  return (
    <Badge variant="outline" className={STATUS_CLASSES[normalized] || "bg-slate-100 text-slate-700"}>
      {OPENING_STATUS_LABELS[normalized] || normalized}
    </Badge>
  );
};

export default OpeningStatusBadge;
