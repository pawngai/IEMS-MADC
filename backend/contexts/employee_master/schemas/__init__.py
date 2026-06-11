"""Employee Master canonical schemas.

Employee Master is the canonical owner of current employee facts: identity,
appointment-time facts, current assignment, contact/profile/media/completion.
These models merge the former employee_identity + employee_profile schemas with
zero field loss. See docs/refactor/current_fields_inventory.md and
docs/refactor/employee_identity_profile_field_mapping.md.
"""
