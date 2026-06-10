"""Field-level edit and immutability policy constants."""

from __future__ import annotations

# Fields that Data Entry can modify on the core identity record.
DATA_ENTRY_EDITABLE_FIELDS = {
    "full_name",
    "gender",
    "date_of_birth",
    "current_designation_id",
    "current_office_id",
    "reporting_officer_id",
    "employee_status",
    "status_effective_date",
    "status_remarks",
}

