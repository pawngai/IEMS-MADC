const EMPLOYMENT_TYPE_ALIASES = {
  REG: "REGULAR",
  REGULAR: "REGULAR",
  CONTRACT: "CONTRACTUAL",
  CONTRACTUAL: "CONTRACTUAL",
  DAILYWAGE: "DAILY_WAGE",
  DAILY_WAGE: "DAILY_WAGE",
  DEPUTATION: "DEPUTATION",
  REEMPLOYED: "REEMPLOYED",
  REEMPLOYMENT: "REEMPLOYED",
  OUTSOURCED: "OUTSOURCED",
};

export const determineEmploymentType = (employeeOrType) => {
  const raw =
    typeof employeeOrType === "object" && employeeOrType !== null
      ? employeeOrType.current_employment_type_code || employeeOrType.employment_type || employeeOrType.employment_type_code
      : employeeOrType;

  const normalized = String(raw || "").trim().toUpperCase();
  if (!normalized) return "";
  return EMPLOYMENT_TYPE_ALIASES[normalized] || normalized;
};

export const isServiceBookEligible = (employeeOrType) =>
  typeof employeeOrType === "object" && employeeOrType !== null && "eligible_for_service_book" in employeeOrType
    ? Boolean(employeeOrType.eligible_for_service_book)
    : determineEmploymentType(employeeOrType) === "REGULAR";

const NON_REGULAR_EMPLOYMENT_TYPES = new Set([
  "CONTRACT",
  "CONTRACTUAL",
  "MUSTER_ROLL",
  "FIXED_PAY",
  "CO_TERMINUS",
  "WAGES",
  "DAILY_WAGE",
  "DAILY_RATED",
  "CASUAL",
  "PART_TIME",
]);

export const isNonRegularEmploymentType = (employeeOrType) => {
  if (
    typeof employeeOrType === "object"
    && employeeOrType !== null
    && employeeOrType.current_employment_class
  ) {
    return String(employeeOrType.current_employment_class).trim().toUpperCase() === "NON_REGULAR";
  }
  return NON_REGULAR_EMPLOYMENT_TYPES.has(determineEmploymentType(employeeOrType));
};