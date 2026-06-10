"""Focused live smoke test for HOD direct casual-leave approval.

This follows the repository's existing live E2E pattern:
  1. Log in as a seeded HOD user.
  2. Seed a temporary regular employee profile in that HOD's department.
  3. Seed a submitted CL application for that employee with no leave ledger row.
  4. Sanction the CL application directly as the HOD.
  5. Verify the leave is sanctioned and the CL ledger debit uses computed availability.
  6. Clean up all temporary records.
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import bcrypt
import requests
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = os.getenv("IEMS_E2E_BASE", "http://localhost:8000/api")
MONGO_URI = os.getenv("IEMS_E2E_MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("IEMS_E2E_DB_NAME", "iems_db")
TIMEOUT = 20
DEFAULT_HOD_EMAIL = "e2e.browser.1992@madc.gov.in"
DEFAULT_HOD_PASSWORD = "employee123"
ALLOW_REMOTE = (os.getenv("IEMS_E2E_ALLOW_REMOTE") or "").strip() == "1"


def is_local_http_base(base_url: str) -> bool:
    hostname = (urlparse(base_url).hostname or "").strip().lower()
    return hostname in {"localhost", "127.0.0.1"}


def is_local_mongo_uri(uri: str) -> bool:
    try:
        nodes = parse_uri(uri).get("nodelist") or []
    except Exception:
        return False
    return bool(nodes) and all(
        str(host).strip().lower() in {"localhost", "127.0.0.1"}
        for host, _port in nodes
    )


def ensure_local_only_targets() -> None:
    if ALLOW_REMOTE:
        return
    violations: list[str] = []
    if not is_local_http_base(BASE):
        violations.append(f"IEMS_E2E_BASE={BASE}")
    if not is_local_mongo_uri(MONGO_URI):
        violations.append(f"IEMS_E2E_MONGO_URL={MONGO_URI}")
    if violations:
        detail = "; ".join(violations)
        raise RuntimeError(
            "This smoke script only runs against localhost targets by default: "
            f"{detail}. Set IEMS_E2E_ALLOW_REMOTE=1 only for an intentional remote run."
        )


def required_env_or_default(name: str, default: str) -> str:
    value = (os.getenv(name) or "").strip()
    return value or default


HOD_CREDS = {
    "email": required_env_or_default("IEMS_E2E_HOD_EMAIL", DEFAULT_HOD_EMAIL),
    "password": required_env_or_default("IEMS_E2E_HOD_PASSWORD", DEFAULT_HOD_PASSWORD),
}

PASS = 0
FAIL = 0
RESULTS: list[dict[str, Any]] = []

ensure_local_only_targets()
mongo = MongoClient(MONGO_URI)
mdb = mongo[DB_NAME]

session = requests.Session()
retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retry))


def ensure_hod_smoke_user() -> None:
    email = HOD_CREDS["email"].strip().lower()
    password = HOD_CREDS["password"]
    department = (os.getenv("IEMS_E2E_HOD_DEPARTMENT") or "FIN").strip().upper()
    now = datetime.now(timezone.utc).isoformat()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    mdb.users.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "name": "E2E HOD Smoke User",
                "authorities": ["HOD"],
                "employee_id": "E2E-HOD-001",
                "department_code": department,
                "office_code": "HQ",
                "is_active": True,
                "updated_at": now,
                "password_hash": password_hash,
            },
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "created_at": now,
                "created_by": "test_e2e_leave_hod_cl_approval.py",
            },
        },
        upsert=True,
    )


def log(step: str, desc: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    icon = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    line = f"  [{icon}] Step {step}: {desc}"
    if detail:
        line += f"  ->  {detail}"
    print(line)
    RESULTS.append({"step": step, "desc": desc, "ok": ok, "detail": detail})


def print_summary() -> None:
    print("\n" + "=" * 72)
    print(f"  RESULTS:  {PASS} passed,  {FAIL} failed,  {PASS + FAIL} total")
    print("=" * 72)
    if FAIL > 0:
        print("\n  Failed steps:")
        for result in RESULTS:
            if not result["ok"]:
                print(f"    FAIL {result['step']}: {result['desc']}  ->  {result['detail']}")


def response_json(response: requests.Response | None) -> dict[str, Any]:
    if response is None:
        return {}
    try:
        payload = response.json()
        return payload if isinstance(payload, dict) else {"value": payload}
    except ValueError:
        return {}


def auth(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def login(email: str, password: str) -> str | None:
    try:
        response = session.post(
            f"{BASE}/auth/login",
            json={"email": email, "password": password},
            timeout=TIMEOUT,
        )
    except Exception as exc:
        print(f"    WARNING: login failed for {email}: {exc}")
        return None
    if response.status_code == 200:
        return response_json(response).get("access_token")
    print(f"    WARNING: login failed for {email} with status {response.status_code}")
    return None


def safe_post(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_payload: dict[str, Any] | None = None,
) -> requests.Response | None:
    try:
        return session.post(
            url,
            headers=headers,
            json=json_payload,
            timeout=TIMEOUT,
        )
    except Exception as exc:
        print(f"    WARNING: POST {url} failed: {exc}")
        return None


def cleanup_temp_records(employee_id: str, leave_id: str) -> None:
    mdb.leave_applications.delete_many({"id": leave_id})
    mdb.leave_ledger_entries.delete_many({"employee_id": employee_id})
    mdb.employee_profile_read_models.delete_many({"employee_id": employee_id})
    mdb.service_book_part_revisions.delete_many({"employee_id": employee_id})


print("\n" + "=" * 72)
print("  IEMS HOD Direct CL Approval Smoke Test")
print("=" * 72)

ensure_hod_smoke_user()
token = login(HOD_CREDS["email"], HOD_CREDS["password"])
log("1.1", "HOD login", token is not None, HOD_CREDS["email"])

hod_user = mdb.users.find_one({"email": HOD_CREDS["email"].lower()}, {"_id": 0})
hod_exists = hod_user is not None
hod_user_id = str((hod_user or {}).get("id") or "")
hod_department = (
    str((hod_user or {}).get("department_code") or os.getenv("IEMS_E2E_HOD_DEPARTMENT") or "FIN")
    .strip()
    .upper()
)
log("1.2", "Resolve seeded HOD account", hod_exists, hod_user_id or "user not found")

employee_id = f"smoke-hod-cl-{uuid.uuid4()}"
leave_id = str(uuid.uuid4())
timestamp = int(time.time())
now = datetime.now(timezone.utc).isoformat()
leave_start = date.today() + timedelta(days=10)
leave_end = leave_start + timedelta(days=1)

profile_doc = {
    "employee_id": employee_id,
    "employee_code": f"SMOKE-CL-{timestamp}",
    "full_name": "Smoke HOD CL Approval Employee",
    "current_department_id": hod_department,
    "employment_type": "REGULAR",
    "date_of_initial_engagement": "2024-01-15",
}
leave_doc = {
    "id": leave_id,
    "employee_id": employee_id,
    "leave_type_code": "CL",
    "from_date": leave_start.isoformat(),
    "to_date": leave_end.isoformat(),
    "days_applied": 2.0,
    "reason": "Smoke test for HOD direct casual leave approval",
    "leave_station": "Aizawl",
    "contact_during_leave": "9876543210",
    "status": "SUBMITTED",
    "applied_by": employee_id,
    "applied_at": now,
    "attachments": [],
}

try:
    if not token or not hod_exists:
        print_summary()
        sys.exit(1)

    cleanup_temp_records(employee_id, leave_id)
    mdb.employee_profile_read_models.insert_one(profile_doc)
    mdb.leave_applications.insert_one(leave_doc)

    seeded_leave = mdb.leave_applications.find_one({"id": leave_id}, {"_id": 0, "status": 1})
    log(
        "2.1",
        "Seed temporary employee profile and submitted CL application",
        seeded_leave is not None,
        f"employee_id={employee_id}, leave_id={leave_id}",
    )

    sanction_response = safe_post(
        f"{BASE}/leave/{leave_id}/sanction",
        headers=auth(token),
        json_payload={
            "remarks": "Approved by HOD via smoke test",
            "order_number": f"SMOKE-CL-{timestamp}",
            "order_date": date.today().isoformat(),
        },
    )
    sanction_payload = response_json(sanction_response)
    sanction_ok = sanction_response is not None and sanction_response.status_code == 200
    log(
        "3.1",
        "Sanction submitted CL directly as HOD",
        sanction_ok,
        sanction_payload.get("status") or f"status={getattr(sanction_response, 'status_code', 'request-failed')}",
    )

    if not sanction_ok:
        print_summary()
        sys.exit(1)

    recommendation_filled = (
        sanction_payload.get("status") == "SANCTIONED"
        and sanction_payload.get("recommended_by") == hod_user_id
        and sanction_payload.get("sanctioned_by") == hod_user_id
        and bool(sanction_payload.get("recommended_at"))
        and bool(sanction_payload.get("sanctioned_at"))
    )
    log(
        "3.2",
        "Sanction response backfills recommendation fields",
        recommendation_filled,
        f"recommended_by={sanction_payload.get('recommended_by')}, sanctioned_by={sanction_payload.get('sanctioned_by')}",
    )

    ledger_entry = mdb.leave_ledger_entries.find_one({"employee_id": employee_id}, {"_id": 0})
    transactions = (ledger_entry or {}).get("transactions") or []
    latest_txn = transactions[-1] if transactions else {}
    ledger_ok = (
        ledger_entry is not None
        and abs(float(ledger_entry.get("casual_leave_balance", 0.0)) - 6.0) < 0.001
        and abs(float(latest_txn.get("opening_balance", 0.0)) - 8.0) < 0.001
        and abs(float(latest_txn.get("closing_balance", 0.0)) - 6.0) < 0.001
    )
    log(
        "4.1",
        "CL ledger debit uses computed annual availability",
        ledger_ok,
        f"opening={latest_txn.get('opening_balance')}, closing={latest_txn.get('closing_balance')}, cached={ledger_entry.get('casual_leave_balance') if ledger_entry else None}",
    )

    revision = mdb.service_book_part_revisions.find_one(
        {"employee_id": employee_id, "part": "SB_PART_VI"},
        {"_id": 0, "part": 1, "payload.transaction.leave_type": 1},
    )
    revision_ok = revision is not None and ((revision.get("payload") or {}).get("transaction") or {}).get("leave_type") == "CL"
    log(
        "4.2",
        "Service book revision recorded for sanctioned CL",
        revision_ok,
        f"part={revision.get('part') if revision else None}",
    )

    sanctioned_leave = mdb.leave_applications.find_one({"id": leave_id}, {"_id": 0, "status": 1})
    persisted_ok = (sanctioned_leave or {}).get("status") == "SANCTIONED"
    log(
        "4.3",
        "Leave application persisted as sanctioned",
        persisted_ok,
        (sanctioned_leave or {}).get("status", "missing"),
    )
finally:
    cleanup_temp_records(employee_id, leave_id)
    cleanup_ok = (
        mdb.leave_applications.count_documents({"id": leave_id}) == 0
        and mdb.leave_ledger_entries.count_documents({"employee_id": employee_id}) == 0
        and mdb.employee_profile_read_models.count_documents({"employee_id": employee_id}) == 0
        and mdb.service_book_part_revisions.count_documents({"employee_id": employee_id}) == 0
    )
    log("5.1", "Cleanup temporary smoke-test records", cleanup_ok, employee_id)
    print_summary()

if FAIL > 0:
    sys.exit(1)
