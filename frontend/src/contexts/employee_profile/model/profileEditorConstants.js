export const TYPE_SPECIFIC_FIELDS = {
  REGULAR: [],
  CONTRACTUAL: [
    { id: "contract_order_no", label: "Contract Order No", type: "text", required: true, placeholder: "CON/2025/001" },
    { id: "contract_start_date", label: "Contract Start Date", type: "date", required: true },
    { id: "contract_end_date", label: "Contract End Date", type: "date", required: true },
    { id: "consolidated_pay", label: "Monthly Remuneration (Rs)", type: "number", required: true, placeholder: "50000" },
    { id: "contract_authority", label: "Contracting Authority", type: "text", required: true, placeholder: "Director HR" },
    {
      id: "renewal_allowed",
      label: "Renewal Allowed",
      type: "select",
      required: true,
      options: [
        { value: "YES", label: "Yes" },
        { value: "NO", label: "No" },
      ],
    },
  ],
  DAILY_WAGE: [
    { id: "engagement_order_no", label: "Engagement Order No", type: "text", required: true, placeholder: "DW/2025/001" },
    { id: "muster_roll_number", label: "Muster Roll Number", type: "text", required: true, placeholder: "MR-2025-001" },
    { id: "daily_wage_rate", label: "Daily Wage Rate (Rs)", type: "number", required: true, placeholder: "500" },
    { id: "engagement_office", label: "Engagement Office", type: "text", required: true, placeholder: "District Office, North Delhi" },
    { id: "nature_of_work", label: "Nature of Work", type: "text", required: true, placeholder: "Office Assistant / Data Entry" },
    { id: "expected_duration_days", label: "Expected Duration (Days)", type: "number", required: false, placeholder: "180" },
  ],
  DEPUTATION: [
    { id: "deputation_order_no", label: "Deputation Order No", type: "text", required: true, placeholder: "DEP/2025/001" },
    { id: "parent_department", label: "Parent Department", type: "text", required: true, placeholder: "Ministry of Finance" },
    { id: "parent_designation", label: "Parent Designation", type: "text", required: true, placeholder: "Section Officer" },
    {
      id: "lien_status",
      label: "Lien Status",
      type: "select",
      required: true,
      options: [
        { value: "RETAINED", label: "Lien Retained" },
        { value: "SUSPENDED", label: "Lien Suspended" },
      ],
    },
    { id: "deputation_start_date", label: "Deputation Start Date", type: "date", required: true },
    { id: "deputation_end_date", label: "Deputation End Date", type: "date", required: true },
    { id: "deputation_allowance_percent", label: "Deputation Allowance (%)", type: "number", required: false, placeholder: "10" },
  ],
};
