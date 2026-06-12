import EssChangeRequestDocumentPicker from "@/modules/change_requests/containers/EssChangeRequestDocumentPicker";
import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Textarea } from "@/shared/ui/textarea";
import {
  BookOpen,
  CheckCircle2,
  Edit3,
  Plus,
  RefreshCw,
  Send,
  User,
} from "lucide-react";

const EssChangeRequestFormDialog = ({
  canDeleteDocuments,
  canSubmit,
  docs,
  docsExpanded,
  form,
  serviceBookEligible,
  setDocsExpanded,
  setShowForm,
  showForm,
  submitting,
  submitHint,
}) => (
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

        <EssChangeRequestDocumentPicker
          canDeleteDocuments={canDeleteDocuments}
          docs={docs}
          docsExpanded={docsExpanded}
          form={form}
          setDocsExpanded={setDocsExpanded}
        />
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

);

export default EssChangeRequestFormDialog;
