import {
  getAutoCalculatedPayValue,
  getMatchingSelectValue,
  getResolvedCpcFieldValue,
  getSelectOptionLabel,
  getSelectOptionValue,
  isSystemManagedSourcePayField,
} from "@/contexts/service_book/records/model/recordServiceBookRecordDialogModel";
import {
  getFieldLabel,
  getInputPlaceholder,
  getSelectPlaceholder,
} from "@/contexts/service_book/records/lib/recordServiceBookRecordDialogUiHelpers";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

const SELECT_CLASS = "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

const getErrorSelectClass = (hasError) => (
  `flex h-9 w-full rounded-md border ${hasError ? "border-destructive ring-1 ring-destructive" : "border-input"} bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring`
);

const RecordServiceBookRecordPayCommissionSection = ({
  cpcFieldDefs,
  cpcFields,
  cpcFixationFitmentFields,
  cpcFixationSourceFields,
  cpcOptions,
  cpcFieldValues,
  cpcValueContext,
  dynamicPayFixationValue,
  fieldErrors,
  fromCpcOptions,
  getCpcLabel,
  getCpcSelectOptions,
  isCpcPayFixationEvent,
  isCustomEvent,
  isRequiredField,
  onCpcFieldChange,
  onFromCpcChange,
  onSelectedCpcChange,
  preRevisedBasicPay,
  selectedCpc,
  selectedCpcLabel,
  selectedFromCpc,
}) => {
  if (isCustomEvent) {
    return null;
  }

  return (
    <>
      {isCpcPayFixationEvent ? (
        <div className="space-y-3">
          <p className="text-sm font-semibold">Pay Commission</p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="fromCpc">{getFieldLabel("From Pay Commission (CPC)", isRequiredField("from_cpc"))}</Label>
              <select
                id="fromCpc"
                className={getErrorSelectClass(fieldErrors.has("from_cpc"))}
                value={selectedFromCpc}
                onChange={(e) => onFromCpcChange(e.target.value)}
              >
                <option value="">Select from pay commission</option>
                {fromCpcOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {fieldErrors.has("from_cpc") && (
                <p className="text-xs text-destructive">This field is required.</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cpcSelector">{getFieldLabel("To Pay Commission (CPC)", isRequiredField("to_cpc"))}</Label>
              <select
                id="cpcSelector"
                className={getErrorSelectClass(fieldErrors.has("to_cpc"))}
                value={selectedCpc}
                onChange={(e) => onSelectedCpcChange(e.target.value, { clearToCpcError: true })}
              >
                {cpcOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {fieldErrors.has("to_cpc") && (
                <p className="text-xs text-destructive">This field is required.</p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm font-semibold">Pay Commission</p>
          <div className="space-y-1.5">
            <Label htmlFor="cpcSelector">Pay Commission (CPC)</Label>
            <select
              id="cpcSelector"
              className={SELECT_CLASS}
              value={selectedCpc}
              onChange={(e) => onSelectedCpcChange(e.target.value)}
            >
              {cpcOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          {cpcFields.length > 0 && (
            <div className="space-y-3 rounded-md border border-border p-3">
              <p className="text-sm font-semibold">Pay Structure - {selectedCpcLabel}</p>
              <div className="grid grid-cols-2 gap-2">
                {cpcFields.map((key) => {
                  const def = cpcFieldDefs[key] || {
                    label: key.replaceAll("_", " "),
                    type: "text",
                  };
                  const hasError = fieldErrors.has(key);
                  const isRequired = isRequiredField(key);
                  const isSystemManaged = isSystemManagedSourcePayField(key, cpcValueContext);
                  return (
                    <div key={key} className="space-y-1">
                      <Label htmlFor={`cpc_${key}`} className="text-xs text-muted-foreground">{getFieldLabel(def.label, isRequired)}</Label>
                      {def.type === "select" ? (
                        (() => {
                          const options = getCpcSelectOptions(key, def);
                          const resolvedValue = getMatchingSelectValue(
                            key,
                            getResolvedCpcFieldValue(key, cpcValueContext),
                            options
                          );
                          return (
                            <select
                              id={`cpc_${key}`}
                              className={getErrorSelectClass(hasError)}
                              value={resolvedValue}
                              onChange={(e) => onCpcFieldChange(key, e.target.value)}
                              disabled={isSystemManaged}
                              required={isRequired}
                            >
                              <option value="">{getSelectPlaceholder(def.label)}</option>
                              {options.map((opt) => (
                                <option key={getSelectOptionValue(opt)} value={getSelectOptionValue(opt)}>
                                  {getSelectOptionLabel(opt)}
                                </option>
                              ))}
                            </select>
                          );
                        })()
                      ) : (
                        <Input
                          id={`cpc_${key}`}
                          type={def.type === "number" ? "number" : "text"}
                          placeholder={getInputPlaceholder(key, def)}
                          value={getResolvedCpcFieldValue(key, cpcValueContext)}
                          onChange={(e) => onCpcFieldChange(key, e.target.value)}
                          required={isRequired}
                          readOnly={isSystemManaged || Boolean(getAutoCalculatedPayValue(key, cpcValueContext))}
                          className={hasError ? "border-destructive ring-1 ring-destructive" : undefined}
                        />
                      )}
                      {isSystemManaged && (
                        <p className="text-xs text-muted-foreground">Derived automatically from the employee's latest recorded pay structure.</p>
                      )}
                      {hasError && (
                        <p className="text-xs text-destructive">This field is required.</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {isCpcPayFixationEvent && (
        <>
          <div className="space-y-3 rounded-md border border-border p-3">
            <p className="text-sm font-semibold">
              Pre-Revised Pay{selectedFromCpc ? ` - ${getCpcLabel(selectedFromCpc)}` : ""}
            </p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {cpcFixationSourceFields.map((key) => {
                const def = cpcFieldDefs[key] || {
                  label: key.replaceAll("_", " "),
                  type: "text",
                };
                const resolvedValue = getResolvedCpcFieldValue(key, cpcValueContext);
                const hasError = fieldErrors.has(key);
                const options = getCpcSelectOptions(key, def, selectedFromCpc);

                return (
                  <div key={`pre_${key}`} className="space-y-1">
                    <Label htmlFor={`pre_${key}`} className="text-xs text-muted-foreground">
                      {def.label}
                    </Label>
                    {def.type === "select" ? (
                      <select
                        id={`pre_${key}`}
                        className={getErrorSelectClass(hasError)}
                        value={getMatchingSelectValue(key, resolvedValue, options)}
                        disabled
                      >
                        <option value="">{getSelectPlaceholder(def.label)}</option>
                        {options.map((opt) => (
                          <option key={getSelectOptionValue(opt)} value={getSelectOptionValue(opt)}>
                            {getSelectOptionLabel(opt)}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <Input
                        id={`pre_${key}`}
                        type={def.type === "number" ? "number" : "text"}
                        value={resolvedValue}
                        readOnly
                        className={hasError ? "border-destructive ring-1 ring-destructive" : undefined}
                      />
                    )}
                  </div>
                );
              })}
              <div className="space-y-1">
                <Label htmlFor="cpc_from_basic_pay" className="text-xs text-muted-foreground">
                  {getFieldLabel("From Basic Pay", isRequiredField("from_basic_pay"))}
                </Label>
                <Input
                  id="cpc_from_basic_pay"
                  type="number"
                  placeholder="Derived from the latest recorded basic pay"
                  value={preRevisedBasicPay}
                  readOnly
                  required={isRequiredField("from_basic_pay")}
                  className={fieldErrors.has("from_basic_pay") ? "border-destructive ring-1 ring-destructive" : undefined}
                />
                <p className="text-xs text-muted-foreground">Derived automatically from the employee's latest recorded pay structure.</p>
                {fieldErrors.has("from_basic_pay") && (
                  <p className="text-xs text-destructive">This field is required.</p>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-3 rounded-md border border-border p-3">
            <p className="text-sm font-semibold">Fitment - {selectedCpcLabel}</p>
            <div className="grid grid-cols-2 gap-2">
              {cpcFixationFitmentFields.map((key) => {
                const def = cpcFieldDefs[key] || {
                  label: key.replaceAll("_", " "),
                  type: "text",
                };
                const hasError = fieldErrors.has(key);
                const isRequired = isRequiredField(key);
                return (
                  <div key={key} className="space-y-1">
                    <Label htmlFor={`cpc_${key}`} className="text-xs text-muted-foreground">{getFieldLabel(def.label, isRequired)}</Label>
                    {def.type === "select" ? (
                      (() => {
                        const options = getCpcSelectOptions(key, def);
                        return (
                          <select
                            id={`cpc_${key}`}
                            className={getErrorSelectClass(hasError)}
                            value={cpcFieldValues[key] || ""}
                            onChange={(e) => onCpcFieldChange(key, e.target.value)}
                            required={isRequired}
                          >
                            <option value="">{getSelectPlaceholder(def.label)}</option>
                            {options.map((opt) => (
                              <option key={getSelectOptionValue(opt)} value={getSelectOptionValue(opt)}>
                                {getSelectOptionLabel(opt)}
                              </option>
                            ))}
                          </select>
                        );
                      })()
                    ) : (
                      <Input
                        id={`cpc_${key}`}
                        type={def.type === "number" ? "number" : "text"}
                        placeholder={getInputPlaceholder(key, def)}
                        value={getResolvedCpcFieldValue(key, cpcValueContext)}
                        onChange={(e) => onCpcFieldChange(key, e.target.value)}
                        required={isRequired}
                        className={hasError ? "border-destructive ring-1 ring-destructive" : undefined}
                      />
                    )}
                    {hasError && (
                      <p className="text-xs text-destructive">This field is required.</p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="space-y-3 rounded-md border border-border p-3">
            <p className="text-sm font-semibold">Post-Revised Pay - {selectedCpcLabel}</p>
            <div className="grid grid-cols-2 gap-2">
              {cpcFixationFitmentFields.map((key) => {
                const def = cpcFieldDefs[key] || {
                  label: key.replaceAll("_", " "),
                  type: "text",
                };
                return (
                  <div key={`post_${key}`} className="space-y-1">
                    <Label htmlFor={`post_${key}`} className="text-xs text-muted-foreground">{def.label}</Label>
                    <Input
                      id={`post_${key}`}
                      type={def.type === "number" ? "number" : "text"}
                      value={cpcFieldValues[key] || ""}
                      readOnly
                    />
                  </div>
                );
              })}
              <div className="space-y-1 sm:col-span-2">
                <Label htmlFor="dynamicPayFixation" className="text-xs text-muted-foreground">
                  {getFieldLabel("Basic Pay", isRequiredField("to_basic_pay"))}
                </Label>
                <Input
                  id="dynamicPayFixation"
                  value={dynamicPayFixationValue}
                  placeholder="Calculated automatically from the fitment values"
                  readOnly
                  required={isRequiredField("to_basic_pay")}
                  className={fieldErrors.has("to_basic_pay") ? "border-destructive ring-1 ring-destructive" : undefined}
                />
                <p className="text-xs text-muted-foreground">
                  The post-revised basic pay is calculated automatically from the fitment values.
                </p>
                {fieldErrors.has("to_basic_pay") && (
                  <p className="text-xs text-destructive">This field is required.</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default RecordServiceBookRecordPayCommissionSection;
