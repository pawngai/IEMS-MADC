from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from contexts.employee_master.identity.schemas.commands import EmployeeIdentityCreate
from contexts.employee_master.profile.contracts.profile_write import (
    EmployeeProfileExtensionUpsert,
)


IDENTITY_CREATE_FIELDS = set(EmployeeIdentityCreate.model_fields.keys())
PROFILE_EXTENSION_FIELDS = set(EmployeeProfileExtensionUpsert.model_fields.keys())


@dataclass
class SplitEmployeeCreateResult:
    employee_id: str | None
    identity_response: Any
    profile_response: Any | None
    identity_payload: dict[str, Any]
    profile_payload: dict[str, Any]
    extra_fields: dict[str, Any]


def split_employee_payload(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    identity_payload: dict[str, Any] = {}
    profile_payload: dict[str, Any] = {}
    extra_fields: dict[str, Any] = {}

    for key, value in payload.items():
        if key in IDENTITY_CREATE_FIELDS:
            identity_payload[key] = value
        elif key in PROFILE_EXTENSION_FIELDS:
            profile_payload[key] = value
        else:
            extra_fields[key] = value

    return identity_payload, profile_payload, extra_fields


def create_employee_two_step(
    client: Any,
    *,
    base_url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    assert_known_fields: bool = True,
) -> SplitEmployeeCreateResult:
    identity_payload, profile_payload, extra_fields = split_employee_payload(payload)
    if assert_known_fields and extra_fields:
        unknown = ", ".join(sorted(extra_fields.keys()))
        raise AssertionError(f"Unexpected employee payload fields for split API: {unknown}")

    identity_response = client.post(
        f"{base_url}/api/employee-identities/",
        json=identity_payload,
        headers=headers,
    )

    employee_id: str | None = None
    profile_response = None
    if identity_response.status_code in (200, 201):
        employee_id = identity_response.json().get("employee_id")
        if employee_id and profile_payload:
            profile_response = client.put(
                f"{base_url}/api/employee-profiles/{employee_id}",
                json=profile_payload,
                headers=headers,
            )

    return SplitEmployeeCreateResult(
        employee_id=employee_id,
        identity_response=identity_response,
        profile_response=profile_response,
        identity_payload=identity_payload,
        profile_payload=profile_payload,
        extra_fields=extra_fields,
    )


def delete_employee_profile(
    client: Any,
    *,
    base_url: str,
    headers: dict[str, str],
    employee_id: str,
):
    return client.delete(
        f"{base_url}/api/employee-profiles/{employee_id}",
        headers=headers,
    )


def submit_employee_profile(
    client: Any,
    *,
    base_url: str,
    headers: dict[str, str],
    employee_id: str,
    remarks: str,
):
    return client.post(
        f"{base_url}/api/employee-profiles/{employee_id}/submit",
        json={"remarks": remarks},
        headers=headers,
    )
