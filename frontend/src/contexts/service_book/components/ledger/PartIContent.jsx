import { Label } from '@/shared/ui/label';
import { AuthImage } from '@/platform/auth/AuthImage';
import {
  DataField,
  EmptyPartPlaceholder,
} from '@/contexts/service_book/components/serviceBookLedgerPrimitives';
import {
  formatDisplayDate,
  listToDisplayLines,
} from '@/contexts/service_book/components/serviceBookPartHelpers';

const toTitleCase = (value) => String(value || '')
  .trim()
  .toLowerCase()
  .replace(/\b\w/g, (char) => char.toUpperCase());

const formatAllCapsText = (value) => {
  const normalized = String(value || '').trim();
  if (!normalized) return null;
  if (/[a-z]/.test(normalized)) return normalized;
  if (!/[A-Z]/.test(normalized)) return normalized;
  return toTitleCase(normalized);
};

const formatMaritalStatus = (value) => {
  const normalized = String(value || '').trim().toUpperCase();
  if (!normalized) return null;
  return normalized
    .toLowerCase()
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

const formatCasteCategory = (value, options = []) => {
  const normalized = String(value || '').trim();
  if (!normalized) return null;

  const mapped = (options || []).find((option) => String(option?.value || option).trim().toUpperCase() === normalized.toUpperCase());
  const label = mapped?.label || mapped?.name || normalized;
  const upper = String(label).trim().toUpperCase();

  if (upper === 'GEN' || upper === 'GENERAL') return 'General';
  return label;
};

const PartIContent = ({ data, casteCategoryOptions }) => {
  if (!data) {
    return <EmptyPartPlaceholder message="No bio-data has been finalized yet." />;
  }

  const permanentAddress = data.permanent_address || {
    line1: data.permanent_address_line1,
    line2: data.permanent_address_line2,
    city: data.permanent_city,
    state: data.permanent_state_code,
    pin: data.permanent_pincode,
    country: data.permanent_country,
  };

  const photoUrl = data.photograph_url;
  const sigUrl = data.signature_url;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
      <div className="col-span-2 flex items-start gap-4 mb-2">
        {photoUrl ? (
          <AuthImage path={photoUrl} alt="Employee photograph" className="w-24 h-28 object-cover rounded border border-gray-300"
            fallback={<div className="w-24 h-28 bg-gray-100 border border-dashed border-gray-300 rounded flex items-center justify-center text-xs text-gray-400">No Photo</div>}
          />
        ) : (
          <div className="w-24 h-28 bg-gray-100 border border-dashed border-gray-300 rounded flex items-center justify-center text-xs text-gray-400">No Photo</div>
        )}
        <div>
          <div className="font-semibold text-gray-900 text-base">{formatAllCapsText(data.name_in_block_letters) || '-'}</div>
          {data.employee_code && <div className="text-xs text-gray-500 mt-1">Employee Code: {data.employee_code}</div>}
        </div>
      </div>

      <DataField label="Parent's Name" value={formatAllCapsText(data.parent_name || data.father_name)} />
      <DataField label="Spouse's Name (if married)" value={formatAllCapsText(data.spouse_name)} />
      <DataField label="Marital Status" value={formatMaritalStatus(data.marital_status)} />
      <DataField label="Nationality" value={data.nationality} />
      <DataField label="Caste Category" value={formatCasteCategory(data.caste_category, casteCategoryOptions)} />
      <DataField label="Date of Birth (Christian era)" value={formatDisplayDate(data.date_of_birth_christian)} />
      <DataField label="Date of Birth (Saka era)" value={data.date_of_birth_saka} />
      <DataField label="Exact Height (cm)" value={data.height_cm} />
      <DataField label="Identification Marks" value={Array.isArray(data.identification_marks) ? data.identification_marks.join('; ') : data.identification_marks} />
      <DataField
        label="Permanent Address"
        value={[
          permanentAddress.line1,
          permanentAddress.line2,
          permanentAddress.city,
          permanentAddress.state,
          permanentAddress.pin,
          permanentAddress.country,
        ].filter(Boolean).join(', ')}
      />

      <div>
        <Label className="text-gray-500 text-xs">Signature</Label>
        {sigUrl ? (
          <AuthImage path={sigUrl} alt="Employee signature" className="mt-1 h-12 object-contain border-b border-gray-300" />
        ) : (
          <div className="text-gray-400 text-sm italic mt-1">Not uploaded</div>
        )}
      </div>

      <DataField label="Thumb Impression" value={data.thumb_impression_url ? 'On file' : null} />
      <DataField label="Attesting Officer Name" value={data.attesting_officer_name} />
      <DataField label="Attesting Officer Designation" value={data.attesting_officer_designation} />

      {data.educational_qualifications_initial?.length > 0 && (
        <div className="col-span-2">
          <Label className="text-gray-500 text-xs">Educational Qualifications (Initial)</Label>
          <div className="mt-1 space-y-1 text-gray-700">
            {listToDisplayLines(data.educational_qualifications_initial).map((line, idx) => (
              <div key={idx}>{line}</div>
            ))}
          </div>
        </div>
      )}

      {data.educational_qualifications_acquired?.length > 0 && (
        <div className="col-span-2">
          <Label className="text-gray-500 text-xs">Educational Qualifications (Acquired)</Label>
          <div className="mt-1 space-y-1 text-gray-700">
            {listToDisplayLines(data.educational_qualifications_acquired).map((line, idx) => (
              <div key={idx}>{line}</div>
            ))}
          </div>
        </div>
      )}

      {data.professional_qualifications?.length > 0 && (
        <div className="col-span-2">
          <Label className="text-gray-500 text-xs">Professional/Technical Qualifications</Label>
          <div className="mt-1 space-y-1 text-gray-700">
            {listToDisplayLines(data.professional_qualifications).map((line, idx) => (
              <div key={idx}>{line}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PartIContent;
