import { Plus, Trash2, Upload } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";
import { Checkbox } from "@/shared/ui/checkbox";

const OpeningPartFormFields = ({ schema, value, onChange, disabled, documents = [], uploading, onUpload }) => {
  const fieldMap = new Map((schema.fields || []).map((field) => [field.name, field]));
  const hasSectionCards = Array.isArray(schema.sections) && schema.sections.length > 0;
  const sections = Array.isArray(schema.sections) && schema.sections.length > 0
    ? schema.sections.map((section) => ({
        ...section,
        fields: (section.fields || []).map((fieldName) => fieldMap.get(fieldName)).filter(Boolean),
      }))
    : [{ id: schema.id || "default", fields: schema.fields || [] }];

  const updateRepeatableRows = (fieldName, rows) => {
    onChange({ [fieldName]: rows });
  };

  const getRowFieldOptions = (rowField) => {
    if (Array.isArray(rowField.options)) {
      return rowField.options
        .map((option) => (typeof option === "string" ? { label: option, value: option } : option))
        .filter((option) => option?.value !== undefined && option?.value !== null && option?.value !== "");
    }

    if (!rowField.optionsFromField) {
      return [];
    }

    const sourceRows = Array.isArray(value?.[rowField.optionsFromField]) ? value[rowField.optionsFromField] : [];
    const optionLabelField = rowField.optionLabelField || "name";
    const optionValueField = rowField.optionValueField || optionLabelField;
    const seen = new Set();

    return sourceRows.reduce((options, sourceRow) => {
      const optionValue = String(sourceRow?.[optionValueField] || "").trim();
      if (!optionValue || seen.has(optionValue)) {
        return options;
      }

      seen.add(optionValue);
      options.push({
        label: String(sourceRow?.[optionLabelField] || optionValue).trim(),
        value: optionValue,
        source: sourceRow,
      });
      return options;
    }, []);
  };

  const renderUploadPanel = ({ uploadConfig, uploadId, fieldKey, fieldLabel, fieldDisabled, title, description, cardClassName = "space-y-2 pt-1" }) => {
    if (!uploadConfig) return null;

    const uploadLabel = uploadConfig?.buttonLabel || `Upload ${fieldLabel} document`;
    const targetFieldKey = uploadConfig?.fieldKey || fieldKey;
    const targetFieldLabel = uploadConfig?.fieldLabel || fieldLabel;
    const uploadDocuments = documents.filter((document) => document?.field_key === targetFieldKey && (document?.part_id || schema.id) === schema.id);

    return (
      <div className={cardClassName}>
        {(title || description) && (
          <div className="space-y-1">
            {title && <p className="text-sm font-medium text-slate-900">{title}</p>}
            {description && <p className="text-xs text-slate-500">{description}</p>}
          </div>
        )}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="gap-2"
          disabled={fieldDisabled || uploading}
          onClick={() => document.getElementById(uploadId)?.click()}
        >
          <Upload className="w-4 h-4" />
          {uploading ? "Uploading..." : uploadLabel}
        </Button>
        <input
          id={uploadId}
          type="file"
          className="hidden"
          aria-label={`Upload ${targetFieldLabel} document`}
          disabled={fieldDisabled || uploading}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) {
              onUpload?.(file, {
                partId: schema.id,
                fieldKey: targetFieldKey,
                fieldLabel: targetFieldLabel,
              });
            }
            event.target.value = "";
          }}
        />
        {uploadDocuments.length > 0 && (
          <div className="space-y-1 rounded-md border border-dashed border-slate-200 p-2">
            {uploadDocuments.map((document, index) => (
              <p key={`${document.document_id || document.name || targetFieldKey}-${index}`} className="text-xs text-slate-600">
                {document.name || document.original_name || document.document_id}
              </p>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderFieldUpload = (field, fieldDisabled) => renderUploadPanel({
    uploadConfig: field.documentUpload,
    uploadId: `${schema.id}-${field.name}-upload`,
    fieldKey: field.name,
    fieldLabel: field.label,
    fieldDisabled,
  });

  const renderRepeatableRowsField = (field) => {
    const rows = Array.isArray(value?.[field.name]) ? value[field.name] : [];
    const rowFields = Array.isArray(field.fields) ? field.fields : [];
    const fieldDisabled = disabled || field.readOnly;
    const addRow = () => {
      updateRepeatableRows(
        field.name,
        rows.concat([
          rowFields.reduce((nextRow, rowField) => ({
            ...nextRow,
            [rowField.name]: "",
          }), {}),
        ])
      );
    };
    const updateRow = (rowIndex, rowFieldName, nextValue, rowField) => {
      updateRepeatableRows(
        field.name,
        rows.map((row, index) =>
          index === rowIndex
            ? (() => {
                const nextRow = {
                  ...(row || {}),
                  [rowFieldName]: nextValue,
                };

                if (rowField?.populateFromSource && rowField?.optionsFromField) {
                  const selectedOption = getRowFieldOptions(rowField).find((option) => option.value === nextValue);
                  Object.entries(rowField.populateFromSource).forEach(([targetField, sourceField]) => {
                    nextRow[targetField] = selectedOption?.source?.[sourceField] || "";
                  });
                }

                return nextRow;
              })()
            : row
        )
      );
    };
    const removeRow = (rowIndex) => {
      updateRepeatableRows(
        field.name,
        rows.filter((_, index) => index !== rowIndex)
      );
    };

    return (
      <div key={field.name} className="md:col-span-2 space-y-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <Label className="text-xs font-medium text-slate-600">{field.label}</Label>
            {field.emptyState && rows.length === 0 && <p className="mt-1 text-xs text-slate-500">{field.emptyState}</p>}
          </div>
          <Button type="button" variant="outline" size="sm" className="gap-2" disabled={disabled} onClick={addRow}>
            <Plus className="w-4 h-4" />
            {field.addLabel || `Add ${field.rowLabel || field.label}`}
          </Button>
        </div>

        {rows.length > 0 && (
          <div className="space-y-3">
            {rows.map((row, rowIndex) => (
              <div key={`${field.name}-${rowIndex}`} className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-slate-900">{field.rowLabel || field.label} {rowIndex + 1}</p>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="gap-2 text-slate-500"
                    disabled={disabled}
                    onClick={() => removeRow(rowIndex)}
                  >
                    <Trash2 className="w-4 h-4" />
                    Remove
                  </Button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {rowFields.map((rowField) => {
                    const inputId = `${schema.id}-${field.name}-${rowIndex}-${rowField.name}`;
                    const rowFieldOptions = getRowFieldOptions(rowField);
                    const selectDisabled = fieldDisabled || (rowField.type === "select" && rowFieldOptions.length === 0);
                    return (
                      <div key={rowField.name} className="space-y-1.5">
                        <Label htmlFor={inputId} className="text-xs font-medium text-slate-600">
                          {rowField.label}
                        </Label>
                        {rowField.type === "select" ? (
                          <select
                            id={inputId}
                            className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                            value={row?.[rowField.name] || ""}
                            disabled={selectDisabled}
                            onChange={(event) => updateRow(rowIndex, rowField.name, event.target.value, rowField)}
                          >
                            <option value="">
                              {rowFieldOptions.length > 0
                                ? rowField.placeholder || `Select ${rowField.label.toLowerCase()}`
                                : rowField.emptyOptionsLabel || "Add a family member first"}
                            </option>
                            {rowFieldOptions.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <Input
                            id={inputId}
                            type={rowField.type || "text"}
                            value={row?.[rowField.name] || ""}
                            disabled={fieldDisabled}
                            onChange={(event) => updateRow(rowIndex, rowField.name, event.target.value, rowField)}
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
        {renderFieldUpload(field, fieldDisabled)}
      </div>
    );
  };

  const renderField = (field) => {
      if (field.type === "repeatable_rows") {
        return renderRepeatableRowsField(field);
      }
      const rawValue = value?.[field.name];
      const fieldValue = Array.isArray(rawValue) ? rawValue.join("\n") : rawValue || "";
      const fieldDisabled = disabled || field.readOnly;
      return (
        <div key={field.name} className={field.type === "textarea" ? "md:col-span-2 space-y-1.5" : "space-y-1.5"}>
          {field.type === "boolean" ? (
            <label
              htmlFor={`${schema.id}-${field.name}`}
              className="flex min-h-10 items-center gap-2 rounded-md border px-3 py-2 text-sm text-slate-700"
            >
              <Checkbox
                id={`${schema.id}-${field.name}`}
                checked={Boolean(rawValue)}
                disabled={fieldDisabled}
                onCheckedChange={(checked) => onChange({ [field.name]: Boolean(checked) })}
              />
              <span>
                {field.label}
                {schema.required.includes(field.name) ? " *" : ""}
              </span>
            </label>
          ) : (
            <>
              <Label htmlFor={`${schema.id}-${field.name}`} className="text-xs font-medium text-slate-600">
                {field.label}
                {schema.required.includes(field.name) ? " *" : ""}
              </Label>
              {field.type === "textarea" ? (
            <Textarea
              id={`${schema.id}-${field.name}`}
              value={fieldValue}
              disabled={fieldDisabled}
              onChange={(event) => {
                const nextValue = field.type === "textarea" && Array.isArray(rawValue)
                  ? event.target.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
                  : event.target.value;
                onChange({ [field.name]: nextValue });
              }}
            />
              ) : (
            <Input
              id={`${schema.id}-${field.name}`}
              type={field.type || "text"}
              value={fieldValue}
              disabled={fieldDisabled}
              onChange={(event) => onChange({ [field.name]: event.target.value })}
            />
              )}
            </>
          )}
          {renderFieldUpload(field, fieldDisabled)}
        </div>
      );
  };

  return (
    <div className="space-y-4">
      {sections.map((section) => {
        const sectionBody = (
          <>
            {!hasSectionCards && (section.title || section.description) && (
              <div className="space-y-1">
                {section.title && <h3 className="text-sm font-semibold text-slate-900">{section.title}</h3>}
                {section.description && <p className="text-xs text-slate-500">{section.description}</p>}
              </div>
            )}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {section.fields.map((field) => renderField(field))}
            </div>
            {section.documentUpload && renderUploadPanel({
              uploadConfig: section.documentUpload,
              uploadId: `${schema.id}-${section.id}-upload`,
              fieldKey: section.id,
              fieldLabel: section.title || section.id,
              fieldDisabled: disabled,
              title: section.documentUpload.title,
              description: section.documentUpload.description,
              cardClassName: "rounded-lg border border-dashed border-slate-300 bg-white/70 p-4 space-y-3",
            })}
          </>
        );

        if (hasSectionCards) {
          return (
            <Card key={section.id} className="border-slate-200 shadow-sm" data-testid={`opening-section-${schema.id}-${section.id}`}>
              {(section.title || section.description) && (
                <CardHeader className="pb-3">
                  {section.title && <CardTitle className="text-base">{section.title}</CardTitle>}
                  {section.description && <p className="text-sm text-slate-500">{section.description}</p>}
                </CardHeader>
              )}
              <CardContent className="space-y-4">
                {sectionBody}
              </CardContent>
            </Card>
          );
        }

        return (
          <section key={section.id} className="rounded-lg border border-slate-200 bg-slate-50/50 p-4 space-y-4">
            {sectionBody}
          </section>
        );
      })}
    </div>
  );
};

export default OpeningPartFormFields;
