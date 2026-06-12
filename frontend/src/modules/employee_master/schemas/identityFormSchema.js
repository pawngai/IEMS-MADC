import { z } from "zod";

const MOBILE_PATTERN = /^[6-9]\d{9}$/;
const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/**
 * Core identity form schema. Employment type is required only when creating
 * a non-regular employee (the editor seeds the profile extension with it).
 */
export const buildEmployeeIdentityFormSchema = ({ requireEmploymentType = false } = {}) =>
  z.object({
    full_name: z
      .string()
      .trim()
      .min(1, "Full name is required"),
    gender: z.string().min(1, "Gender is required"),
    date_of_birth: z.string().min(1, "Date of birth is required"),
    mobile_primary: z
      .string()
      .refine((value) => !value || MOBILE_PATTERN.test(value), "Enter a valid 10-digit mobile number"),
    email_official: z
      .string()
      .refine((value) => !value.trim() || EMAIL_PATTERN.test(value.trim()), "Enter a valid official email"),
    employment_type: requireEmploymentType
      ? z.string().min(1, "Employment type is required for non-regular employees")
      : z.string(),
  });

export const employeeIdentityFormSchema = buildEmployeeIdentityFormSchema();
