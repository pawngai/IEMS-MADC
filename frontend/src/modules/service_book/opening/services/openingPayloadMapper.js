const coalesce = (...values) =>
  values.find((value) => value !== undefined && value !== null && String(value).trim() !== "") || "";

export const mapIdentityProfileToPartIDefaults = ({ identity = {}, profile = {} } = {}) => ({
  employee_id: coalesce(identity.employee_id, profile.employee_id),
  employee_code: coalesce(identity.employee_code, profile.employee_code),
  name_in_block_letters: String(coalesce(
    identity.name_in_block_letters,
    identity.full_name,
    profile.name_in_block_letters,
    profile.full_name,
    profile.name
  )).toUpperCase(),
  date_of_birth_christian: coalesce(identity.date_of_birth_christian, identity.date_of_birth, profile.date_of_birth_christian, profile.date_of_birth),
  father_name: coalesce(identity.father_name, profile.father_name),
  mother_name: coalesce(identity.mother_name, profile.mother_name),
  spouse_name: coalesce(identity.spouse_name, profile.spouse_name),
  marital_status: coalesce(identity.marital_status, profile.marital_status),
  nationality: coalesce(identity.nationality, profile.nationality),
  caste_category: coalesce(identity.caste_category, identity.category, profile.caste_category, profile.category),
  religion: coalesce(identity.religion, profile.religion),
  blood_group: coalesce(identity.blood_group, profile.blood_group),
  place_of_birth: coalesce(identity.place_of_birth, profile.place_of_birth),
  height_cm: coalesce(identity.height_cm, profile.height_cm),
  identification_marks: coalesce(identity.identification_marks, profile.identification_marks),
  permanent_address_line1: coalesce(identity.permanent_address_line1, profile.permanent_address_line1),
  permanent_address_line2: coalesce(identity.permanent_address_line2, profile.permanent_address_line2),
  educational_qualifications_initial: coalesce(identity.educational_qualifications_initial, profile.educational_qualifications_initial),
  educational_qualifications_acquired: coalesce(identity.educational_qualifications_acquired, profile.educational_qualifications_acquired),
  professional_qualifications: coalesce(identity.professional_qualifications, profile.professional_qualifications),
  attesting_officer_name: coalesce(identity.attesting_officer_name, profile.attesting_officer_name),
  attesting_officer_designation: coalesce(identity.attesting_officer_designation, profile.attesting_officer_designation),
});

export const mapDraftToOpeningPayload = ({ employeeId, draft }) => ({
  employee_id: employeeId,
  parts: {
    part_i: { ...(draft?.parts?.part_i || {}) },
    part_iia: { ...(draft?.parts?.part_iia || {}) },
    part_iib: { ...(draft?.parts?.part_iib || {}) },
    part_iii: { ...(draft?.parts?.part_iii || {}) },
  },
  documents: Array.isArray(draft?.documents) ? draft.documents : [],
});

export const normalizeOpeningDraft = ({ employeeId, opening, partIDefaults }) => {
  const parts = opening?.parts || {};
  return {
    id: opening?.id || opening?.opening_id || null,
    employee_id: opening?.employee_id || employeeId,
    status: opening?.status || opening?.workflow_status || "NOT_STARTED",
    parts: {
      part_i: { ...(partIDefaults || {}), ...(parts.part_i || opening?.part_i || {}) },
      part_iia: { ...(parts.part_iia || opening?.part_iia || {}) },
      part_iib: { ...(parts.part_iib || opening?.part_iib || {}) },
      part_iii: { ...(parts.part_iii || opening?.part_iii || {}) },
    },
    documents: Array.isArray(opening?.documents) ? opening.documents : [],
    remarks: opening?.remarks || "",
  };
};
