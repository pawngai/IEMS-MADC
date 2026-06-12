import { partISchema } from "@/modules/service_book/opening/schemas/partISchema";
import { partIIASchema } from "@/modules/service_book/opening/schemas/partIIASchema";
import { partIIBSchema } from "@/modules/service_book/opening/schemas/partIIBSchema";
import { partIIISchema } from "@/modules/service_book/opening/schemas/partIIISchema";

export const openingSchema = {
  parts: {
    part_i: partISchema,
    part_iia: partIIASchema,
    part_iib: partIIBSchema,
    part_iii: partIIISchema,
  },
};

export const validateOpeningPart = (part, schema) => {
  const data = part || {};
  return (schema.required || []).filter((field) => {
    const value = data[field];
    return value === undefined || value === null || String(value).trim() === "";
  });
};
