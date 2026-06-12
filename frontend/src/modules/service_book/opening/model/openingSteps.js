export const OPENING_STEPS = [
  {
    id: "part_i",
    label: "Part I",
    title: "Bio-Data",
    requiredFields: [
      "name_in_block_letters",
      "father_name",
      "marital_status",
      "caste_category",
      "date_of_birth_christian",
    ],
  },
  {
    id: "part_iia",
    label: "Part II-A",
    title: "Immutable Certificates",
    requiredFields: [
      "medical_fitness_certificate",
      "character_verification_done",
      "entries_confirmed",
    ],
  },
  {
    id: "part_iib",
    label: "Part II-B",
    title: "Mutable Certificates",
    requiredFields: [],
  },
  {
    id: "part_iii",
    label: "Part III",
    title: "Previous and foreign service details",
    requiredFields: [],
  },
];

export const OPENING_STEP_IDS = OPENING_STEPS.map((step) => step.id);

export const getOpeningStep = (stepId) =>
  OPENING_STEPS.find((step) => step.id === stepId) || OPENING_STEPS[0];
