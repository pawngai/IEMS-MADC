from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from contexts.service_book.contracts.servicebook.schema_definition import (
    SCHEMA_DEFINITIONS,
    ServiceBookEntryKind,
)
from contexts.service_book.domain.services.payload_normalizer import (
    normalize_part_i_payload,
    normalize_passthrough_payload,
)


PART_I_KEY = "SB_PART_I"
PART_I_SCHEMA_KEY = "SB_I_BIODATA"
PART_II_A_KEY = "SB_PART_II_A"
PART_II_A_SCHEMA_KEY = "SB_IIA_IMMUTABLE_CERTS"
PART_II_B_KEY = "SB_PART_II_B"
PART_III_KEY = "SB_PART_III"


@dataclass(frozen=True, slots=True)
class ManualEntryPolicy:
    part_key: str
    part_aliases: set[str]
    part_label: str
    entry_policy: str
    payload_normalizer: Callable[[dict[str, Any]], dict[str, Any]]
    enrich_profile_assets: bool = False
    stamp_attestation: bool = False


MANUAL_ENTRY_POLICY_BY_SCHEMA_KEY: dict[str, ManualEntryPolicy] = {
    PART_I_SCHEMA_KEY: ManualEntryPolicy(
        part_key=PART_I_KEY,
        part_aliases={PART_I_KEY, "I"},
        part_label="Part I",
        entry_policy="singleton",
        payload_normalizer=normalize_part_i_payload,
        enrich_profile_assets=True,
        stamp_attestation=True,
    ),
    PART_II_A_SCHEMA_KEY: ManualEntryPolicy(
        part_key=PART_II_A_KEY,
        part_aliases={PART_II_A_KEY, "II-A"},
        part_label="Part II-A",
        entry_policy="singleton",
        payload_normalizer=normalize_passthrough_payload,
    ),
    "SB_IIB_FAMILY_SHEET": ManualEntryPolicy(
        part_key=PART_II_B_KEY,
        part_aliases={PART_II_B_KEY, "II-B"},
        part_label="Part II-B",
        entry_policy="singleton",
        payload_normalizer=normalize_passthrough_payload,
    ),
    "SB_IIB_FAMILY_MEMBER_ROW": ManualEntryPolicy(
        part_key=PART_II_B_KEY,
        part_aliases={PART_II_B_KEY, "II-B"},
        part_label="Part II-B",
        entry_policy="append",
        payload_normalizer=normalize_passthrough_payload,
    ),
    "SB_IIB_PCF_NOMINATION_ROW": ManualEntryPolicy(
        part_key=PART_II_B_KEY,
        part_aliases={PART_II_B_KEY, "II-B"},
        part_label="Part II-B",
        entry_policy="append",
        payload_normalizer=normalize_passthrough_payload,
    ),
    "SB_IIB_DCRG_NOMINATION_ROW": ManualEntryPolicy(
        part_key=PART_II_B_KEY,
        part_aliases={PART_II_B_KEY, "II-B"},
        part_label="Part II-B",
        entry_policy="append",
        payload_normalizer=normalize_passthrough_payload,
    ),
    "SB_IIB_NPS_NOMINATION_ROW": ManualEntryPolicy(
        part_key=PART_II_B_KEY,
        part_aliases={PART_II_B_KEY, "II-B"},
        part_label="Part II-B",
        entry_policy="append",
        payload_normalizer=normalize_passthrough_payload,
    ),
    "SB_IIB_LEAVE_ENCASHMENT_NOMINATION_ROW": ManualEntryPolicy(
        part_key=PART_II_B_KEY,
        part_aliases={PART_II_B_KEY, "II-B"},
        part_label="Part II-B",
        entry_policy="append",
        payload_normalizer=normalize_passthrough_payload,
    ),
    "SB_IIB_FAMILY_PENSION_NOMINATION_ROW": ManualEntryPolicy(
        part_key=PART_II_B_KEY,
        part_aliases={PART_II_B_KEY, "II-B"},
        part_label="Part II-B",
        entry_policy="append",
        payload_normalizer=normalize_passthrough_payload,
    ),
    "SB_III_PREVIOUS_SERVICE_ROW": ManualEntryPolicy(
        part_key=PART_III_KEY,
        part_aliases={PART_III_KEY, "III"},
        part_label="Part III",
        entry_policy="append",
        payload_normalizer=normalize_passthrough_payload,
    ),
    "SB_III_FOREIGN_SERVICE_ROW": ManualEntryPolicy(
        part_key=PART_III_KEY,
        part_aliases={PART_III_KEY, "III"},
        part_label="Part III",
        entry_policy="append",
        payload_normalizer=normalize_passthrough_payload,
    ),
}


def manual_entry_scope_message() -> str:
    return "Manual Service Book entry is currently enabled only for Part I, Part II-A, Part II-B, and Part III."


def policy_for_manual_entry(*, schema_key: str, part_key: str) -> ManualEntryPolicy | None:
    normalized_schema = str(schema_key or "").strip().upper()
    normalized_part = str(part_key or "").strip().upper()
    policy = MANUAL_ENTRY_POLICY_BY_SCHEMA_KEY.get(normalized_schema)
    if not policy or normalized_part not in policy.part_aliases:
        return None
    return policy


def entry_kind_for_schema(schema_key: str) -> str:
    schema = SCHEMA_DEFINITIONS.get(schema_key)
    if not schema:
        return ServiceBookEntryKind.SNAPSHOT.value
    return schema.entry_kind
