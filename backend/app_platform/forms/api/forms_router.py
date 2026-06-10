# Form Configuration API
# ======================

from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from app_platform.auth.current_user import get_current_user

from app_platform.reference_data.contracts.employment_rules import (
    check_employment_type_allows_service_book,
)
from app_platform.forms.api.helpers import (
    EMPLOYMENT_TYPE_LABELS,
    TYPE_SPECIFIC_FIELDS,
    parse_employment_type,
    parse_workflow_stage,
    require_forms_access,
)

from app_platform.forms.infrastructure.service import (
    RuleContext,
    RuleEvaluator,
    WorkflowStage,
    get_resolved_form,
    load_schema,
    validate_form_data,
)

forms_router = APIRouter(prefix="/forms", tags=["Dynamic Forms"])


def _build_employment_type_field_payload(resolved_form: Dict) -> Dict:
    fields = resolved_form.get("fields", [])
    payload_fields = [
        {
            "field_id": field.get("field_id"),
            "label": field.get("label"),
            "type": field.get("type"),
            "part": field.get("part"),
            "required": bool(field.get("required")),
            "readonly": bool(field.get("readonly")),
        }
        for field in fields
    ]
    return {
        "field_count": len(payload_fields),
        "visible_field_ids": [field["field_id"] for field in payload_fields],
        "required_field_ids": [field["field_id"] for field in payload_fields if field["required"]],
        "readonly_field_ids": [field["field_id"] for field in payload_fields if field["readonly"]],
        "fields": payload_fields,
    }


@forms_router.get("/employee-profile")
async def get_employee_profile_form(
    employment_type: Optional[str] = Query(None, description="Employment type (REGULAR, CONTRACTUAL, etc.)"),
    workflow_stage: str = Query("DRAFT", description="Current workflow stage"),
    is_edit_mode: bool = Query(False, description="Is this an edit of existing record?"),
    current_user: dict = Depends(get_current_user),
):
    require_forms_access(current_user)
    try:
        resolved = get_resolved_form(
            employment_type=employment_type,
            workflow_stage=workflow_stage,
            is_edit_mode=is_edit_mode,
        )
        return resolved
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@forms_router.post("/employee-profile/resolve")
async def resolve_form_with_data(
    request_data: Dict,
    current_user: dict = Depends(get_current_user),
):
    require_forms_access(current_user)
    try:
        schema = load_schema()
        context = RuleContext.from_request(request_data)
        evaluator = RuleEvaluator(schema, context)
        return evaluator.resolve()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@forms_router.post("/employee-profile/validate")
async def validate_employee_profile_form(
    request_data: Dict,
    current_user: dict = Depends(get_current_user),
):
    require_forms_access(current_user)
    form_data = request_data.get("form_data", request_data)
    employment_type = request_data.get("employment_type", form_data.get("employment_type"))
    workflow_stage = request_data.get("workflow_stage", "DRAFT")

    try:
        errors = validate_form_data(
            data=form_data,
            employment_type=employment_type,
            workflow_stage=workflow_stage,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "error_count": len(errors),
    }


@forms_router.get("/employee-profile/field/{field_id}")
async def get_field_config(
    field_id: str,
    employment_type: Optional[str] = Query(None),
    workflow_stage: str = Query("DRAFT"),
    current_user: dict = Depends(get_current_user),
):
    require_forms_access(current_user)
    schema = load_schema()

    field_def = next(
        (f for f in schema.get("fields", []) if f["field_id"] == field_id),
        None,
    )

    if not field_def:
        raise HTTPException(status_code=404, detail=f"Field '{field_id}' not found")

    emp_type = parse_employment_type(employment_type)
    stage = parse_workflow_stage(workflow_stage)

    context = RuleContext(
        employment_type=emp_type,
        workflow_stage=stage,
    )

    evaluator = RuleEvaluator(schema, context)

    return {
        **field_def,
        "visible": evaluator._is_visible(field_id),
        "required": evaluator._is_required(field_id),
        "readonly": evaluator._is_readonly(field_id),
    }


@forms_router.get("/employee-profile/parts")
async def get_form_parts(
    employment_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    require_forms_access(current_user)
    schema = load_schema()
    try:
        resolved = get_resolved_form(employment_type=employment_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    parts = schema.get("_metadata", {}).get("parts", [])
    fields = resolved.get("fields", [])

    result = []
    for part in parts:
        part_fields = [f for f in fields if f.get("part") == part["id"]]
        result.append(
            {
                **part,
                "field_count": len(part_fields),
                "required_count": len([f for f in part_fields if f.get("required")]),
            }
        )

    return {
        "parts": result,
        "total_fields": len(fields),
    }


@forms_router.get("/employee-profile/employment-types")
async def get_employment_types(current_user: dict = Depends(get_current_user)):
    require_forms_access(current_user)

    types = []
    payloads_by_type = {}
    for emp_type, label in EMPLOYMENT_TYPE_LABELS.items():
        resolved = get_resolved_form(employment_type=emp_type)
        fields_payload = _build_employment_type_field_payload(resolved)
        visible_fields = [f["field_id"] for f in resolved.get("fields", [])]
        required_fields = [
            f["field_id"] for f in resolved.get("fields", []) if f.get("required")
        ]

        types.append(
            {
                "code": emp_type,
                "label": label,
                "field_count": len(visible_fields),
                "required_count": len(required_fields),
                "has_service_book": check_employment_type_allows_service_book(emp_type),
                "specific_fields": TYPE_SPECIFIC_FIELDS.get(emp_type, []),
                "fields_payload": fields_payload,
            }
        )
        payloads_by_type[emp_type] = fields_payload

    return {
        "employment_types": types,
        "employment_type_payloads": payloads_by_type,
    }


@forms_router.get("/employee-profile/readonly-matrix")
async def get_readonly_matrix(current_user: dict = Depends(get_current_user)):
    require_forms_access(current_user)
    schema = load_schema()
    stages = list(WorkflowStage)

    matrix = []
    for field in schema.get("fields", []):
        field_id = field.get("field_id")
        row = {"field_id": field_id, "label": field.get("label")}

        for stage in stages:
            context = RuleContext(workflow_stage=stage)
            evaluator = RuleEvaluator(schema, context)
            row[stage.value] = evaluator._is_readonly(field_id)

        matrix.append(row)

    return {
        "stages": [s.value for s in stages],
        "matrix": matrix,
    }
