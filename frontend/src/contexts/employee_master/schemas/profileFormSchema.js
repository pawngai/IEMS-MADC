import { z } from "zod";

export const employeeProfileFormSchema = z.object({
  employee_id: z.string().min(1),
  current_department_id: z.string().optional(),
  current_designation_id: z.string().optional(),
  employment_type: z.string().optional(),
  employee_status: z.string().optional(),
});
