import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { DataTable } from "@/shared/data-table";
import { cn } from "@/shared/lib/utils";
import { Clock, FileText } from "lucide-react";

const STATUS_STYLES = {
  PENDING: "bg-amber-100 text-amber-700",
  APPROVED: "bg-blue-100 text-blue-700",
  APPLIED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  CANCELLED: "bg-slate-100 text-slate-700",
};

const STATUS_ICONS = {
  PENDING: Clock,
  APPROVED: Clock,
  APPLIED: Clock,
  REJECTED: Clock,
  CANCELLED: Clock,
};

const buildColumns = ({
  profileCategoryLabels,
  serviceBookCategoryLabels,
  onCancelRequest,
  cancellingId,
}) => [
  {
    key: "request_id",
    header: "ID",
    className: "font-mono text-xs hidden md:table-cell",
    headClassName: "hidden md:table-cell",
  },
  {
    key: "type",
    header: "Type",
    render: (request) => (
      <Badge variant="outline">{request.request_type === "PROFILE" ? "Profile" : "Service Book"}</Badge>
    ),
  },
  {
    key: "category",
    header: "Category",
    className: "text-sm hidden sm:table-cell",
    headClassName: "hidden sm:table-cell",
    render: (request) =>
      request.request_type === "PROFILE"
        ? profileCategoryLabels[request.category]?.label || request.category
        : serviceBookCategoryLabels[request.category]?.label || request.category,
  },
  {
    key: "fields",
    header: "Fields",
    className: "text-sm hidden lg:table-cell",
    headClassName: "hidden lg:table-cell",
    render: (request) => `${request.fields?.length || 0} field(s)`,
  },
  {
    key: "status",
    header: "Status",
    render: (request) => {
      const StatusIcon = STATUS_ICONS[request.status] || Clock;
      return (
        <Badge className={cn("gap-1", STATUS_STYLES[request.status])}>
          <StatusIcon className="h-3 w-3" />
          {request.status}
        </Badge>
      );
    },
  },
  {
    key: "created_at",
    header: "Date",
    className: "text-xs text-muted-foreground hidden sm:table-cell",
    headClassName: "hidden sm:table-cell",
    render: (request) => new Date(request.created_at).toLocaleDateString("en-IN"),
  },
  {
    key: "actions",
    header: "Actions",
    className: "text-right",
    render: (request) =>
      request.status === "PENDING" ? (
        <Button
          variant="ghost"
          size="sm"
          className="text-red-600 hover:text-red-700"
          disabled={cancellingId === request.request_id}
          onClick={(event) => {
            event.stopPropagation();
            onCancelRequest(request.request_id);
          }}
        >
          Cancel
        </Button>
      ) : null,
  },
];

const ChangeRequestList = ({
  loading,
  requests,
  statusFilter,
  onClearFilter,
  onSelectRequest,
  onCancelRequest,
  cancellingId,
  profileCategoryLabels,
  serviceBookCategoryLabels,
}) => {
  const columns = buildColumns({
    profileCategoryLabels,
    serviceBookCategoryLabels,
    onCancelRequest,
    cancellingId,
  });

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">My Requests</CardTitle>
          {statusFilter !== "ALL" && (
            <Button variant="ghost" size="sm" onClick={onClearFilter}>
              Clear filter
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          rows={requests || []}
          rowKey={(request) => request.request_id}
          loading={loading}
          skeletonRows={5}
          onRowClick={onSelectRequest}
          emptyState={
            <div className="py-12 text-center text-muted-foreground">
              <FileText className="mx-auto h-10 w-10 mb-2 opacity-30" />
              {statusFilter === "ALL"
                ? "No change requests yet. Click 'New Request' to submit one."
                : `No ${statusFilter} requests found.`}
            </div>
          }
        />
      </CardContent>
    </Card>
  );
};

export default ChangeRequestList;
