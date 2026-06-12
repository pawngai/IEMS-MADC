import { AlertCircle, CheckCircle, FileText } from 'lucide-react';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { SearchableSelect } from '@/shared/ui/searchable-select';
import { formatDisplayDate } from '@/modules/service_book/components/serviceBookPartHelpers';

export function EmptyPartPlaceholder({ message }) {
  return (
    <div className="text-center py-8 text-gray-500">
      <FileText className="h-8 w-8 mx-auto mb-2 text-gray-300" />
      <p>{message}</p>
    </div>
  );
}

export function FormField({ label, type = 'text', value, onChange, disabled = false }) {
  return (
    <div>
      <Label className="text-sm font-medium text-gray-700">{label}</Label>
      <Input
        type={type}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1"
        disabled={disabled}
      />
    </div>
  );
}

export function SelectField({ label, value, onChange, options, disabled = false }) {
  const normalizedOptions = (options || []).map((opt) =>
    typeof opt === 'string' ? { value: opt, label: opt } : opt
  );

  return (
    <div>
      <Label className="text-sm font-medium text-gray-700">{label}</Label>
      <SearchableSelect
        value={value || ''}
        onValueChange={(v) => onChange(v)}
        options={normalizedOptions}
        placeholder="Select..."
        disabled={disabled}
        className="mt-1"
      />
    </div>
  );
}

export function TextAreaField({ label, value, onChange, rows = 3 }) {
  return (
    <div>
      <Label className="text-sm font-medium text-gray-700">{label}</Label>
      <textarea
        className="w-full mt-1 p-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows={rows}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

export function CheckboxField({ label, checked, onChange }) {
  return (
    <div className="flex items-center gap-2">
      <input
        type="checkbox"
        checked={checked || false}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 rounded border-gray-300"
      />
      <Label className="text-sm font-medium text-gray-700">{label}</Label>
    </div>
  );
}

export function DataField({ label, value }) {
  return (
    <div>
      <Label className="text-gray-500 text-xs">{label}</Label>
      <div className={value ? "text-gray-900" : "text-gray-400 italic"}>{value || 'Not provided'}</div>
    </div>
  );
}

export function BooleanField({ label, value, date }) {
  const displayDate = date ? formatDisplayDate(date) : null;

  return (
    <div className="flex items-center gap-2">
      {value ? (
        <CheckCircle className="h-4 w-4 text-green-600" />
      ) : (
        <AlertCircle className="h-4 w-4 text-gray-400" />
      )}
      <div>
        <div className="text-gray-900">{label}</div>
        {displayDate && <div className="text-xs text-gray-500">{displayDate}</div>}
      </div>
    </div>
  );
}
