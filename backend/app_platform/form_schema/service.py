# Form Rules Engine - Business Logic Separated from Structure

import copy
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

from dateutil.relativedelta import relativedelta


class RuleType(str, Enum):
    VISIBILITY = "visibility"
    REQUIRED = "required"
    READONLY = "readonly"
    COMPUTED = "computed"
    VALIDATION = "validation"


class EmploymentType(str, Enum):
    REGULAR = "REGULAR"
    CONTRACTUAL = "CONTRACTUAL"
    DAILY_WAGE = "DAILY_WAGE"
    DEPUTATION = "DEPUTATION"
    REEMPLOYED = "REEMPLOYED"
    OUTSOURCED = "OUTSOURCED"
    CONTRACT = "CONTRACT"
    MUSTER_ROLL = "MUSTER_ROLL"
    FIXED_PAY = "FIXED_PAY"
    CO_TERMINUS = "CO_TERMINUS"
    WAGES = "WAGES"


class WorkflowStage(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    ATTESTED = "ATTESTED"
    LOCKED = "LOCKED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


FINALIZED_WORKFLOW_STAGES = {WorkflowStage.ATTESTED, WorkflowStage.LOCKED}

CONTRACT_LIKE_EMPLOYMENT_TYPES = {
    EmploymentType.CONTRACTUAL,
    EmploymentType.CONTRACT,
}
WAGE_LIKE_EMPLOYMENT_TYPES = {
    EmploymentType.DAILY_WAGE,
    EmploymentType.MUSTER_ROLL,
    EmploymentType.WAGES,
}
PAY_SCALE_EMPLOYMENT_TYPES = {
    EmploymentType.REGULAR,
    EmploymentType.DEPUTATION,
    EmploymentType.REEMPLOYED,
    EmploymentType.CO_TERMINUS,
}


def _parse_employment_type(employment_type: Optional[str]) -> Optional[EmploymentType]:
    if employment_type in (None, ""):
        return None
    try:
        return EmploymentType(employment_type)
    except ValueError as exc:
        allowed = ", ".join([item.value for item in EmploymentType])
        raise ValueError(
            f"Invalid employment_type '{employment_type}'. Allowed values: {allowed}"
        ) from exc


def _parse_workflow_stage(workflow_stage: str) -> WorkflowStage:
    try:
        return WorkflowStage(workflow_stage)
    except ValueError as exc:
        allowed = ", ".join([item.value for item in WorkflowStage])
        raise ValueError(
            f"Invalid workflow_stage '{workflow_stage}'. Allowed values: {allowed}"
        ) from exc


@dataclass
class RuleContext:
    form_data: Dict[str, Any] = field(default_factory=dict)
    employment_type: Optional[EmploymentType] = None
    workflow_stage: WorkflowStage = WorkflowStage.DRAFT
    user_role: Optional[str] = None
    is_edit_mode: bool = False
    record_id: Optional[str] = None

    @classmethod
    def from_request(cls, data: Dict) -> "RuleContext":
        emp_type = data.get("employment_type")
        if emp_type:
            try:
                emp_type = EmploymentType(emp_type)
            except ValueError:
                emp_type = None

        stage = data.get("workflow_stage", data.get("status", "DRAFT"))
        try:
            stage = WorkflowStage(stage)
        except ValueError:
            stage = WorkflowStage.DRAFT

        return cls(
            form_data=data.get("form_data", data),
            employment_type=emp_type,
            workflow_stage=stage,
            user_role=data.get("user_role"),
            is_edit_mode=data.get("is_edit_mode", False),
            record_id=data.get("record_id"),
        )


def _is_married_status(value: Any) -> bool:
    return str(value or "").strip().upper() == "MARRIED"


VISIBILITY_RULES: Dict[str, Callable[[RuleContext], bool]] = {
    "marital_status": lambda ctx: True,
    "spouse_name": lambda ctx: _is_married_status(ctx.form_data.get("marital_status")),
    "father_husband_name": lambda ctx: ctx.employment_type == EmploymentType.REGULAR,
    "mother_name": lambda ctx: True,
    "contract_start_date": lambda ctx: ctx.employment_type in CONTRACT_LIKE_EMPLOYMENT_TYPES,
    "contract_end_date": lambda ctx: ctx.employment_type in CONTRACT_LIKE_EMPLOYMENT_TYPES,
    "contract_renewal_count": lambda ctx: ctx.employment_type in CONTRACT_LIKE_EMPLOYMENT_TYPES,
    "consolidated_pay": lambda ctx: ctx.employment_type in CONTRACT_LIKE_EMPLOYMENT_TYPES,
    "daily_rate": lambda ctx: ctx.employment_type in WAGE_LIKE_EMPLOYMENT_TYPES,
    "muster_roll_number": lambda ctx: ctx.employment_type in WAGE_LIKE_EMPLOYMENT_TYPES,
    "parent_department_code": lambda ctx: ctx.employment_type == EmploymentType.DEPUTATION,
    "deputation_start_date": lambda ctx: ctx.employment_type == EmploymentType.DEPUTATION,
    "deputation_end_date": lambda ctx: ctx.employment_type == EmploymentType.DEPUTATION,
    "deputation_tenure_years": lambda ctx: ctx.employment_type == EmploymentType.DEPUTATION,
    "lien_position": lambda ctx: ctx.employment_type == EmploymentType.DEPUTATION,
    "previous_retirement_date": lambda ctx: ctx.employment_type == EmploymentType.REEMPLOYED,
    "reemployment_start_date": lambda ctx: ctx.employment_type == EmploymentType.REEMPLOYED,
    "reemployment_end_date": lambda ctx: ctx.employment_type == EmploymentType.REEMPLOYED,
    "pension_details": lambda ctx: ctx.employment_type == EmploymentType.REEMPLOYED,
    "outsourcing_agency": lambda ctx: ctx.employment_type == EmploymentType.OUTSOURCED,
    "agency_contract_number": lambda ctx: ctx.employment_type == EmploymentType.OUTSOURCED,
    "service_group": lambda ctx: ctx.employment_type in [EmploymentType.REGULAR, EmploymentType.DEPUTATION],
    "cadre": lambda ctx: ctx.employment_type in [EmploymentType.REGULAR, EmploymentType.DEPUTATION],
    "pay_level": lambda ctx: ctx.employment_type in PAY_SCALE_EMPLOYMENT_TYPES,
    "basic_pay": lambda ctx: ctx.employment_type in PAY_SCALE_EMPLOYMENT_TYPES,
    "pension_scheme": lambda ctx: ctx.employment_type == EmploymentType.REGULAR,
    "retirement_date": lambda ctx: ctx.employment_type in [EmploymentType.REGULAR, EmploymentType.DEPUTATION],
    "appointment_order_no": lambda ctx: ctx.employment_type in [EmploymentType.REGULAR, EmploymentType.DEPUTATION],
    "appointment_order_date": lambda ctx: ctx.employment_type in [EmploymentType.REGULAR, EmploymentType.DEPUTATION],
    "recruitment_mode": lambda ctx: ctx.employment_type in [EmploymentType.REGULAR, EmploymentType.DEPUTATION],
}

REQUIRED_RULES: Dict[str, Callable[[RuleContext], bool]] = {
    "full_name": lambda ctx: True,
    "gender": lambda ctx: True,
    "date_of_birth": lambda ctx: True,
    "mobile_number": lambda ctx: True,
    "employment_type": lambda ctx: True,
    "department_code": lambda ctx: True,
    "designation_code": lambda ctx: True,
    "spouse_name": lambda ctx: _is_married_status(ctx.form_data.get("marital_status")),
    "contract_start_date": lambda ctx: ctx.employment_type in CONTRACT_LIKE_EMPLOYMENT_TYPES,
    "contract_end_date": lambda ctx: ctx.employment_type in CONTRACT_LIKE_EMPLOYMENT_TYPES,
    "consolidated_pay": lambda ctx: ctx.employment_type in CONTRACT_LIKE_EMPLOYMENT_TYPES,
    "daily_rate": lambda ctx: ctx.employment_type in WAGE_LIKE_EMPLOYMENT_TYPES,
    "parent_department_code": lambda ctx: ctx.employment_type == EmploymentType.DEPUTATION,
    "deputation_start_date": lambda ctx: ctx.employment_type == EmploymentType.DEPUTATION,
    "outsourcing_agency": lambda ctx: ctx.employment_type == EmploymentType.OUTSOURCED,
    "service_group": lambda ctx: ctx.employment_type == EmploymentType.REGULAR,
    "pension_scheme": lambda ctx: ctx.employment_type == EmploymentType.REGULAR,
    "retirement_date": lambda ctx: ctx.employment_type == EmploymentType.REGULAR,
    "aadhaar_number": lambda ctx: ctx.employment_type == EmploymentType.REGULAR,
    "pan_number": lambda ctx: ctx.employment_type == EmploymentType.REGULAR,
}

READONLY_RULES: Dict[str, Callable[[RuleContext], bool]] = {
    "employee_id": lambda ctx: True,
    "employment_type": lambda ctx: ctx.workflow_stage not in [WorkflowStage.DRAFT, WorkflowStage.REJECTED],
    "date_of_birth": lambda ctx: ctx.workflow_stage not in [WorkflowStage.DRAFT, WorkflowStage.REJECTED],
    "full_name": lambda ctx: ctx.workflow_stage not in [WorkflowStage.DRAFT, WorkflowStage.REJECTED],
    "gender": lambda ctx: ctx.workflow_stage not in [WorkflowStage.DRAFT, WorkflowStage.REJECTED],
    "pay_level": lambda ctx: ctx.workflow_stage in [WorkflowStage.VERIFIED, WorkflowStage.APPROVED, WorkflowStage.ATTESTED, WorkflowStage.LOCKED],
    "basic_pay": lambda ctx: ctx.workflow_stage in [WorkflowStage.VERIFIED, WorkflowStage.APPROVED, WorkflowStage.ATTESTED, WorkflowStage.LOCKED],
    "appointment_order_no": lambda ctx: ctx.workflow_stage in [WorkflowStage.APPROVED, WorkflowStage.ATTESTED, WorkflowStage.LOCKED],
    "appointment_order_date": lambda ctx: ctx.workflow_stage in [WorkflowStage.APPROVED, WorkflowStage.ATTESTED, WorkflowStage.LOCKED],
    "department_code": lambda ctx: ctx.workflow_stage in FINALIZED_WORKFLOW_STAGES,
    "designation_code": lambda ctx: ctx.workflow_stage in FINALIZED_WORKFLOW_STAGES,
    "office_code": lambda ctx: ctx.workflow_stage in FINALIZED_WORKFLOW_STAGES,
    "retirement_date": lambda ctx: True,
}

COMPUTED_RULES: Dict[str, Callable[[RuleContext], Any]] = {
    "retirement_date": lambda ctx: _compute_retirement_date(ctx),
    "full_name": lambda ctx: _compute_full_name(ctx),
    "contract_end_date_suggestion": lambda ctx: _compute_contract_end_suggestion(ctx),
}


def _compute_retirement_date(ctx: RuleContext) -> Optional[str]:
    dob_str = ctx.form_data.get("date_of_birth")
    if not dob_str:
        return None

    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        retirement_date = dob + relativedelta(years=60)
        retirement_date = (
            retirement_date.replace(day=1)
            + relativedelta(months=1)
            - relativedelta(days=1)
        )
        return retirement_date.isoformat()
    except (ValueError, TypeError):
        return None


def _compute_full_name(ctx: RuleContext) -> Optional[str]:
    full_name = ctx.form_data.get("full_name")
    if isinstance(full_name, str):
        full_name = full_name.strip()
    return full_name or None


def _compute_contract_end_suggestion(ctx: RuleContext) -> Optional[str]:
    start_str = ctx.form_data.get("contract_start_date")
    if not start_str:
        return None

    try:
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = start + relativedelta(years=1) - relativedelta(days=1)
        return end.isoformat()
    except (ValueError, TypeError):
        return None


VALIDATION_RULES: Dict[str, Callable[[RuleContext], Optional[str]]] = {
    "contract_end_date": lambda ctx: (
        "Contract end date must be after start date"
        if (
            ctx.form_data.get("contract_start_date")
            and ctx.form_data.get("contract_end_date")
            and ctx.form_data["contract_end_date"] <= ctx.form_data["contract_start_date"]
        )
        else None
    ),
    "deputation_end_date": lambda ctx: (
        "Deputation end date must be after start date"
        if (
            ctx.form_data.get("deputation_start_date")
            and ctx.form_data.get("deputation_end_date")
            and ctx.form_data["deputation_end_date"] <= ctx.form_data["deputation_start_date"]
        )
        else None
    ),
    "basic_pay": lambda ctx: (
        "Basic pay must be positive"
        if ctx.form_data.get("basic_pay") is not None and ctx.form_data["basic_pay"] <= 0
        else None
    ),
    "date_of_birth": lambda ctx: _validate_age(ctx),
}

FIELD_ALIASES: Dict[str, tuple[str, ...]] = {
    "mobile_number": ("mobile_number", "mobile_primary"),
    "personal_email": ("personal_email", "email_personal"),
    "department_code": ("department_code", "current_department_id"),
    "designation_code": ("designation_code", "current_designation_id"),
    "service_group": ("service_group", "service"),
}


def _candidate_field_names(field_id: str) -> tuple[str, ...]:
    return FIELD_ALIASES.get(field_id, (field_id,))


def _resolve_payload_key_to_field_id(field_name: str) -> str:
    if field_name in FIELD_ALIASES:
        return field_name
    for canonical_field_id, aliases in FIELD_ALIASES.items():
        if field_name in aliases:
            return canonical_field_id
    return field_name


def _has_value_for_field(data: Dict[str, Any], field_id: str) -> bool:
    for candidate in _candidate_field_names(field_id):
        value = data.get(candidate)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False


def _validate_age(ctx: RuleContext) -> Optional[str]:
    dob_str = ctx.form_data.get("date_of_birth")
    if not dob_str:
        return None

    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = date.today()
        age = relativedelta(today, dob).years

        if age < 18:
            return "Employee must be at least 18 years old"
        if age > 65:
            return "Employee cannot be older than 65 years"

        return None
    except (ValueError, TypeError):
        return "Invalid date format"


class RuleEvaluator:
    def __init__(self, schema: Dict, context: RuleContext):
        self.schema = schema
        self.context = context

    def resolve(self) -> Dict:
        resolved_fields = []

        for field_def in self.schema.get("fields", []):
            field_id = field_def.get("field_id")

            if not self._is_visible(field_id):
                continue

            resolved = {
                **field_def,
                "visible": True,
                "required": self._is_required(field_id),
                "readonly": self._is_readonly(field_id),
            }

            computed_value = self._get_computed_value(field_id)
            if computed_value is not None:
                resolved["computed_value"] = computed_value

            validation_error = self._get_validation_error(field_id)
            if validation_error:
                resolved["validation_error"] = validation_error

            resolved_fields.append(resolved)

        return {
            "_metadata": self.schema.get("_metadata", {}),
            "context": {
                "employment_type": (
                    self.context.employment_type.value if self.context.employment_type else None
                ),
                "workflow_stage": self.context.workflow_stage.value,
                "is_edit_mode": self.context.is_edit_mode,
            },
            "fields": resolved_fields,
            "field_count": len(resolved_fields),
        }

    def _is_visible(self, field_id: str) -> bool:
        rule = VISIBILITY_RULES.get(field_id)
        if rule is None:
            return True
        return rule(self.context)

    def _is_required(self, field_id: str) -> bool:
        rule = REQUIRED_RULES.get(field_id)
        if rule is None:
            return False
        return rule(self.context)

    def _is_readonly(self, field_id: str) -> bool:
        rule = READONLY_RULES.get(field_id)
        if rule is None:
            return False
        return rule(self.context)

    def _get_computed_value(self, field_id: str) -> Any:
        rule = COMPUTED_RULES.get(field_id)
        if rule is None:
            return None
        return rule(self.context)

    def _get_validation_error(self, field_id: str) -> Optional[str]:
        rule = VALIDATION_RULES.get(field_id)
        if rule is None:
            return None
        return rule(self.context)

    def get_visible_fields(self) -> List[str]:
        return [
            f["field_id"]
            for f in self.schema.get("fields", [])
            if self._is_visible(f["field_id"])
        ]

    def get_required_fields(self) -> List[str]:
        return [
            f["field_id"]
            for f in self.schema.get("fields", [])
            if self._is_visible(f["field_id"]) and self._is_required(f["field_id"])
        ]

    def get_readonly_fields(self) -> List[str]:
        return [
            f["field_id"]
            for f in self.schema.get("fields", [])
            if self._is_visible(f["field_id"]) and self._is_readonly(f["field_id"])
        ]

    def validate_submission(self, data: Dict) -> List[Dict]:
        errors = []
        self.context.form_data = data
        schema_fields = {
            field_def["field_id"]: field_def for field_def in self.schema.get("fields", [])
        }
        visible_fields = set(self.get_visible_fields())

        for field_id in self.get_required_fields():
            if not _has_value_for_field(data, field_id):
                field_def = schema_fields.get(field_id)
                label = field_def.get("label", field_id) if field_def else field_id
                errors.append(
                    {
                        "field_id": field_id,
                        "error_type": "required",
                        "message": f"{label} is required",
                    }
                )

        for field_id, rule in VALIDATION_RULES.items():
            if self._is_visible(field_id):
                error = rule(self.context)
                if error:
                    errors.append(
                        {
                            "field_id": field_id,
                            "error_type": "validation",
                            "message": error,
                        }
                    )

        if self.context.employment_type is not None:
            hidden_actionable_fields = set()
            employment_type_label = self.context.employment_type.value
            for payload_key in data:
                field_id = _resolve_payload_key_to_field_id(payload_key)
                if field_id in visible_fields or field_id in hidden_actionable_fields:
                    continue
                field_def = schema_fields.get(field_id)
                if field_def is None:
                    continue
                label = field_def.get("label", field_id)
                errors.append(
                    {
                        "field_id": field_id,
                        "error_type": "forbidden",
                        "message": f"{label} is not allowed for {employment_type_label} employees",
                    }
                )
                hidden_actionable_fields.add(field_id)

        return errors


@lru_cache(maxsize=1)
def _load_schema_cached() -> Dict:
    schema_path = os.path.join(os.path.dirname(__file__), "form_schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_schema() -> Dict:
    return copy.deepcopy(_load_schema_cached())


def get_resolved_form(
    employment_type: Optional[str] = None,
    workflow_stage: str = "DRAFT",
    form_data: Dict = None,
    is_edit_mode: bool = False,
) -> Dict:
    schema = load_schema()

    context = RuleContext(
        form_data=form_data or {},
        employment_type=_parse_employment_type(employment_type),
        workflow_stage=_parse_workflow_stage(workflow_stage),
        is_edit_mode=is_edit_mode,
    )

    evaluator = RuleEvaluator(schema, context)
    return evaluator.resolve()


def validate_form_data(
    data: Dict, employment_type: Optional[str] = None, workflow_stage: str = "DRAFT"
) -> List[Dict]:
    schema = load_schema()

    context = RuleContext(
        form_data=data,
        employment_type=_parse_employment_type(employment_type),
        workflow_stage=_parse_workflow_stage(workflow_stage),
    )

    evaluator = RuleEvaluator(schema, context)
    return evaluator.validate_submission(data)
