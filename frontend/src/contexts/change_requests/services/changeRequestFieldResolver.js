export const PROFILE_FIELD_ALIASES = {
  mobile_number: "mobile_primary",
  alternate_mobile: "mobile_alternate",
  personal_email: "email_personal",
  emergency_contact_name: "emergency_name",
  emergency_contact_number: "emergency_phone",
  emergency_contact_phone: "emergency_phone",
  emergency_contact_relation: "emergency_relation",
  current_address_line1: "address_line1",
  current_address_line2: "address_line2",
  current_city: "city",
  current_state_code: "state",
  current_pincode: "pincode",
};

export const PROFILE_FIELD_PATHS = {
  mobile_primary: ["contact.mobile_primary", "mobile_primary", "contact.mobile_number", "mobile_number"],
  mobile_alternate: ["contact.mobile_alternate", "mobile_alternate", "contact.alternate_mobile", "alternate_mobile"],
  email_personal: ["contact.email_personal", "email_personal", "contact.personal_email", "personal_email"],
  emergency_name: ["contact.emergency_name", "emergency_name", "contact.emergency_contact_name", "emergency_contact_name"],
  emergency_phone: ["contact.emergency_phone", "emergency_phone", "contact.emergency_contact_number", "emergency_contact_number", "contact.emergency_contact_phone", "emergency_contact_phone"],
  emergency_relation: ["contact.emergency_relation", "emergency_relation", "contact.emergency_contact_relation", "emergency_contact_relation"],
  address_line1: ["contact.address_line1", "address_line1", "current_address_line1"],
  address_line2: ["contact.address_line2", "address_line2", "current_address_line2"],
  city: ["contact.city", "city", "current_city"],
  district: ["contact.district", "district"],
  state: ["contact.state", "state", "current_state_code"],
  pincode: ["contact.pincode", "pincode", "current_pincode"],
  aadhaar_number: ["identifiers.aadhaar_number", "aadhaar_number"],
  pan_number: ["identifiers.pan_number", "pan_number"],
};

export const getValueByPath = (obj, path) => {
  if (!obj || !path) return undefined;
  return path.split(".").reduce((acc, key) => {
    if (acc == null || typeof acc !== "object") return undefined;
    return acc[key];
  }, obj);
};

// Helper to summarise an entry into a human-readable label
export const entryLabel = (entry, type) => {
  switch (type) {
    case "service_history":
      return `${entry.event_type || "Event"} \u2014 ${entry.post_held || ""} (${entry.period_from || "?"} to ${entry.period_to || "Present"})`;
    case "previous_service":
      return `${entry.post_held || "Post"} at ${entry.organization || "Org"} (${entry.service_from || "?"} to ${entry.service_to || "?"})`;
    case "foreign_service":
      return `${entry.post_held || "Post"} at ${entry.employer || "Employer"} (${entry.service_from || "?"} to ${entry.service_to || "?"})`;
    case "verification":
      return `${entry.post_held || "Post"} (${entry.period_from || "?"} to ${entry.period_to || "?"})`;
    case "leave_transaction":
      return `${entry.leave_type || "Leave"} \u2014 ${entry.transaction_type || ""} (${entry.transaction_date || "?"})`;
    case "ltc":
      return `LTC ${entry.ltc_type || ""} \u2014 ${entry.block_year || ""} (${entry.journey_from || "?"} \u2192 ${entry.journey_to || "?"})`;
    case "hba":
      return `HBA \u20B9${entry.amount_sanctioned?.toLocaleString() || "?"} \u2014 ${entry.purpose || ""} (${entry.sanction_date || "?"})`;
    case "audit_comment": {
      const sev = entry.severity || "?";
      const aType = entry.audit_type || "Audit";
      const txt = (entry.comment_text || "").slice(0, 50);
      return sev + " | " + aType + " - " + txt;
    }
    default:
      return entry.id || "Entry";
  }
};
