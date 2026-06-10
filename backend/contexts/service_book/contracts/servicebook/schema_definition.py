from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from contexts.service_book.contracts.servicebook.part_constants import SB_LEDGER_PART_KEY_BY_ROMAN


class SchemaLifecycleStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"


class ServiceBookPartKey(str, Enum):
    SB_PART_I = "SB_PART_I"
    SB_PART_II_A = "SB_PART_II_A"
    SB_PART_II_B = "SB_PART_II_B"
    SB_PART_III = "SB_PART_III"
    SB_PART_IV = "SB_PART_IV"
    SB_PART_V = "SB_PART_V"
    SB_PART_VI = "SB_PART_VI"
    SB_PART_VII = "SB_PART_VII"
    SB_PART_VIII = "SB_PART_VIII"


class ServiceBookEntryKind(str, Enum):
    SNAPSHOT = "SNAPSHOT"
    ROW = "ROW"
    SHEET = "SHEET"
    COMMENT = "COMMENT"


@dataclass(slots=True)
class SchemaDefinition:
    schema_key: str
    title: str
    part_key: str
    entry_kind: str
    payload_model_name: str
    current_version: int = 1
    status: str = SchemaLifecycleStatus.PUBLISHED.value
    owner_department: str | None = None
    aliases: dict[str, str] = field(default_factory=dict)
    row_collection_key: str | None = None


PART_KEY_BY_ROMAN: dict[str, str] = dict(SB_LEDGER_PART_KEY_BY_ROMAN)


SCHEMA_DEFINITIONS: dict[str, SchemaDefinition] = {
    "SB_I_BIODATA": SchemaDefinition(
        schema_key="SB_I_BIODATA",
        title="Part I Bio-Data Snapshot",
        part_key=ServiceBookPartKey.SB_PART_I.value,
        entry_kind=ServiceBookEntryKind.SNAPSHOT.value,
        payload_model_name="PartI_BioData",
    ),
    "SB_IIA_IMMUTABLE_CERTS": SchemaDefinition(
        schema_key="SB_IIA_IMMUTABLE_CERTS",
        title="Part II-A Immutable Certificates Snapshot",
        part_key=ServiceBookPartKey.SB_PART_II_A.value,
        entry_kind=ServiceBookEntryKind.SNAPSHOT.value,
        payload_model_name="PartIIA_ImmutableCertificates",
    ),
    "SB_IIB_FAMILY_SHEET": SchemaDefinition(
        schema_key="SB_IIB_FAMILY_SHEET",
        title="Part II-B Family Sheet",
        part_key=ServiceBookPartKey.SB_PART_II_B.value,
        entry_kind=ServiceBookEntryKind.SHEET.value,
        payload_model_name="PartIIB_MutableCertificates",
    ),
    "SB_IIB_PCF_NOMINATION_ROW": SchemaDefinition(
        schema_key="SB_IIB_PCF_NOMINATION_ROW",
        title="Part II-B PCF Nomination Row",
        part_key=ServiceBookPartKey.SB_PART_II_B.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="PartIIB_MutableCertificates",
        row_collection_key="pcf_nomination",
    ),
    "SB_IIB_DCRG_NOMINATION_ROW": SchemaDefinition(
        schema_key="SB_IIB_DCRG_NOMINATION_ROW",
        title="Part II-B DCRG Nomination Row",
        part_key=ServiceBookPartKey.SB_PART_II_B.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="PartIIB_MutableCertificates",
        row_collection_key="dcr_gratuity_nomination",
    ),
    "SB_IIB_NPS_NOMINATION_ROW": SchemaDefinition(
        schema_key="SB_IIB_NPS_NOMINATION_ROW",
        title="Part II-B NPS Nomination Row",
        part_key=ServiceBookPartKey.SB_PART_II_B.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="PartIIB_MutableCertificates",
        row_collection_key="nps_nomination",
    ),
    "SB_IIB_LEAVE_ENCASHMENT_NOMINATION_ROW": SchemaDefinition(
        schema_key="SB_IIB_LEAVE_ENCASHMENT_NOMINATION_ROW",
        title="Part II-B Leave Encashment Nomination Row",
        part_key=ServiceBookPartKey.SB_PART_II_B.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="PartIIB_MutableCertificates",
        row_collection_key="leave_encashment_nomination",
    ),
    "SB_IIB_FAMILY_PENSION_NOMINATION_ROW": SchemaDefinition(
        schema_key="SB_IIB_FAMILY_PENSION_NOMINATION_ROW",
        title="Part II-B Family Pension Nomination Row",
        part_key=ServiceBookPartKey.SB_PART_II_B.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="PartIIB_MutableCertificates",
        row_collection_key="family_pension_nomination",
    ),
    "SB_IIB_BANK_DETAILS": SchemaDefinition(
        schema_key="SB_IIB_BANK_DETAILS",
        title="Part II-B Bank Details Snapshot",
        part_key=ServiceBookPartKey.SB_PART_II_B.value,
        entry_kind=ServiceBookEntryKind.SNAPSHOT.value,
        payload_model_name="PartIIB_MutableCertificates",
    ),
    "SB_IIB_NPS_PRAN": SchemaDefinition(
        schema_key="SB_IIB_NPS_PRAN",
        title="Part II-B NPS PRAN Snapshot",
        part_key=ServiceBookPartKey.SB_PART_II_B.value,
        entry_kind=ServiceBookEntryKind.SNAPSHOT.value,
        payload_model_name="PartIIB_MutableCertificates",
    ),
    "SB_III_PREVIOUS_SERVICE_ROW": SchemaDefinition(
        schema_key="SB_III_PREVIOUS_SERVICE_ROW",
        title="Part III Previous Service Row",
        part_key=ServiceBookPartKey.SB_PART_III.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="PreviousService",
    ),
    "SB_III_FOREIGN_SERVICE_ROW": SchemaDefinition(
        schema_key="SB_III_FOREIGN_SERVICE_ROW",
        title="Part III Foreign Service Row",
        part_key=ServiceBookPartKey.SB_PART_III.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="ForeignService",
    ),
    "SB_III_TOTAL_QS_SUMMARY": SchemaDefinition(
        schema_key="SB_III_TOTAL_QS_SUMMARY",
        title="Part III Total Qualifying Service Summary",
        part_key=ServiceBookPartKey.SB_PART_III.value,
        entry_kind=ServiceBookEntryKind.SNAPSHOT.value,
        payload_model_name="PartIII_ServiceHistoryOutside",
        aliases={
            "part_iii_verified": "verified",
            "part_iii_verified_by": "verified_by",
            "part_iii_verification_date": "verification_date",
        },
    ),
    "SB_IV_SERVICE_HISTORY_ROW": SchemaDefinition(
        schema_key="SB_IV_SERVICE_HISTORY_ROW",
        title="Part IV Service History Row",
        part_key=ServiceBookPartKey.SB_PART_IV.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="ServiceHistoryEntry",
    ),
    "SB_V_SERVICE_VERIFICATION_ROW": SchemaDefinition(
        schema_key="SB_V_SERVICE_VERIFICATION_ROW",
        title="Part V Service Verification Row",
        part_key=ServiceBookPartKey.SB_PART_V.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="ServiceVerificationEntry",
    ),
    "SB_VI_LEAVE_TRANSACTION_ROW": SchemaDefinition(
        schema_key="SB_VI_LEAVE_TRANSACTION_ROW",
        title="Part VI Leave Transaction Row",
        part_key=ServiceBookPartKey.SB_PART_VI.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="LeaveTransaction",
    ),
    "SB_VI_LEAVE_OPENING_BALANCE": SchemaDefinition(
        schema_key="SB_VI_LEAVE_OPENING_BALANCE",
        title="Part VI Leave Opening Balance Snapshot",
        part_key=ServiceBookPartKey.SB_PART_VI.value,
        entry_kind=ServiceBookEntryKind.SNAPSHOT.value,
        payload_model_name="PartVI_LeaveAccount",
    ),
    "SB_VII_LTC_ROW": SchemaDefinition(
        schema_key="SB_VII_LTC_ROW",
        title="Part VII LTC Row",
        part_key=ServiceBookPartKey.SB_PART_VII.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="LTCRecord",
    ),
    "SB_VII_HBA_ROW": SchemaDefinition(
        schema_key="SB_VII_HBA_ROW",
        title="Part VII HBA Row",
        part_key=ServiceBookPartKey.SB_PART_VII.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="HBARecord",
    ),
    "SB_VII_VEHICLE_ADVANCE_ROW": SchemaDefinition(
        schema_key="SB_VII_VEHICLE_ADVANCE_ROW",
        title="Part VII Vehicle Advance Row",
        part_key=ServiceBookPartKey.SB_PART_VII.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="PartVII_OtherRecords",
        row_collection_key="vehicle_advance_records",
    ),
    "SB_VII_FESTIVAL_ADVANCE_ROW": SchemaDefinition(
        schema_key="SB_VII_FESTIVAL_ADVANCE_ROW",
        title="Part VII Festival Advance Row",
        part_key=ServiceBookPartKey.SB_PART_VII.value,
        entry_kind=ServiceBookEntryKind.ROW.value,
        payload_model_name="PartVII_OtherRecords",
        row_collection_key="festival_advance_records",
    ),
    "SB_VIII_AUDIT_COMMENT": SchemaDefinition(
        schema_key="SB_VIII_AUDIT_COMMENT",
        title="Part VIII Audit Comment",
        part_key=ServiceBookPartKey.SB_PART_VIII.value,
        entry_kind=ServiceBookEntryKind.COMMENT.value,
        payload_model_name="AuditComment",
    ),
}


SCHEMA_KEYS_BY_PART: dict[str, list[str]] = {}
for _schema_key, _definition in SCHEMA_DEFINITIONS.items():
    SCHEMA_KEYS_BY_PART.setdefault(_definition.part_key, []).append(_schema_key)