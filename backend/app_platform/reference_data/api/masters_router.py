from __future__ import annotations

from fastapi import APIRouter, Depends

from app_platform.db.runtime import get_db_optional
from app_platform.reference_data.infrastructure import service

masters_router = APIRouter(prefix="/masters", tags=["Master Data"])


@masters_router.get("/employment-types")
async def get_employment_types(db=Depends(get_db_optional)):
    return await service.get_employment_types(db)


@masters_router.get("/employment-types/{code}/rules")
async def get_employment_type_rules(code: str, db=Depends(get_db_optional)):
    return await service.get_employment_type_rules(code, db)


@masters_router.get("/service-event-types")
async def get_service_event_types(db=Depends(get_db_optional)):
    return await service.get_service_event_types(db)


@masters_router.get("/leave-types")
async def get_leave_types(
    employment_type_code: str | None = None, db=Depends(get_db_optional)
):
    return await service.get_leave_types(db, employment_type_code=employment_type_code)


@masters_router.get("/pay-levels")
async def get_pay_levels(db=Depends(get_db_optional)):
    return await service.get_pay_levels(db)


@masters_router.get("/service-groups")
async def get_service_groups(db=Depends(get_db_optional)):
    return await service.get_service_groups(db)


@masters_router.get("/services")
async def get_services(db=Depends(get_db_optional)):
    return await service.get_services(db)


@masters_router.get("/caste-categories")
async def get_caste_categories(db=Depends(get_db_optional)):
    return await service.get_caste_categories(db)


@masters_router.get("/departments")
async def get_departments(db=Depends(get_db_optional)):
    return await service.get_departments(db)


@masters_router.get("/designations")
async def get_designations(db=Depends(get_db_optional)):
    return await service.get_designations(db)


@masters_router.get("/offices")
async def get_offices(department_code: str | None = None, db=Depends(get_db_optional)):
    return await service.get_offices(db, department_code=department_code)


@masters_router.get("/form-config/{form_id}")
async def get_form_config(form_id: str, employment_type_code: str | None = None):
    return await service.get_form_config(
        form_id, employment_type_code=employment_type_code
    )


@masters_router.get("/employee-form-schema")
async def get_employee_form_schema(employment_type: str | None = None):
    return await service.get_employee_form_schema(employment_type=employment_type)


@masters_router.get("/employee-form-fields/{employment_type}")
async def get_employee_form_fields(employment_type: str):
    return await service.get_employee_form_fields(employment_type)
