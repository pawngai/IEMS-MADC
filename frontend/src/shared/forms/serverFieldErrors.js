/**
 * Map a FastAPI 422 validation error onto React Hook Form field errors.
 *
 * Detail entries look like { loc: ["body", "field"], msg } or carry an
 * explicit field/field_id. Returns true when at least one field error was
 * applied, so callers can decide whether a fallback toast is still needed.
 */
export function applyServerFieldErrors(form, error) {
  const detail = error?.response?.data?.detail;
  if (!Array.isArray(detail)) return false;

  let applied = false;
  for (const issue of detail) {
    const field = issue?.loc?.[1] || issue?.field || issue?.field_id;
    if (!field) continue;
    form.setError(String(field), {
      type: "server",
      message: issue?.msg || issue?.message || "Invalid value",
    });
    applied = true;
  }
  return applied;
}
