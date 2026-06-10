from __future__ import annotations

import pytest

from contexts.employee_profile.infrastructure.gateway import (
    EmployeeProfileReadMongoGateway,
    EmployeeProfileRepositoryMongoGateway,
)


class _FakeAsyncCursor:
    def __init__(self, rows) -> None:
        self._rows = list(rows)
        self._index = 0

    def sort(self, sort):
        rows = list(self._rows)
        sort_items = list(sort or [])
        for field, direction in reversed(sort_items):
            rows.sort(key=lambda row: row.get(field), reverse=direction < 0)
        self._rows = rows
        return self

    def skip(self, count):
        self._rows = self._rows[count:]
        return self

    def limit(self, count):
        self._rows = self._rows[:count]
        return self

    async def to_list(self, length=None):
        if length is None:
            return list(self._rows)
        return list(self._rows[:length])

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._rows):
            raise StopAsyncIteration
        value = self._rows[self._index]
        self._index += 1
        return value


class _FakeCollection:
    def __init__(self, document=None, rows=None) -> None:
        self.document = document
        self.rows = list(rows if rows is not None else ([document] if document is not None else []))
        self.inserted: list[dict] = []
        self.updated: list[tuple[dict, dict, bool]] = []
        self.deleted: list[dict] = []

    def _matches(self, row, query):
        if not query:
            return True
        for key, value in query.items():
            if isinstance(value, dict):
                if "$in" in value:
                    if row.get(key) not in value["$in"]:
                        return False
                    continue
            if row.get(key) != value:
                return False
        return True

    async def find_one(self, query, _projection):
        for row in self.rows:
            if self._matches(row, query):
                return dict(row)
        return None

    def find(self, query, _projection):
        return _FakeAsyncCursor([dict(row) for row in self.rows if self._matches(row, query)])

    async def count_documents(self, query):
        return sum(1 for row in self.rows if self._matches(row, query))

    async def insert_one(self, document):
        self.inserted.append(document)
        self.document = document
        self.rows.append(dict(document))

    async def update_one(self, query, update, upsert=False):
        self.updated.append((query, update, upsert))
        for index, row in enumerate(self.rows):
            if not self._matches(row, query):
                continue
            next_row = dict(row)
            next_row.update(update.get("$set", {}))
            for key, value in update.get("$setOnInsert", {}).items():
                next_row.setdefault(key, value)
            self.rows[index] = next_row
            self.document = next_row
            return type("_UpdateResult", (), {"modified_count": 1, "upserted_id": None})()
        if upsert:
            next_row = dict(query)
            next_row.update(update.get("$setOnInsert", {}))
            next_row.update(update.get("$set", {}))
            self.rows.append(next_row)
            self.document = next_row
            return type("_UpdateResult", (), {"modified_count": 0, "upserted_id": "upserted"})()
        return type("_UpdateResult", (), {"modified_count": 0, "upserted_id": None})()

    async def delete_one(self, query):
        self.deleted.append(query)
        self.rows = [row for row in self.rows if not self._matches(row, query)]
        self.document = self.rows[0] if self.rows else None


class _FakeDb:
    def __init__(self, *, projected=None, projected_rows=None, identities=None, extensions=None) -> None:
        self.employee_profile_read_models = _FakeCollection(projected, projected_rows)
        self.employee_identities = _FakeCollection(rows=identities or [])
        self.employee_profile_extensions = _FakeCollection(rows=extensions or [])


@pytest.mark.asyncio
async def test_repository_get_profile_normalizes_missing_workflow_status_from_projection() -> None:
    gateway = EmployeeProfileRepositoryMongoGateway(
        db=_FakeDb(
            projected={
                "employee_id": "EMP-1",
                "full_name": "Demo Employee",
            }
        )
    )

    profile = await gateway.get_profile(employee_id="EMP-1")

    assert profile is not None
    assert profile["workflow_status"] == "DRAFT"


@pytest.mark.asyncio
async def test_repository_insert_profile_rejects_identity_fields_after_cutover() -> None:
    gateway = EmployeeProfileRepositoryMongoGateway(db=_FakeDb())

    with pytest.raises(PermissionError):
        await gateway.insert_profile(
            profile={
                "employee_id": "EMP-2",
                "full_name": "Identity Leak",
                "father_name": "Allowed Extension",
            }
        )


@pytest.mark.asyncio
async def test_repository_insert_profile_accepts_extension_only_payload() -> None:
    db = _FakeDb()
    gateway = EmployeeProfileRepositoryMongoGateway(db=db)

    await gateway.insert_profile(
        profile={
            "employee_id": "EMP-3",
            "father_name": "Extension Only",
            "contact": {"mobile_primary": "9999999999"},
            "workflow_status": "DRAFT",
        }
    )

    assert db.employee_profile_extensions.inserted == [
        {
            "employee_id": "EMP-3",
            "father_name": "Extension Only",
            "contact": {"mobile_primary": "9999999999"},
            "workflow_status": "DRAFT",
        }
    ]


@pytest.mark.asyncio
async def test_read_gateway_backfills_missing_projection_for_list_and_count() -> None:
    db = _FakeDb(
        projected_rows=[
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Projected Employee",
                "workflow_status": "APPROVED",
            }
        ],
        identities=[
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Projected Employee",
                "employment_type": "REGULAR",
            },
            {
                "employee_id": "EMP-2",
                "employee_code": "MADC-2024-R0002",
                "full_name": "Identity Only Employee",
                "employment_type": "REGULAR",
                "workflow_status": "ACTIVE",
            },
        ],
    )
    gateway = EmployeeProfileReadMongoGateway(db=db)

    total = await gateway.count_profiles(query={})
    profiles = await gateway.list_profiles(query={}, skip=0, limit=10, sort=[("employee_code", 1)])

    assert total == 2
    assert [profile["employee_code"] for profile in profiles] == [
        "MADC-2024-R0001",
        "MADC-2024-R0002",
    ]
    assert any(row.get("employee_id") == "EMP-2" for row in db.employee_profile_read_models.rows)


@pytest.mark.asyncio
async def test_read_gateway_refreshes_stale_projection_before_workflow_filter() -> None:
    db = _FakeDb(
        projected_rows=[
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Projected Employee",
                "workflow_status": "DRAFT",
                "updated_at": "2026-04-21T00:00:00+00:00",
            }
        ],
        identities=[
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Projected Employee",
                "employment_type": "REGULAR",
                "workflow_status": "ACTIVE",
                "updated_at": "2026-04-27T00:00:00+00:00",
            },
        ],
        extensions=[
            {
                "employee_id": "EMP-1",
                "workflow_status": "SUBMITTED",
            },
        ],
    )
    gateway = EmployeeProfileReadMongoGateway(db=db)

    total = await gateway.count_profiles(query={"workflow_status": "SUBMITTED"})
    profiles = await gateway.list_profiles(
        query={"workflow_status": "SUBMITTED"},
        skip=0,
        limit=10,
        sort=[("employee_code", 1)],
    )

    assert total == 1
    assert [profile["workflow_status"] for profile in profiles] == ["SUBMITTED"]
    assert db.employee_profile_read_models.rows[0]["workflow_status"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_read_gateway_uses_active_identity_rows_for_draft_profile_queue() -> None:
    db = _FakeDb(
        projected_rows=[
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Projected Employee",
                "workflow_status": "LOCKED",
            }
        ],
        identities=[
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Projected Employee",
                "employment_type": "REGULAR",
                "workflow_status": "ACTIVE",
            }
        ],
    )
    gateway = EmployeeProfileReadMongoGateway(db=db)

    total = await gateway.count_profiles(query={"workflow_status": "DRAFT"})
    profiles = await gateway.list_profiles(
        query={"workflow_status": "DRAFT"},
        skip=0,
        limit=10,
        sort=[("employee_code", 1)],
    )

    assert total == 1
    assert [profile["workflow_status"] for profile in profiles] == ["DRAFT"]
    assert [profile["identity_workflow_status"] for profile in profiles] == ["ACTIVE"]


@pytest.mark.asyncio
async def test_read_gateway_excludes_unactivated_identity_rows_from_profile_queue() -> None:
    db = _FakeDb(
        identities=[
            {
                "employee_id": "EMP-DRAFT",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Identity Draft Employee",
                "employment_type": "REGULAR",
                "workflow_status": "DRAFT",
            },
            {
                "employee_id": "EMP-ACTIVE",
                "employee_code": "MADC-2024-R0002",
                "full_name": "Identity Active Employee",
                "employment_type": "REGULAR",
                "workflow_status": "ACTIVE",
            },
        ],
    )
    gateway = EmployeeProfileReadMongoGateway(db=db)

    total = await gateway.count_profiles(
        query={"workflow_status": "DRAFT", "identity_workflow_status": "ACTIVE"}
    )
    profiles = await gateway.list_profiles(
        query={"workflow_status": "DRAFT", "identity_workflow_status": "ACTIVE"},
        skip=0,
        limit=10,
        sort=[("employee_code", 1)],
    )

    assert total == 1
    assert [profile["employee_id"] for profile in profiles] == ["EMP-ACTIVE"]
    assert profiles[0]["workflow_status"] == "DRAFT"
    assert profiles[0]["identity_workflow_status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_read_gateway_lists_new_identity_in_default_directory_after_creation() -> None:
    db = _FakeDb(
        projected_rows=[
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Existing Employee",
                "workflow_status": "LOCKED",
            }
        ],
        identities=[
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Existing Employee",
                "employment_type": "REGULAR",
                "workflow_status": "ACTIVE",
            },
            {
                "employee_id": "EMP-2",
                "employee_code": "MADC-2024-R0002",
                "full_name": "Newly Created Employee",
                "employment_type": "REGULAR",
                "workflow_status": "DRAFT",
            },
        ],
    )
    gateway = EmployeeProfileReadMongoGateway(db=db)

    total = await gateway.count_profiles(query={})
    profiles = await gateway.list_profiles(
        query={},
        skip=0,
        limit=10,
        sort=[("employee_code", 1)],
    )

    assert total == 2
    by_employee_id = {profile["employee_id"]: profile for profile in profiles}
    assert by_employee_id["EMP-2"]["workflow_status"] == "DRAFT"
    assert by_employee_id["EMP-2"]["identity_workflow_status"] == "DRAFT"
    assert any(row.get("employee_id") == "EMP-2" for row in db.employee_profile_read_models.rows)


@pytest.mark.asyncio
async def test_read_gateway_does_not_fallback_to_identity_rows_for_submitted_profile_queue() -> None:
    db = _FakeDb(
        projected_rows=[],
        identities=[
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-2024-R0001",
                "full_name": "Identity Employee",
                "employment_type": "REGULAR",
                "workflow_status": "DRAFT",
            }
        ],
    )
    gateway = EmployeeProfileReadMongoGateway(db=db)

    total = await gateway.count_profiles(query={"workflow_status": "SUBMITTED"})
    profiles = await gateway.list_profiles(
        query={"workflow_status": "SUBMITTED"},
        skip=0,
        limit=10,
        sort=[("employee_code", 1)],
    )

    assert total == 0
    assert profiles == []


@pytest.mark.asyncio
async def test_read_gateway_does_not_fallback_active_identity_into_draft_profile_queue_after_profile_submission() -> None:
    db = _FakeDb(
        projected_rows=[],
        identities=[
            {
                "employee_id": "EMP-SUBMITTED-PROFILE",
                "employee_code": "MADC-0111",
                "full_name": "Submitted Profile",
                "employment_type": "CONTRACTUAL",
                "workflow_status": "ACTIVE",
            }
        ],
        extensions=[
            {
                "employee_id": "EMP-SUBMITTED-PROFILE",
                "workflow_status": "SUBMITTED",
                "employee_section_completed": True,
                "data_entry_section_completed": True,
            }
        ],
    )
    gateway = EmployeeProfileReadMongoGateway(db=db)

    total = await gateway.count_profiles(
        query={"workflow_status": "DRAFT", "identity_workflow_status": "ACTIVE"}
    )
    profiles = await gateway.list_profiles(
        query={"workflow_status": "DRAFT", "identity_workflow_status": "ACTIVE"},
        skip=0,
        limit=10,
        sort=[("employee_code", 1)],
    )

    assert total == 0
    assert profiles == []
    assert db.employee_profile_read_models.rows[0]["workflow_status"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_read_gateway_includes_draft_identities_in_default_directory() -> None:
    db = _FakeDb(
        identities=[
            {
                "employee_id": "EMP-DRAFT",
                "employee_code": "MADC-2026-R0001",
                "full_name": "Identity Queue Only",
                "employment_type": "REGULAR",
                "workflow_status": "DRAFT",
            }
        ]
    )
    gateway = EmployeeProfileReadMongoGateway(db=db)

    total = await gateway.count_profiles(query={})
    profiles = await gateway.list_profiles(query={}, skip=0, limit=10)

    assert total == 1
    assert [profile["employee_id"] for profile in profiles] == ["EMP-DRAFT"]
    assert profiles[0]["workflow_status"] == "DRAFT"
    assert profiles[0]["identity_workflow_status"] == "DRAFT"
    assert any(row.get("employee_id") == "EMP-DRAFT" for row in db.employee_profile_read_models.rows)


@pytest.mark.asyncio
async def test_repository_gateway_get_profile_allows_draft_identity_for_extension_write() -> None:
    db = _FakeDb(
        identities=[
            {
                "employee_id": "EMP-DRAFT-WRITE",
                "employee_code": "MADC-2026-R0005",
                "full_name": "Draft Write Employee",
                "employment_type": "REGULAR",
                "workflow_status": "DRAFT",
            }
        ]
    )
    gateway = EmployeeProfileRepositoryMongoGateway(db=db)

    profile = await gateway.get_profile(employee_id="EMP-DRAFT-WRITE")

    assert profile is not None
    assert profile["employee_id"] == "EMP-DRAFT-WRITE"
    assert profile["workflow_status"] == "DRAFT"
    assert profile["identity_workflow_status"] == "DRAFT"
    assert any(row.get("employee_id") == "EMP-DRAFT-WRITE" for row in db.employee_profile_read_models.rows)


@pytest.mark.asyncio
@pytest.mark.parametrize("identity_workflow_status", ["SUBMITTED", "VERIFIED"])
async def test_read_gateway_get_profile_backfills_submitted_identity_projection(
    identity_workflow_status: str,
) -> None:
    db = _FakeDb(
        identities=[
            {
                "employee_id": "EMP-SUBMITTED-READ",
                "employee_code": "MADC-2026-R0007",
                "full_name": "Submitted Read Employee",
                "employment_type": "REGULAR",
                "workflow_status": identity_workflow_status,
            }
        ]
    )
    gateway = EmployeeProfileReadMongoGateway(db=db)

    profile = await gateway.get_profile(employee_id="EMP-SUBMITTED-READ")

    assert profile is not None
    assert profile["employee_id"] == "EMP-SUBMITTED-READ"
    assert profile["workflow_status"] == "DRAFT"
    assert profile["identity_workflow_status"] == identity_workflow_status
    assert any(
        row.get("employee_id") == "EMP-SUBMITTED-READ"
        for row in db.employee_profile_read_models.rows
    )


@pytest.mark.asyncio
async def test_read_gateway_backfill_keeps_projection_after_identity_submission() -> None:
    db = _FakeDb(
        projected_rows=[
            {
                "employee_id": "EMP-SUBMITTED-KEEP",
                "employee_code": "MADC-2026-R0008",
                "full_name": "Submitted Keep Employee",
                "workflow_status": "DRAFT",
                "identity_workflow_status": "DRAFT",
                "updated_at": "2026-05-03T00:00:00+00:00",
            }
        ],
        identities=[
            {
                "employee_id": "EMP-SUBMITTED-KEEP",
                "employee_code": "MADC-2026-R0008",
                "full_name": "Submitted Keep Employee",
                "employment_type": "REGULAR",
                "workflow_status": "SUBMITTED",
                "updated_at": "2026-05-04T00:00:00+00:00",
            }
        ],
    )
    gateway = EmployeeProfileReadMongoGateway(db=db)

    profiles = await gateway.list_profiles(query={}, skip=0, limit=10)

    assert [profile["employee_id"] for profile in profiles] == ["EMP-SUBMITTED-KEEP"]
    assert profiles[0]["workflow_status"] == "DRAFT"
    assert profiles[0]["identity_workflow_status"] == "SUBMITTED"
    assert db.employee_profile_read_models.deleted == []


@pytest.mark.asyncio
async def test_repository_update_profile_refreshes_projection_for_draft_identity_with_extension() -> None:
    db = _FakeDb(
        identities=[
            {
                "employee_id": "EMP-DRAFT-EXTENSION",
                "employee_code": "MADC-2026-R0006",
                "full_name": "Draft Extension Employee",
                "employment_type": "REGULAR",
                "workflow_status": "ACTIVE",
            }
        ]
    )
    gateway = EmployeeProfileRepositoryMongoGateway(db=db)

    modified = await gateway.update_profile(
        employee_id="EMP-DRAFT-EXTENSION",
        mongo_update={"$set": {"father_name": "Parent Name"}},
    )

    assert modified == 1
    assert any(
        row.get("employee_id") == "EMP-DRAFT-EXTENSION"
        for row in db.employee_profile_read_models.rows
    )


@pytest.mark.asyncio
async def test_repository_gateway_get_profile_backfills_missing_projection() -> None:
    db = _FakeDb(
        identities=[
            {
                "employee_id": "EMP-4",
                "employee_code": "MADC-2024-C0003",
                "full_name": "Contract Employee",
                "employment_type": "CONTRACTUAL",
                "workflow_status": "ACTIVE",
            }
        ]
    )
    gateway = EmployeeProfileRepositoryMongoGateway(db=db)

    profile = await gateway.get_profile(employee_id="EMP-4")

    assert profile is not None
    assert profile["employee_code"] == "MADC-2024-C0003"
    assert profile["workflow_status"] == "DRAFT"
    assert any(row.get("employee_id") == "EMP-4" for row in db.employee_profile_read_models.rows)
