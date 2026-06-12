import {
  getFieldLabel,
  getInputPlaceholder,
} from "@/modules/service_book/records/lib/recordServiceBookRecordDialogUiHelpers";
import { SheetFooter } from "@/shared/ui/sheet";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Loader2 } from "lucide-react";

export const EventCategorySelect = ({
  options,
  value,
  onChange,
}) => (
  <div className="space-y-1.5">
    <Label htmlFor="eventCategory">Event Category</Label>
    <select
      id="eventCategory"
      className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  </div>
);

export const AuthorityField = ({
  value,
  required,
  onChange,
}) => (
  <div className="space-y-1.5">
    <Label htmlFor="authority">
      {getFieldLabel("Authority", required)}
    </Label>
    <Input
      id="authority"
      required={required}
      placeholder={getInputPlaceholder("authority", { label: "authority", type: "text" })}
      value={value || ""}
      onChange={(event) => onChange(event.target.value)}
    />
  </div>
);

export const FallbackSchemaNotice = () => (
  <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
    Live event schema is unavailable. Using offline fallback schema.
  </div>
);

export const RemarksField = ({ value, onChange }) => (
  <div className="space-y-1.5">
    <Label htmlFor="remarks">Remarks</Label>
    <Input
      id="remarks"
      placeholder={getInputPlaceholder("remarks", { label: "remarks", type: "text" })}
      value={value || ""}
      onChange={(event) => onChange(event.target.value)}
    />
  </div>
);

export const RecordDialogActions = ({ saving, onCancel }) => (
  <SheetFooter className="mt-4">
    <Button
      type="button"
      variant="outline"
      onClick={onCancel}
      disabled={saving}
    >
      Cancel
    </Button>
    <Button type="submit" disabled={saving} className="gap-1">
      {saving && <Loader2 className="w-4 h-4 animate-spin" />}
      Record Event
    </Button>
  </SheetFooter>
);
