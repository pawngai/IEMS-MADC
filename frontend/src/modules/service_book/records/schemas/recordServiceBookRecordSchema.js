import { z } from "zod";

export const recordServiceBookRecordSchema = z.object({
  employee_id: z.string().min(1),
  event_type: z.string().min(1),
  effective_from: z.string().min(1),
  order_number: z.string().min(1),
  order_date: z.string().min(1),
  issuing_authority: z.string().min(1),
  payload: z.record(z.string(), z.unknown()).default({}),
});

export const recordServiceBookRecordDefaultValues = {
  employee_id: "",
  event_type: "",
  effective_from: "",
  order_number: "",
  order_date: "",
  issuing_authority: "",
  payload: {},
};
