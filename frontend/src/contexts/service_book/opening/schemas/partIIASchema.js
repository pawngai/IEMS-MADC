export const partIIASchema = {
  id: "part_iia",
  required: [
    "medical_fitness_certificate",
    "character_verification_done",
    "entries_confirmed",
  ],
  fields: [
    {
      name: "medical_fitness_certificate",
      label: "Medical Fitness Certificate",
      type: "boolean",
      documentUpload: { buttonLabel: "Upload medical certificate" },
    },
    { name: "medical_exam_date", label: "Medical Exam Date", type: "date" },
    { name: "medical_officer_name", label: "Medical Officer" },
    { name: "medical_category", label: "Medical Category" },
    {
      name: "character_verification_done",
      label: "Character Verification",
      type: "boolean",
      documentUpload: { buttonLabel: "Upload character verification" },
    },
    { name: "character_verification_date", label: "Character Verification Date", type: "date" },
    { name: "character_verification_authority", label: "Character Verification Authority" },
    {
      name: "police_verification_done",
      label: "Police Verification",
      type: "boolean",
      documentUpload: { buttonLabel: "Upload police verification" },
    },
    { name: "police_verification_date", label: "Police Verification Date", type: "date" },
    {
      name: "oath_of_allegiance_taken",
      label: "Oath of Allegiance",
      type: "boolean",
      documentUpload: { buttonLabel: "Upload oath of allegiance" },
    },
    { name: "oath_of_allegiance_date", label: "Oath of Allegiance Date", type: "date" },
    {
      name: "oath_of_secrecy_taken",
      label: "Oath of Secrecy",
      type: "boolean",
      documentUpload: { buttonLabel: "Upload oath of secrecy" },
    },
    { name: "oath_of_secrecy_date", label: "Oath of Secrecy Date", type: "date" },
    {
      name: "entries_confirmed",
      label: "Confirmation of Entries",
      type: "boolean",
      documentUpload: { buttonLabel: "Upload confirmation document" },
    },
    { name: "confirmation_date", label: "Confirmation Date", type: "date" },
    { name: "confirming_officer", label: "Confirming Officer" },
    { name: "marital_status_declaration_date", label: "Marital Status Declaration Date", type: "date" },
    { name: "declared_hometown", label: "Declared Hometown" },
    { name: "hometown_declaration_date", label: "Hometown Declaration Date", type: "date" },
  ],
  sections: [
    {
      id: "medical",
      title: "Medical Fitness",
      description: "Capture the employee's medical fitness certificate and the certifying examination details.",
      fields: [
        "medical_fitness_certificate",
        "medical_exam_date",
        "medical_officer_name",
        "medical_category",
      ],
    },
    {
      id: "character",
      title: "Character Verification",
      description: "Record the outcome and authority details for the employee's character verification.",
      fields: [
        "character_verification_done",
        "character_verification_date",
        "character_verification_authority",
      ],
    },
    {
      id: "police",
      title: "Police Verification",
      description: "Track whether police verification was completed and when it was recorded.",
      fields: [
        "police_verification_done",
        "police_verification_date",
      ],
    },
    {
      id: "oath_allegiance",
      title: "Oath of Allegiance",
      description: "Store the oath of allegiance acknowledgement and supporting document.",
      fields: [
        "oath_of_allegiance_taken",
        "oath_of_allegiance_date",
      ],
    },
    {
      id: "oath_secrecy",
      title: "Oath of Secrecy",
      description: "Store the oath of secrecy acknowledgement and supporting document.",
      fields: [
        "oath_of_secrecy_taken",
        "oath_of_secrecy_date",
      ],
    },
    {
      id: "entries_confirmation",
      title: "Confirmation of Entries",
      description: "Capture the final confirmation that the opening entries were checked and confirmed.",
      fields: [
        "entries_confirmed",
        "confirmation_date",
        "confirming_officer",
      ],
    },
    {
      id: "marital_status_declaration",
      title: "Marital Status Declaration",
      description: "Record when the employee's marital status declaration was submitted for Part II-A.",
      fields: [
        "marital_status_declaration_date",
      ],
    },
    {
      id: "hometown_declaration",
      title: "Hometown Declaration",
      description: "Record the declared hometown and the date the hometown declaration was made for Part II-A.",
      fields: [
        "declared_hometown",
        "hometown_declaration_date",
      ],
    },
  ],
};
