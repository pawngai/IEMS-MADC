import { useState } from "react";
import Layout from "@/app/layout/Layout";
import { useAuth } from "@/contexts/identity";
import { usePermissions } from "@/contexts/identity_access";
import { documentsAPI } from "@/contexts/documents";
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { TableSkeleton } from "@/shared/ui/skeletons";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { Textarea } from "@/shared/ui/textarea";
import { toast } from "sonner";
import { useChangeRequestFilters } from "@/contexts/change_requests/hooks/useChangeRequestFilters";
import { useChangeRequestList } from "@/contexts/change_requests/hooks/useChangeRequestList";
import { useChangeRequestActions } from "@/contexts/change_requests/hooks/useChangeRequestActions";
import { useChangeRequestForm } from "@/contexts/change_requests/hooks/useChangeRequestForm";
import { useChangeRequestDocuments } from "@/contexts/change_requests/hooks/useChangeRequestDocuments";
import {
  PROFILE_CATEGORIES,
  SERVICE_BOOK_CATEGORIES,
  PART_KEY_TO_COMPLETE_KEY,
} from "@/contexts/change_requests/model/changeRequestFieldSchema";
import {
  canDeleteDocumentsForAuthority,
  formatDocumentSourceContextLabel,
  formatDocumentTypeLabel,
} from "@/contexts/change_requests/model/essChangeRequestDocumentDisplay";

export {
  canDeleteDocumentsForAuthority,
  formatDocumentSourceContextLabel,
  formatDocumentTypeLabel,
};
import {
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Edit3,
  FileText,
  Paperclip,
  Plus,
  RefreshCw,
  Send,
  Trash2,
  Upload,
  User,
  XCircle,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Small inline constants (not worth a separate file)
// ---------------------------------------------------------------------------

const STATUS_STYLES = {
  PENDING: "bg-amber-100 text-amber-700",
  APPROVED: "bg-blue-100 text-blue-700",
  APPLIED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  CANCELLED: "bg-slate-100 text-slate-700",
};

const STATUS_ICONS = {
  PENDING: Clock,
  APPROVED: CheckCircle2,
  APPLIED: CheckCircle2,
  REJECTED: XCircle,
  CANCELLED: XCircle,
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function EssChangeRequestsScreen() {
  const { user } = useAuth();
  const { getPrimaryAuthority } = usePermissions();

  const { loading, requests, profile, serviceBook, serviceBookEligible, loadData } =
    useChangeRequestList({ partKeyToCompleteKey: PART_KEY_TO_COMPLETE_KEY });
  const { statusFilter, setStatusFilter, filteredRequests, pendingCount } =
    useChangeRequestFilters({ requests });
  const { submitting, cancellingId, submitChangeRequest, cancelChangeRequest } =
    useChangeRequestActions({ onAfterAction: loadData });

  const [showForm, setShowForm] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [docsExpanded, setDocsExpanded] = useState(false);

  // Form hook
  const form = useChangeRequestForm({
    profile,
    serviceBook,
    serviceBookEligible,
    submitChangeRequest,
    onSuccess: () => setShowForm(false),
  });

  // Documents hook
  const docs = useChangeRequestDocuments({ open: showForm });
  const canDeleteDocuments = canDeleteDocumentsForAuthority(getPrimaryAuthority());

  // ---------------------------------------------------------------------------
  const handleCancel = async (requestId) => {
    await cancelChangeRequest(requestId);
  };

  const submitHint = !form.hasCategory
    ? "Select a category to continue."
    : !form.hasEntrySelection
      ? "Select the record entry you want to correct."
      : !form.hasValidFields
        ? "Add at least one field with a requested value."
        : !form.isReasonValid
          ? "Reason must be at least 10 characters."
          : "Ready to submit.";

  const canSubmit =
    form.hasCategory && form.hasEntrySelection && form.hasValidFields && form.isReasonValid && !submitting;

  return (
    <Layout>
      <div className="mx-auto max-w-5xl space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Change Requests</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Request corrections to your profile or service book entries
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
              <RefreshCw className={cn("mr-2 h-4 w-4", loading && "animate-spin")} />
              Refresh
            </Button>
            <Button
              size="sm"
              onClick={() => {
                form.resetForm();
                docs.resetDocuments();
                form.addField();
                setDocsExpanded(false);
                setShowForm(true);
              }}
            >
              <Plus className="mr-2 h-4 w-4" />
              New Request
            </Button>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setStatusFilter("ALL")}>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold">{requests.length}</p>
              <p className="text-xs text-muted-foreground">Total Requests</p>
            </CardContent>
          </Card>
          <Card
            className={cn("cursor-pointer hover:shadow-md transition-shadow", statusFilter === "PENDING" && "ring-2 ring-amber-500")}
            onClick={() => setStatusFilter("PENDING")}
          >
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-amber-600">{pendingCount}</p>
              <p className="text-xs text-muted-foreground">Pending</p>
            </CardContent>
          </Card>
          <Card
            className={cn("cursor-pointer hover:shadow-md transition-shadow", statusFilter === "APPLIED" && "ring-2 ring-green-500")}
            onClick={() => setStatusFilter("APPLIED")}
          >
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-green-600">
                {requests.filter((r) => r.status === "APPLIED").length}
              </p>
              <p className="text-xs text-muted-foreground">Applied</p>
            </CardContent>
          </Card>
          <Card
            className={cn("cursor-pointer hover:shadow-md transition-shadow", statusFilter === "REJECTED" && "ring-2 ring-red-500")}
            onClick={() => setStatusFilter("REJECTED")}
          >
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-red-600">
                {requests.filter((r) => r.status === "REJECTED").length}
              </p>
              <p className="text-xs text-muted-foreground">Rejected</p>
            </CardContent>
          </Card>
        </div>

        {/* Request List */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">My Requests</CardTitle>
              {statusFilter !== "ALL" && (
                <Button variant="ghost" size="sm" onClick={() => setStatusFilter("ALL")}>
                  Clear filter
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <TableSkeleton rows={5} columns={6} />
            ) : filteredRequests.length === 0 ? (
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
                    {filteredRequests.map((req) => {
                      const Icon = STATUS_ICONS[req.status] || Clock;
                      return (
                        <TableRow key={req.request_id} className="cursor-pointer" onClick={() => setSelectedRequest(req)}>
                          <TableCell className="font-mono text-xs hidden md:table-cell">{req.request_id}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{req.request_type === "PROFILE" ? "Profile" : "Service Book"}</Badge>
                          </TableCell>
                          <TableCell className="text-sm hidden sm:table-cell">
                            {req.request_type === "PROFILE"
                              ? PROFILE_CATEGORIES[req.category]?.label || req.category
                              : SERVICE_BOOK_CATEGORIES[req.category]?.label || req.category}
                          </TableCell>
                          <TableCell className="text-sm hidden lg:table-cell">{req.fields?.length || 0} field(s)</TableCell>
                          <TableCell>
                            <Badge className={cn("gap-1", STATUS_STYLES[req.status])}>
                              <Icon className="h-3 w-3" />
                              {req.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground hidden sm:table-cell">
                            {new Date(req.created_at).toLocaleDateString("en-IN")}
                          </TableCell>
                          <TableCell className="text-right">
                            {req.status === "PENDING" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                                disabled={cancellingId === req.request_id}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleCancel(req.request_id);
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

        {/* Detail Dialog */}
        <Dialog open={!!selectedRequest} onOpenChange={() => setSelectedRequest(null)}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Change Request  {selectedRequest?.request_id}</DialogTitle>
              <DialogDescription>
                {selectedRequest?.request_type === "PROFILE" ? "Profile" : "Service Book"}{" "}
                {selectedRequest?.request_type === "PROFILE"
                  ? PROFILE_CATEGORIES[selectedRequest?.category]?.label
                  : SERVICE_BOOK_CATEGORIES[selectedRequest?.category]?.label}
                {selectedRequest?.entry_label && (
                  <span className="block mt-1 text-xs">Entry: {selectedRequest.entry_label}</span>
                )}
              </DialogDescription>
            </DialogHeader>
            {selectedRequest && (
              <div className="space-y-4 text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Status:</span>
                  <Badge className={STATUS_STYLES[selectedRequest.status]}>{selectedRequest.status}</Badge>
                </div>

                <div>
                  <span className="font-medium">Requested Changes:</span>
                  <div className="mt-2 rounded-md border overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="text-xs">Field</TableHead>
                          <TableHead className="text-xs">Current</TableHead>
                          <TableHead className="text-xs">Requested</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedRequest.fields?.map((f, i) => (
                          <TableRow key={i}>
                            <TableCell className="text-xs font-medium">{f.field_label || f.field_name}</TableCell>
                            <TableCell className="text-xs text-muted-foreground">{f.current_value || ""}</TableCell>
                            <TableCell className="text-xs font-semibold text-blue-700">{f.requested_value}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>

                <div>
                  <span className="font-medium">Reason:</span>
                  <p className="mt-1 text-muted-foreground">{selectedRequest.reason}</p>
                </div>

                {selectedRequest.supporting_info && (
                  <div>
                    <span className="font-medium">Supporting Info:</span>
                    <p className="mt-1 text-muted-foreground">{selectedRequest.supporting_info}</p>
                  </div>
                )}

                {selectedRequest.attachments?.length > 0 && (
                  <div>
                    <span className="font-medium">Attachments:</span>
                    <div className="mt-1 space-y-1">
                      {selectedRequest.attachments.map((att, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between gap-2 rounded-md border px-3 py-1.5 text-xs"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <Paperclip className="h-3 w-3 text-muted-foreground" />
                            <span className="truncate">{att.original_name || att.filename}</span>
                            {att.file_size && (
                              <span className="shrink-0 text-muted-foreground">
                                ({(att.file_size / 1024).toFixed(0)} KB)
                              </span>
                            )}
                          </div>
                          {docs.getAttachmentFilename(att) ? (
                            <button
                              type="button"
                              onClick={() => documentsAPI.downloadDocument(docs.getAttachmentFilename(att), { suggestedName: att.original_name || att.filename })}
                              className="text-blue-600 hover:text-blue-700 font-medium"
                            >
                              Download
                            </button>
                          ) : (
                            <a
                              href={att.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-700 font-medium"
                            >
                              Open
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedRequest.reviewed_by && (
                  <div className="rounded-md bg-muted p-3">
                    <p className="font-medium">
                      Reviewed by: {selectedRequest.reviewer_name || selectedRequest.reviewed_by}
                    </p>
                    {selectedRequest.reviewed_at && (
                      <p className="text-xs text-muted-foreground">
                        on {new Date(selectedRequest.reviewed_at).toLocaleString("en-IN")}
                      </p>
                    )}
                    {selectedRequest.review_remarks && (
                      <p className="mt-1 text-sm italic">"{selectedRequest.review_remarks}"</p>
                    )}
                  </div>
                )}

                <p className="text-xs text-muted-foreground">
                  Submitted: {new Date(selectedRequest.created_at).toLocaleString("en-IN")}
                </p>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* New Request Dialog */}
        <Dialog
          open={showForm}
          onOpenChange={(open) => {
            if (!open) {
              setShowForm(false);
              form.resetForm();
              docs.resetDocuments();
              setDocsExpanded(false);
            }
          }}
        >
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Edit3 className="h-5 w-5" />
                New Change Request
              </DialogTitle>
              <DialogDescription>
                Request a correction to your profile or service book. Your request will be
                reviewed by an authorised officer before changes are applied.
              </DialogDescription>
            </DialogHeader>

            {(() => {
              const steps = [
                { label: "Category", done: form.hasCategory },
                { label: "Record", done: form.hasEntrySelection },
                { label: "Fields", done: form.hasValidFields },
                { label: "Reason", done: form.isReasonValid },
              ];
              const currentStep = steps.findIndex((s) => !s.done);
              return (
                <div className="flex items-start">
                  {steps.map((step, idx) => {
                    const isCompleted = step.done;
                    const isCurrent = idx === currentStep;
                    return (
                      <div key={step.label} className="flex items-center">
                        <div className="flex flex-col items-center gap-1">
                          <div className={[
                            "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 shrink-0 transition-colors",
                            isCompleted ? "bg-green-500 border-green-500 text-white" : "",
                            isCurrent ? "bg-blue-600 border-blue-600 text-white" : "",
                            !isCompleted && !isCurrent ? "bg-white border-slate-300 text-slate-400" : "",
                          ].join(" ")}>
                            {isCompleted ? <CheckCircle2 className="w-3.5 h-3.5" /> : idx + 1}
                          </div>
                          <span className={[
                            "text-[10px] font-semibold uppercase tracking-wide whitespace-nowrap",
                            isCompleted ? "text-green-600" : "",
                            isCurrent ? "text-blue-600" : "",
                            !isCompleted && !isCurrent ? "text-slate-400" : "",
                          ].join(" ")}>
                            {step.label}
                          </span>
                        </div>
                        {idx < steps.length - 1 && (
                          <div className={[
                            "h-0.5 w-8 sm:w-14 mx-1 mb-4 shrink-0 transition-colors",
                            step.done ? "bg-green-400" : "bg-slate-200",
                          ].join(" ")} />
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })()}

            <div className="space-y-5">
              {/* Request Type */}
              <div className="grid gap-1.5">
                <Label>Request Type</Label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1">
                  <button
                    type="button"
                    onClick={() => form.switchType("PROFILE")}
                    className={[
                      "flex items-start gap-3 rounded-lg border-2 p-4 text-left transition-colors",
                      form.formType === "PROFILE"
                        ? "border-blue-600 bg-blue-50"
                        : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50",
                    ].join(" ")}
                  >
                    <div className={[
                      "w-9 h-9 rounded-lg flex items-center justify-center shrink-0 mt-0.5",
                      form.formType === "PROFILE" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-500",
                    ].join(" ")}>
                      <User className="w-4 h-4" />
                    </div>
                    <div>
                      <p className={["text-sm font-semibold", form.formType === "PROFILE" ? "text-blue-700" : "text-slate-900"].join(" ")}>
                        Profile Change
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5">Update personal or contact details</p>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => form.switchType("SERVICE_BOOK")}
                    disabled={!serviceBookEligible}
                    className={[
                      "flex items-start gap-3 rounded-lg border-2 p-4 text-left transition-colors",
                      !serviceBookEligible
                        ? "opacity-50 cursor-not-allowed border-slate-100 bg-slate-50"
                        : form.formType === "SERVICE_BOOK"
                        ? "border-blue-600 bg-blue-50"
                        : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50",
                    ].join(" ")}
                  >
                    <div className={[
                      "w-9 h-9 rounded-lg flex items-center justify-center shrink-0 mt-0.5",
                      form.formType === "SERVICE_BOOK" ? "bg-blue-600 text-white" :
                      !serviceBookEligible ? "bg-slate-100 text-slate-300" : "bg-slate-100 text-slate-500",
                    ].join(" ")}>
                      <BookOpen className="w-4 h-4" />
                    </div>
                    <div>
                      <p className={[
                        "text-sm font-semibold",
                        form.formType === "SERVICE_BOOK" ? "text-blue-700" :
                        !serviceBookEligible ? "text-slate-400" : "text-slate-900",
                      ].join(" ")}>
                        Service Book Change
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {serviceBookEligible ? "Correct a service book entry" : "Regular employees only"}
                      </p>
                    </div>
                  </button>
                </div>
              </div>

              {/* Category */}
              <div className="grid gap-2">
                <Label>Category</Label>
                <Select value={form.formCategory} onValueChange={form.switchCategory}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {form.availableCategories.map((c) => (
                      <SelectItem key={c.value} value={c.value}>
                        {c.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Entry Section selector */}
              {form.isEntryBased && form.entrySections.length > 1 && (
                <div className="grid gap-2">
                  <Label>Record Type</Label>
                  <Select value={form.formEntrySection} onValueChange={form.switchEntrySection}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select record type" />
                    </SelectTrigger>
                    <SelectContent>
                      {form.entrySections.map((s) => (
                        <SelectItem key={s.key} value={s.key}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Entry selector */}
              {form.isEntryBased && form.activeEntrySection && (
                <div className="grid gap-2">
                  <Label>Select Entry to Correct</Label>
                  {form.availableEntries.length === 0 ? (
                    <p className="text-sm text-muted-foreground italic">No entries found in your service book for this section.</p>
                  ) : (
                    <Select value={form.formEntryId} onValueChange={form.switchEntryId}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select entry" />
                      </SelectTrigger>
                      <SelectContent>
                        {form.availableEntries.map((e) => (
                          <SelectItem key={e.id} value={e.id}>
                            {e.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
              )}

              {/* Fields to Change */}
              {form.formCategory && (!form.isEntryBased || form.formEntryId || (form.categoryConfig?.fields?.length > 0 && !form.formEntryId)) && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <Label>Fields to Change</Label>
                    <Button type="button" variant="outline" size="sm" onClick={form.addField}>
                      <Plus className="mr-2 h-3.5 w-3.5" />
                      Add Field
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Select a field and enter only the corrected value. You can submit multiple field corrections in one request.
                  </p>
                  {form.formFields.map((field, index) => (
                    <div key={index} className="rounded-md border p-3 space-y-2 relative">
                      <p className="text-xs font-medium text-muted-foreground">Field change #{index + 1}</p>
                      {form.formFields.length > 1 && (
                        <button
                          type="button"
                          className="absolute right-2 top-2 text-red-400 hover:text-red-600 text-xs"
                          onClick={() => form.removeField(index)}
                        >
                          &#10005;
                        </button>
                      )}
                      {form.availableFields.length > 0 ? (
                        <div className="grid gap-1">
                          <Label className="text-xs">Field</Label>
                          <Select
                            value={field.field_name}
                            onValueChange={(v) => form.updateField(index, "field_name", v)}
                          >
                            <SelectTrigger className="text-sm">
                              <SelectValue placeholder="Select field" />
                            </SelectTrigger>
                            <SelectContent>
                              {form.availableFields.map((f) => (
                                <SelectItem key={f.name} value={f.name}>
                                  {f.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          <div className="grid gap-1">
                            <Label className="text-xs">Field Name</Label>
                            <Input
                              placeholder="e.g. date_of_birth"
                              value={field.field_name}
                              onChange={(e) => form.updateField(index, "field_name", e.target.value)}
                              className="text-sm"
                            />
                          </div>
                          <div className="grid gap-1">
                            <Label className="text-xs">Field Label</Label>
                            <Input
                              placeholder="e.g. Date of Birth"
                              value={field.field_label}
                              onChange={(e) => form.updateField(index, "field_label", e.target.value)}
                              className="text-sm"
                            />
                          </div>
                        </div>
                      )}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div className="grid gap-1">
                          <Label className="text-xs">Current Value</Label>
                          <Input
                            value={field.current_value}
                            readOnly
                            placeholder="Auto-populated"
                            className="text-sm bg-muted"
                          />
                        </div>
                        <div className="grid gap-1">
                          <Label className="text-xs">Requested Value</Label>
                          <Input
                            placeholder="New value"
                            value={field.requested_value}
                            onChange={(e) => form.updateField(index, "requested_value", e.target.value)}
                            className="text-sm"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Reason */}
              <div className="grid gap-2">
                <Label>Reason for Change *</Label>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-muted-foreground">Required (minimum 10 characters)</span>
                  <span className={cn("text-xs", form.reasonLength >= 10 ? "text-green-600" : "text-muted-foreground")}>
                    {form.reasonLength}/10+
                  </span>
                </div>
                <Textarea
                  placeholder="Explain why this change is needed (min 10 characters)"
                  value={form.formReason}
                  onChange={(e) => form.setFormReason(e.target.value)}
                  rows={3}
                />
                {form.reasonLength > 0 && form.reasonLength < 10 && (
                  <p className="text-xs text-amber-600">Please add a bit more detail before submitting.</p>
                )}
              </div>

              {/* Supporting Info */}
              <div className="grid gap-2">
                <Label>Supporting Information (optional)</Label>
                <Textarea
                  placeholder="Reference numbers, document details, etc."
                  value={form.formSupportingInfo}
                  onChange={(e) => form.setFormSupportingInfo(e.target.value)}
                  rows={2}
                />
              </div>

              {/* Supporting Documents */}
              <div className="grid gap-2">
                <Label className="flex items-center gap-1">
                  <Paperclip className="h-3.5 w-3.5" />
                  Supporting Documents (optional)
                </Label>
                <p className="text-xs text-muted-foreground">
                  Upload PDF, images, or Office documents (max 10MB each).
                </p>

                {/* Attached files */}
                {form.formAttachments.length > 0 && (
                  <div className="space-y-1">
                    {form.formAttachments.map((att, idx) => (
                      <div key={idx} className="flex items-center justify-between rounded-md border bg-muted/50 px-3 py-2 text-sm">
                        <div className="flex items-center gap-2 min-w-0">
                          <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                          <span className="truncate">{att.original_name}</span>
                          <span className="shrink-0 text-xs text-muted-foreground">
                            ({(att.file_size / 1024).toFixed(0)} KB)
                          </span>
                        </div>
                        <button
                          type="button"
                          className="ml-2 text-red-400 hover:text-red-600"
                          onClick={() => form.setFormAttachments((prev) => prev.filter((_, i) => i !== idx))}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Upload button */}
                <div>
                  <label
                    className={cn(
                      "inline-flex cursor-pointer items-center gap-2 rounded-md border border-dashed px-4 py-2 text-sm transition-colors hover:bg-muted",
                      docs.uploading && "pointer-events-none opacity-50"
                    )}
                  >
                    {docs.uploading ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Upload className="h-4 w-4" />
                    )}
                    {docs.uploading ? "Uploading" : "Choose file"}
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx,.xls,.xlsx"
                      disabled={docs.uploading}
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        e.target.value = "";
                        await docs.uploadFile(file, { setFormAttachments: form.setFormAttachments });
                      }}
                    />
                  </label>
                </div>

                {/* Existing documents browser – collapsed by default */}
                <button
                  type="button"
                  className="flex w-full items-center justify-between rounded-md border border-dashed px-3 py-2 text-xs text-slate-500 hover:bg-slate-50 hover:text-slate-700 transition-colors"
                  onClick={() => setDocsExpanded((v) => !v)}
                >
                  <span className="flex items-center gap-1.5 font-medium">
                    {docsExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                    Browse previously uploaded files
                  </span>
                </button>
                {docsExpanded && (
                <div className="space-y-2 rounded-md border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <Label className="text-xs text-muted-foreground">Uploaded Documents</Label>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => docs.loadDocuments()}
                      disabled={docs.documentsLoading || docs.loadingMoreDocuments}
                    >
                      <RefreshCw className={cn("h-3.5 w-3.5", (docs.documentsLoading || docs.loadingMoreDocuments) && "animate-spin")} />
                    </Button>
                  </div>
                  <Input
                    placeholder="Search by filename"
                    value={docs.documentQuery}
                    onChange={(e) => docs.setDocumentQuery(e.target.value)}
                    className="h-8 text-xs"
                  />
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    <Select value={docs.documentTypeFilter || "ALL"} onValueChange={(value) => docs.setDocumentTypeFilter(value === "ALL" ? "" : value)}>
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue placeholder="Filter by document type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ALL">All document types</SelectItem>
                        {docs.documentTypeOptions.map((option) => (
                          <SelectItem key={option} value={option}>
                            {formatDocumentTypeLabel(option)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Select value={docs.sourceContextFilter || "ALL"} onValueChange={(value) => docs.setSourceContextFilter(value === "ALL" ? "" : value)}>
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue placeholder="Filter by source" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ALL">All sources</SelectItem>
                        {docs.sourceContextOptions.map((option) => (
                          <SelectItem key={option} value={option}>
                            {formatDocumentSourceContextLabel(option)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="max-h-44 overflow-y-auto rounded-md border">
                    {docs.documentsLoading ? (
                      <div className="p-3 text-xs text-muted-foreground">Loading documents</div>
                    ) : docs.documents.length === 0 ? (
                      <div className="p-3 text-xs text-muted-foreground">No uploaded documents found.</div>
                    ) : docs.visibleDocuments.length === 0 ? (
                      <div className="p-3 text-xs text-muted-foreground">No uploaded documents match the selected filters.</div>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="text-xs">File</TableHead>
                            <TableHead className="text-xs hidden md:table-cell">Uploaded</TableHead>
                            <TableHead className="text-xs hidden sm:table-cell">Size</TableHead>
                            <TableHead className="text-xs hidden lg:table-cell">Status</TableHead>
                            <TableHead className="text-xs text-right">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {docs.visibleDocuments.map((doc) => (
                            <TableRow key={doc.filename}>
                              <TableCell className="text-xs max-w-[210px]">
                                <div className="truncate font-medium">{doc.original_name || doc.filename}</div>
                                <div className="truncate text-[10px] text-muted-foreground">{doc.filename}</div>
                                {(doc.document_type || doc.source_context) && (
                                  <div className="mt-1 flex flex-wrap gap-1">
                                    {doc.document_type && (
                                      <Badge variant="outline" className="text-[10px]">
                                        {formatDocumentTypeLabel(doc.document_type)}
                                      </Badge>
                                    )}
                                    {doc.source_context && (
                                      <Badge variant="secondary" className="text-[10px]">
                                        {formatDocumentSourceContextLabel(doc.source_context)}
                                      </Badge>
                                    )}
                                  </div>
                                )}
                              </TableCell>
                              <TableCell className="text-xs hidden md:table-cell">
                                {docs.formatDate(doc.uploaded_at)}
                              </TableCell>
                              <TableCell className="text-xs hidden sm:table-cell">
                                {docs.formatSize(doc.file_size)}
                              </TableCell>
                              <TableCell className="text-xs hidden lg:table-cell">
                                {doc.is_locked ? (
                                  <Badge variant="secondary" className="text-[10px]">Approved</Badge>
                                ) : (
                                  <Badge variant="outline" className="text-[10px]">Draft</Badge>
                                )}
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex items-center justify-end gap-1">
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => docs.attachExistingDocument(doc, { formAttachments: form.formAttachments, setFormAttachments: form.setFormAttachments })}
                                  >
                                    Attach
                                  </Button>
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => documentsAPI.openDocument(doc.filename)}
                                  >
                                    Open
                                  </Button>
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => documentsAPI.downloadDocument(doc.filename)}
                                  >
                                    Download
                                  </Button>
                                  {canDeleteDocuments ? (
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      size="sm"
                                      className="text-red-600 hover:text-red-700"
                                      disabled={docs.deletingDocument === doc.filename || doc.is_locked}
                                      onClick={() => docs.handleDeleteDocument(doc.filename, { setFormAttachments: form.setFormAttachments })}
                                    >
                                      {doc.is_locked ? "Locked" : "Delete"}
                                    </Button>
                                  ) : null}
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </div>
                  {docs.documents.length > 0 && (
                    <div className="flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
                      <span>
                        Showing {docs.documents.length} of {docs.documentsTotal} uploaded document{docs.documentsTotal === 1 ? "" : "s"}
                      </span>
                      {docs.hasMoreDocuments ? (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="h-7 text-[11px]"
                          onClick={() => docs.loadMoreDocuments()}
                          disabled={docs.documentsLoading || docs.loadingMoreDocuments}
                        >
                          {docs.loadingMoreDocuments ? (
                            <>
                              <RefreshCw className="mr-1 h-3 w-3 animate-spin" />
                              Loading more
                            </>
                          ) : (
                            "Load more"
                          )}
                        </Button>
                      ) : null}
                    </div>
                  )}
                </div>
                )}
              </div>
            </div>

            <DialogFooter className="mt-4 flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className={cn("text-xs", canSubmit ? "text-green-600" : "text-muted-foreground")}>
                {submitHint}
              </p>
              <Button variant="outline" onClick={() => { setShowForm(false); form.resetForm(); docs.resetDocuments(); setDocsExpanded(false); }}>
                Cancel
              </Button>
              <Button onClick={form.handleSubmit} disabled={!canSubmit}>
                {submitting ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Submitting
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Submit Request
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}