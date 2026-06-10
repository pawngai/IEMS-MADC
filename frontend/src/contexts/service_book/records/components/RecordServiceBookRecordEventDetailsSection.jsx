import {
  getSelectOptionLabel,
  getSelectOptionValue,
} from "@/contexts/service_book/records/model/recordServiceBookRecordDialogModel";
import {
  getFieldLabel,
  getInputPlaceholder,
  getSelectPlaceholder,
} from "@/contexts/service_book/records/lib/recordServiceBookRecordDialogUiHelpers";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Plus, X } from "lucide-react";

const RecordServiceBookRecordEventDetailsSection = ({
  isCustomEvent,
  customDetailRows,
  customDetailError,
  eventDetailKeys,
  fieldErrors,
  fieldValues,
  showEffectiveTo,
  effectiveTo,
  getEventDetailDefinition,
  isRequiredField,
  onFieldChange,
  onEffectiveToChange,
  onAddCustomDetailRow,
  onRemoveCustomDetailRow,
  onUpdateCustomDetailRow,
}) => (
  <div className="space-y-2">
    <p className="text-sm font-semibold">Event Details</p>
    {isCustomEvent ? (
      <div className="space-y-3 rounded-md border border-border p-3">
        <p className="text-xs text-muted-foreground">
          Add the event detail fields manually for this custom event.
        </p>
        {customDetailRows.map((row, index) => (
          <div key={`custom_detail_${index}`} className="grid grid-cols-1 gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)_auto]">
            <div className="space-y-1">
              <Label htmlFor={`customDetailKey_${index}`} className="text-xs text-muted-foreground">Field Name</Label>
              <Input
                id={`customDetailKey_${index}`}
                aria-label={`Custom detail field name ${index + 1}`}
                placeholder="e.g., event_title"
                value={row.key}
                onChange={(event) => onUpdateCustomDetailRow(index, "key", event.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor={`customDetailValue_${index}`} className="text-xs text-muted-foreground">Field Value</Label>
              <Input
                id={`customDetailValue_${index}`}
                aria-label={`Custom detail field value ${index + 1}`}
                placeholder="Enter field value"
                value={row.value}
                onChange={(event) => onUpdateCustomDetailRow(index, "value", event.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button
                type="button"
                variant="outline"
                size="icon"
                aria-label={`Remove custom detail row ${index + 1}`}
                onClick={() => onRemoveCustomDetailRow(index)}
                disabled={customDetailRows.length === 1}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
        ))}
        <div className="flex justify-start">
          <Button type="button" variant="outline" size="sm" onClick={onAddCustomDetailRow}>
            <Plus className="w-4 h-4" />
            Add Field
          </Button>
        </div>
        {customDetailError && (
          <p className="text-xs text-destructive">{customDetailError}</p>
        )}
      </div>
    ) : (
      <div className="grid grid-cols-2 gap-3 rounded-md border border-border p-3">
        {eventDetailKeys.map((key) => {
          const definition = getEventDetailDefinition(key);
          const hasError = fieldErrors.has(key);
          const isRequired = isRequiredField(key);
          return (
            <div key={key} className="space-y-1">
              <Label htmlFor={key}>{getFieldLabel(definition.label, isRequired)}</Label>
              {definition.type === "select" ? (
                <select
                  id={key}
                  className={`flex h-9 w-full rounded-md border ${hasError ? "border-destructive ring-1 ring-destructive" : "border-input"} bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring`}
                  value={fieldValues[key] || ""}
                  onChange={(event) => onFieldChange(key, event.target.value)}
                  required={isRequired}
                >
                  <option value="">{getSelectPlaceholder(definition.label)}</option>
                  {(definition.options || []).map((option) => (
                    <option key={getSelectOptionValue(option)} value={getSelectOptionValue(option)}>
                      {getSelectOptionLabel(option)}
                    </option>
                  ))}
                </select>
              ) : (
                <Input
                  id={key}
                  type={definition.type === "number" ? "number" : definition.type === "date" ? "date" : "text"}
                  required={isRequired}
                  placeholder={getInputPlaceholder(key, definition)}
                  value={fieldValues[key] || ""}
                  onChange={(event) => onFieldChange(key, event.target.value)}
                  className={hasError ? "border-destructive ring-1 ring-destructive" : undefined}
                />
              )}
              {hasError && (
                <p className="text-xs text-destructive">This field is required.</p>
              )}
            </div>
          );
        })}
        {showEffectiveTo && (
          <div className="space-y-1">
            <Label htmlFor="effectiveTo">Effective To</Label>
            <Input
              id="effectiveTo"
              type="date"
              value={effectiveTo}
              onChange={(event) => onEffectiveToChange(event.target.value)}
            />
          </div>
        )}
      </div>
    )}
  </div>
);

export default RecordServiceBookRecordEventDetailsSection;
