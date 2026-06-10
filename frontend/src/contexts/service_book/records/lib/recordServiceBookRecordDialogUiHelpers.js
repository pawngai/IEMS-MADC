import { FIELD_PLACEHOLDER_EXAMPLES } from "@/contexts/service_book/records/model/recordServiceBookRecordDialogModel";

export const getFieldLabel = (label, required = false) =>
  required ? `${label} *` : label;

export const getSelectPlaceholder = (label) => `Select ${String(label || "option").trim().toLowerCase()}`;

export const getInputPlaceholder = (key, def) => {
  if (FIELD_PLACEHOLDER_EXAMPLES[key]) {
    return FIELD_PLACEHOLDER_EXAMPLES[key];
  }

  const label = String(def?.label || key || "value").trim().toLowerCase();
  if (def?.type === "number") {
    return `Enter ${label}`;
  }
  if (def?.type === "text") {
    return `Enter ${label}`;
  }
  return undefined;
};