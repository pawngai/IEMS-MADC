import { z } from "zod";

export const employeeIdentityFormSchema = z.object({
  employee_id: z.string().optional(),
  full_name: z.string().min(1),
  date_of_birth: z.string().optional(),
  gender: z.string().optional(),
});
