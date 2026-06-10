import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { TableSkeleton } from "@/shared/ui/skeletons";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
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
        {loading ? (
          <TableSkeleton rows={5} columns={6} />
        ) : (requests || []).length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">
            <FileText className="mx-auto h-10 w-10 mb-2 opacity-30" />
            {statusFilter === "ALL"
              ? "No change requests yet. Click 'New Request' to submit one."
              : `No ${statusFilter} requests found.`}
          </div>
        ) : (
          <div className="overflow-x-auto -mx-4 sm:mx-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="hidden md:table-cell">ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="hidden sm:table-cell">Category</TableHead>
                  <TableHead className="hidden lg:table-cell">Fields</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden sm:table-cell">Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(requests || []).map((request) => {
                  const StatusIcon = STATUS_ICONS[request.status] || Clock;
                  return (
                    <TableRow key={request.request_id} className="cursor-pointer" onClick={() => onSelectRequest(request)}>
                      <TableCell className="font-mono text-xs hidden md:table-cell">{request.request_id}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{request.request_type === "PROFILE" ? "Profile" : "Service Book"}</Badge>
                      </TableCell>
                      <TableCell className="text-sm hidden sm:table-cell">
                        {request.request_type === "PROFILE"
                          ? profileCategoryLabels[request.category]?.label || request.category
                          : serviceBookCategoryLabels[request.category]?.label || request.category}
                      </TableCell>
                      <TableCell className="text-sm hidden lg:table-cell">{request.fields?.length || 0} field(s)</TableCell>
                      <TableCell>
                        <Badge className={cn("gap-1", STATUS_STYLES[request.status])}>
                          <StatusIcon className="h-3 w-3" />
                          {request.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground hidden sm:table-cell">
                        {new Date(request.created_at).toLocaleDateString("en-IN")}
                      </TableCell>
                      <TableCell className="text-right">
                        {request.status === "PENDING" && (
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
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ChangeRequestList;
