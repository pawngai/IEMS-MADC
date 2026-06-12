import { Card, CardContent } from "@/shared/ui/card";
import { cn } from "@/shared/lib/utils";

const ChangeRequestFilters = ({ requests, statusFilter, onStatusFilterChange }) => {
  const total = (requests || []).length;
  const pending = (requests || []).filter((request) => request.status === "PENDING").length;
  const applied = (requests || []).filter((request) => request.status === "APPLIED").length;
  const rejected = (requests || []).filter((request) => request.status === "REJECTED").length;

  const options = [
    { key: "ALL", label: "Total Requests", value: total, tone: "text-slate-900" },
    { key: "PENDING", label: "Pending", value: pending, tone: "text-amber-600" },
    { key: "APPLIED", label: "Applied", value: applied, tone: "text-green-600" },
    { key: "REJECTED", label: "Rejected", value: rejected, tone: "text-red-600" },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {options.map((option) => (
        <Card
          key={option.key}
          className={cn(
            "cursor-pointer hover:shadow-md transition-shadow",
            statusFilter === option.key && option.key !== "ALL" && "ring-2 ring-blue-500"
          )}
          onClick={() => onStatusFilterChange(option.key)}
        >
          <CardContent className="p-4 text-center">
            <p className={cn("text-2xl font-bold", option.tone)}>{option.value}</p>
            <p className="text-xs text-muted-foreground">{option.label}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default ChangeRequestFilters;
