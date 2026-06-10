import { Badge } from "@/shared/ui/badge";

const STATUS_STYLES = {
  SUBMITTED: "bg-amber-100 text-amber-700",
  RECOMMENDED: "bg-blue-100 text-blue-700",
  SANCTIONED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  CANCELLED: "bg-slate-100 text-slate-600",
};

export const LeaveStatusBadge = ({ status }) => (
  <Badge className={STATUS_STYLES[status] || "bg-slate-100 text-slate-600"}>{status}</Badge>
);
