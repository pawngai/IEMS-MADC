export const partIIISchema = {
  id: "part_iii",
  required: [],
  fields: [
    {
      name: "previous_services",
      label: "Previous Services",
      type: "textarea",
      documentUpload: { buttonLabel: "Upload previous service document" },
    },
    {
      name: "total_previous_qualifying_service",
      label: "Total Previous Qualifying Service",
      type: "textarea",
    },
    {
      name: "foreign_services",
      label: "Foreign Services",
      type: "textarea",
      documentUpload: { buttonLabel: "Upload foreign service document" },
    },
  ],
};