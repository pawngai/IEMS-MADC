/**
 * Static schema describing all 9 Service Book parts.
 * Used by the projection API and UI to describe part structure.
 */
export const PARTS_INFO = {
  I: {
    name: "Bio-Data",
    description: "Basic personal information recorded at appointment",
    editable_after_attestation: false,
    fields: [
      "Photograph",
      "Name (Block Letters)",
      "Parent's Name",
      "Spouse's Name (if married)",
      "Nationality",
      "Caste Category (SC/ST/OBC etc.)",
      "Date of Birth (Christian & Saka era)",
      "Educational Qualifications (Initial & Acquired)",
      "Professional/Technical Qualifications",
      "Exact Height",
      "Personal Identification Marks",
      "Permanent Home Address",
      "Signature/Thumb Impression of Government Servant",
      "Attesting Officer Signature & Designation",
    ],
  },
  "II-A": {
    name: "Immutable Certificates",
    description: "Fixed records at appointment that cannot change",
    editable_after_attestation: false,
    fields: [
      "Medical Fitness Certificate",
      "Character Verification",
      "Oath of Allegiance",
      "Oath of Secrecy",
      "Marital Status Declaration",
      "Hometown Declaration",
      "Confirmation of Entries",
    ],
  },
  "II-B": {
    name: "Mutable Certificates",
    description: "Records that may change during service",
    editable_after_attestation: true,
    fields: [
      "Family Particulars",
      "PCF Account & Nomination",
      "DCR Gratuity & Family Pension",
      "NPS PRAN & Nomination",
      "Leave Encashment Nomination",
    ],
  },
  III: {
    name: "Service History Outside Current Appointment",
    description: "Prior service records for pension calculation",
    editable_after_attestation: false,
    fields: ["Previous Qualifying Service", "Foreign Service Records", "Leave & Pension Contributions"],
  },
  IV: {
    name: "History of Service",
    description: "Detailed chronology of employment",
    editable_after_attestation: false,
    fields: ["Period (From/To)", "Office/Station", "Post Held", "Pay Band & Grade Pay", "Events", "Signatures"],
  },
  V: {
    name: "Verification of Service",
    description: "Verified service details for pension",
    editable_after_attestation: false,
    fields: ["Verified Service Details", "Supporting Documents", "Certifying Officer Details"],
  },
  VI: {
    name: "Leave Account",
    description: "Detailed leave ledger",
    editable_after_attestation: true,
    fields: ["Earned Leave", "Half Pay Leave", "Leave Availed", "Dies Non", "Leave Balances"],
  },
  VII: {
    name: "Other Records",
    description: "LTC and advance records",
    editable_after_attestation: true,
    fields: ["Leave Travel Concession", "House Building Advance", "Vehicle Advance", "Festival Advance"],
  },
  VIII: {
    name: "Internal Audit Comments",
    description: "Audit remarks and compliance notes",
    editable_after_attestation: true,
    fields: ["Audit Comments", "Observations", "Responses", "Resolutions"],
  },
};
