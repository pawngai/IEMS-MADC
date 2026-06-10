import { useState } from "react";
import { serviceBookRecordsAPI } from "@/contexts/service_book/records/api/serviceBookRecordsApi";
import {
  buildCorrectCommand,
  getFallbackServiceRecordSchema,
  getServiceRecordDisplayLabel,
} from "@/contexts/service_book/records/model/serviceBookRecordsModel";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/shared/ui/sheet";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { toast } from "sonner";
import { Loader2, Plus, X } from "lucide-react";

const OBJECT_PAYLOAD_FIELD_KEYS = new Set([
  "pre_revised_pay",
  "fitment",
  "post_revised_pay",
  "option",
]);

const FALLBACK_SCHEMA = getFallbackServiceRecordSchema();
const FIELD_DEFINITIONS = {
  cpc: { label: "Pay Commission (CPC)", type: "select", options: FALLBACK_SCHEMA.cpcOptions },
  ...FALLBACK_SCHEMA.fieldDefinitions,
  ...FALLBACK_SCHEMA.cpcFieldDefinitions,
};
const FIELD_OPTIONS = Object.entries(FIELD_DEFINITIONS)
  .map(([value, definition]) => ({
    value,
    label: definition.label,
  }))
  .sort((left, right) => left.label.localeCompare(right.label));

function isObjectPayloadValue(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function formatPayloadFieldValue(value) {
  if (isObjectPayloadValue(value)) {
    return JSON.stringify(value, null, 2);
  }
  return String(value ?? "");
}

function toTitleCase(value) {
  return String(value || "")
    .trim()
    .replace(/[_-]+/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function getReadableFieldLabel(key) {
  return FIELD_DEFINITIONS[key]?.label || toTitleCase(key) || "Custom field";
}

function toReadableOptionLabel(value) {
  return toTitleCase(value);
}

function getSelectOptionValue(option) {
  if (option && typeof option === "object") {
    return option.value ?? option.label ?? "";
  }
  return option;
}

function getSelectOptionLabel(option) {
  if (option && typeof option === "object") {
    return String(option.label || option.value || "").trim();
  }
  return toReadableOptionLabel(option);
}

function getFieldDefinition(key) {
  return FIELD_DEFINITIONS[key] || null;
}

function isKnownField(key) {
  return Boolean(getFieldDefinition(key));
}

function getFieldSelectOptions(definition, selectedCpc, currentValue) {
  const directOptions = Array.isArray(definition?.options) ? definition.options : [];
  const optionsByCpc = definition?.optionsByCpc || definition?.options_by_cpc;

  let options = directOptions;
  if (!options.length && optionsByCpc && typeof optionsByCpc === "object") {
    if (selectedCpc && Array.isArray(optionsByCpc[selectedCpc])) {
      options = optionsByCpc[selectedCpc];
    } else {
      const deduped = new Map();
      Object.values(optionsByCpc).forEach((optionList) => {
        if (!Array.isArray(optionList)) return;
        optionList.forEach((option) => {
          const value = String(getSelectOptionValue(option) || "").trim();
          if (value && !deduped.has(value)) {
            deduped.set(value, option);
          }
        });
      });
      options = Array.from(deduped.values());
    }
  }

  const normalizedCurrentValue = String(currentValue || "").trim();
  if (!normalizedCurrentValue) return options;

  const hasCurrentValue = options.some(
    (option) => String(getSelectOptionValue(option) || "").trim() === normalizedCurrentValue
  );
  return hasCurrentValue ? options : [...options, normalizedCurrentValue];
}

const CorrectServiceBookRecordDialog = ({ event, onSuccess, onClose }) => {
  const eventId = event.id || event.service_event_id;
  const eventLabel = getServiceRecordDisplayLabel(event).toLowerCase();
  const existingPayload = event.payload || {};
  const selectedCpc = String(existingPayload.cpc || "").trim();

  // Pre-fill with existing payload for easy editing
  const initialFields = Object.entries(existingPayload)
    .filter(([k]) => !k.startsWith("_"))
    .map(([key, value]) => ({
      key,
      mode: isKnownField(key) ? "known" : "custom",
      value: formatPayloadFieldValue(value),
      valueType: isObjectPayloadValue(value) || OBJECT_PAYLOAD_FIELD_KEYS.has(key) ? "object" : "scalar",
    }));

  const [payloadFields, setPayloadFields] = useState(
    initialFields.length > 0 ? initialFields : [{ key: "", mode: "known", value: "" }]
  );
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);

  const addPayloadField = () => {
    setPayloadFields((prev) => [...prev, { key: "", mode: "known", value: "", valueType: "scalar" }]);
  };

  const removePayloadField = (idx) => {
    setPayloadFields((prev) => prev.filter((_, i) => i !== idx));
  };

  const updatePayloadField = (idx, field, value) => {
    setPayloadFields((prev) =>
      prev.map((f, i) => (i === idx ? { ...f, [field]: value } : f))
    );
  };

  const updateFieldMode = (idx, mode) => {
    setPayloadFields((prev) =>
      prev.map((field, i) => {
        if (i !== idx) return field;
        return {
          ...field,
          mode,
          key: mode === "known" ? "" : field.key,
        };
      })
    );
  };

  const updatePayloadFieldKey = (idx, key) => {
    setPayloadFields((prev) =>
      prev.map((field, i) => {
        if (i !== idx) return field;
        return {
          ...field,
          key,
          valueType: OBJECT_PAYLOAD_FIELD_KEYS.has(key) ? "object" : field.valueType,
          value: OBJECT_PAYLOAD_FIELD_KEYS.has(key) && field.valueType !== "object"
            ? "{}"
            : field.value,
        };
      })
    );
  };

  const renderValueInput = (field, idx) => {
    const fieldDefinition = getFieldDefinition(field.key);
    const valueLabel = `Corrected value for ${field.key ? getReadableFieldLabel(field.key) : "selected field"}`;

    if (field.valueType === "object") {
      return (
        <textarea
          aria-label={valueLabel}
          className="flex min-h-[96px] flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm font-mono shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          placeholder="Enter valid JSON object"
          value={field.value}
          onChange={(e) => updatePayloadField(idx, "value", e.target.value)}
        />
      );
    }

    if (!fieldDefinition || field.mode === "custom") {
      return (
        <Input
          aria-label={valueLabel}
          placeholder={field.key ? `Updated ${getReadableFieldLabel(field.key).toLowerCase()}` : "Enter corrected value"}
          value={field.value}
          onChange={(e) => updatePayloadField(idx, "value", e.target.value)}
          className="flex-1"
        />
      );
    }

    if (fieldDefinition.type === "select") {
      const options = getFieldSelectOptions(fieldDefinition, selectedCpc, field.value);
      return (
        <select
          aria-label={valueLabel}
          className="flex h-10 sm:h-9 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={field.value}
          onChange={(e) => updatePayloadField(idx, "value", e.target.value)}
        >
          <option value="">Select {getReadableFieldLabel(field.key).toLowerCase()}</option>
          {options.map((option) => {
            const optionValue = getSelectOptionValue(option);
            return (
              <option key={String(optionValue)} value={optionValue}>
                {getSelectOptionLabel(option)}
              </option>
            );
          })}
        </select>
      );
    }

    if (fieldDefinition.type === "date" || fieldDefinition.type === "number") {
      return (
        <Input
          aria-label={valueLabel}
          type={fieldDefinition.type}
          step={fieldDefinition.type === "number" ? "any" : undefined}
          placeholder={fieldDefinition.type === "number" ? `Updated ${getReadableFieldLabel(field.key).toLowerCase()}` : undefined}
          value={field.value}
          onChange={(e) => updatePayloadField(idx, "value", e.target.value)}
          className="flex-1"
        />
      );
    }

    return (
      <Input
        aria-label={valueLabel}
        placeholder={`Updated ${getReadableFieldLabel(field.key).toLowerCase()}`}
        value={field.value}
        onChange={(e) => updatePayloadField(idx, "value", e.target.value)}
        className="flex-1"
      />
    );
  };

  const buildPayload = () => {
    const payload = {};
    for (const { key, value, valueType } of payloadFields) {
      const k = key.trim();
      if (!k) {
        continue;
      }
      if (valueType === "object") {
        const trimmed = String(value || "").trim();
        payload[k] = trimmed ? JSON.parse(trimmed) : {};
        continue;
      }
      payload[k] = value;
    }
    return payload;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason.trim()) {
      toast.error("Reason is required for corrections");
      return;
    }
    let correctedPayload;
    try {
      correctedPayload = buildPayload();
    } catch {
      toast.error("Object fields must contain valid JSON");
      return;
    }
    if (Object.keys(correctedPayload).length === 0) {
      toast.error("At least one corrected field is required");
      return;
    }

    setSaving(true);
    try {
      const cmd = buildCorrectCommand({
        serviceEventId: eventId,
        correctedPayload,
        reason: reason.trim(),
      });
      await serviceBookRecordsAPI.correctEvent(eventId, cmd);
      onSuccess();
    } catch (err) {
      const msg =
        err?.response?.data?.detail || err.message || "Failed to correct event";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" size="xl">
        <SheetHeader>
          <SheetTitle>Correct Service Book Record</SheetTitle>
          <SheetDescription>
            Correct the data for the {eventLabel} event. Provide the corrected values
            and a reason for the correction.
          </SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Corrected Payload */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>Corrected Data</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={addPayloadField}
                className="gap-1 text-xs h-7"
              >
                <Plus className="w-3 h-3" />
                Add Field
              </Button>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {payloadFields.map((field, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  {field.mode === "known" ? (
                    <select
                      aria-label="Corrected field"
                      className="flex h-10 sm:h-9 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      value={field.key}
                      onChange={(e) => {
                        if (e.target.value === "__custom__") {
                          updateFieldMode(idx, "custom");
                          return;
                        }
                        updatePayloadFieldKey(idx, e.target.value);
                      }}
                    >
                      <option value="">Select field</option>
                      {FIELD_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                      <option value="__custom__">Custom field</option>
                    </select>
                  ) : (
                    <Input
                      aria-label="Custom field name"
                      placeholder="Custom field name"
                      value={field.key}
                      onChange={(e) => updatePayloadFieldKey(idx, e.target.value)}
                      className="flex-1"
                    />
                  )}
                  {renderValueInput(field, idx)}
                  {field.mode === "custom" && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => updateFieldMode(idx, "known")}
                      className="h-8 px-2 text-xs flex-shrink-0"
                    >
                      Known Field
                    </Button>
                  )}
                  {payloadFields.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removePayloadField(idx)}
                      className="h-8 w-8 p-0 flex-shrink-0"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Reason */}
          <div className="space-y-1.5">
            <Label htmlFor="reason">Reason for Correction *</Label>
            <textarea
              id="reason"
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              placeholder="Explain why this correction is needed..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
            />
          </div>

          <SheetFooter className="mt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="gap-1">
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              Apply Correction
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
};

export default CorrectServiceBookRecordDialog;
