import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

/**
 * Standard form hook: React Hook Form validated by a Zod schema.
 * All app forms should use this instead of hand-rolled formData/errors state
 * so validation rules live in one schema per form.
 */
export function useZodForm({ schema, ...options }) {
  return useForm({
    resolver: zodResolver(schema),
    mode: "onSubmit",
    ...options,
  });
}
