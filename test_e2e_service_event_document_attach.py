"""
Focused live smoke test for Service Events document attachment.

This follows the repository's existing live E2E pattern:
  1. Log in as a data-entry operator.
  2. Resolve a real service-event stream for a seeded regular employee.
  3. Upload a temporary PDF through the documents context.
  4. Attach that uploaded document to a live service event.
  5. Verify the event stream reflects the attachment.
  6. Clean up by removing the event reference and deleting the document.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any
from urllib.parse import quote, urlparse

import requests
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = os.getenv("IEMS_E2E_BASE", "http://localhost:8000/api")
MONGO_URI = os.getenv("IEMS_E2E_MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("IEMS_E2E_DB_NAME", "iems_db")
DEFAULT_EMPLOYEE_REF = "MADC-1992-R0001"
EMPLOYEE_REF = os.getenv("IEMS_E2E_SERVICE_EVENT_EMPLOYEE_REF", DEFAULT_EMPLOYEE_REF).strip() or DEFAULT_EMPLOYEE_REF
TARGET_EVENT_ID = (os.getenv("IEMS_E2E_SERVICE_EVENT_ID") or "").strip()
DOCUMENT_TYPE = "ORDER"
CATEGORY = "PROMOTION_ORDER"
SOURCE_CONTEXT = "service_events.attach"
TIMEOUT = 20
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


def required_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if value:
        return value
    raise RuntimeError(f"Required environment variable missing: {name}")


DE_CREDS = {
    "email": os.getenv("IEMS_E2E_DE_EMAIL", "global.dataentry@madc.gov.in"),
    "password": required_env("IEMS_E2E_DE_PASSWORD"),
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


def response_json(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
        return payload if isinstance(payload, dict) else {"value": payload}
    except ValueError:
        return {}


def auth(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


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


def safe_get(url: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None):
    try:
        return session.get(url, headers=headers, params=params, timeout=TIMEOUT)
    except Exception as exc:
        print(f"    WARNING: GET {url} failed: {exc}")
        return None


def safe_post(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_payload: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
):
    try:
        return session.post(
            url,
            headers=headers,
            params=params,
            json=json_payload,
            files=files,
            timeout=TIMEOUT,
        )
    except Exception as exc:
        print(f"    WARNING: POST {url} failed: {exc}")
        return None


def safe_delete(url: str, *, headers: dict[str, str] | None = None):
    try:
        return session.delete(url, headers=headers, timeout=TIMEOUT)
    except Exception as exc:
        print(f"    WARNING: DELETE {url} failed: {exc}")
        return None


def select_target_event(stream: dict[str, Any]) -> dict[str, Any] | None:
    events = stream.get("events") or []
    if TARGET_EVENT_ID:
        for event in events:
            if str(event.get("service_event_id") or "") == TARGET_EVENT_ID:
                return event
        return None
    for event in events:
        if not event.get("is_voided") and event.get("service_event_id"):
            return event
    return None


def _normalized_employment_type(*, employee_id: str | None = None, employee_code: str | None = None) -> str:
    query = None
    if employee_id:
        query = {"employee_id": str(employee_id).strip()}
    elif employee_code:
        query = {"employee_code": str(employee_code).strip()}
    if not query:
        return ""

    profile = mdb.employee_profile_read_models.find_one(
        query,
        {"_id": 0, "employment_type": 1, "current_employment_type": 1},
    ) or {}
    identity = mdb.employee_identities.find_one(
        query,
        {"_id": 0, "employment_type": 1, "employment_type_code": 1},
    ) or {}
    return str(
        profile.get("employment_type")
        or profile.get("current_employment_type")
        or identity.get("employment_type")
        or identity.get("employment_type_code")
        or ""
    ).strip().upper()


def resolve_regular_employee_ref(employee_ref: str) -> str | None:
    normalized_ref = str(employee_ref or "").strip()
    if not normalized_ref:
        return None

    identity = mdb.employee_identities.find_one(
        {"$or": [{"employee_id": normalized_ref}, {"employee_code": normalized_ref}]},
        {"_id": 0, "employee_id": 1, "employee_code": 1},
    ) or {}
    resolved_employee_id = str(identity.get("employee_id") or normalized_ref).strip()
    resolved_employee_code = str(identity.get("employee_code") or normalized_ref).strip()
    employment_type = _normalized_employment_type(
        employee_id=resolved_employee_id or None,
        employee_code=resolved_employee_code or None,
    )
    if employment_type in {"REGULAR", "REG"}:
        return resolved_employee_code or resolved_employee_id or None
    return None


def find_regular_service_event_ref() -> str | None:
    records = mdb.service_event_records.find(
        {"service_event_id": {"$exists": True}, "is_voided": {"$ne": True}},
        {"_id": 0, "employee_id": 1},
    ).limit(500)
    seen: set[str] = set()
    for record in records:
        employee_id = str(record.get("employee_id") or "").strip()
        if not employee_id:
            continue
        if employee_id in seen:
            continue
        seen.add(employee_id)
        identity = mdb.employee_identities.find_one(
            {"employee_id": employee_id},
            {"_id": 0, "employee_code": 1},
        ) or {}
        employment_type = _normalized_employment_type(
            employee_id=employee_id,
            employee_code=str(identity.get("employee_code") or "").strip() or None,
        )
        if employment_type not in {"REGULAR", "REG"}:
            continue
        return str(identity.get("employee_code") or employee_id).strip() or employee_id
    return None


def find_regular_employee_ref() -> str | None:
    profile = mdb.employee_profile_read_models.find_one(
        {"employment_type": {"$in": ["REGULAR", "REG"]}},
        {"_id": 0, "employee_id": 1, "employee_code": 1},
    )
    if not profile:
        profile = mdb.employee_profile_read_models.find_one(
            {"current_employment_type": {"$in": ["REGULAR", "REG"]}},
            {"_id": 0, "employee_id": 1, "employee_code": 1},
        )
    if profile:
        return str(profile.get("employee_code") or profile.get("employee_id") or "").strip() or None

    identity = mdb.employee_identities.find_one(
        {"employment_type": {"$in": ["REGULAR", "REG"]}},
        {"_id": 0, "employee_id": 1, "employee_code": 1},
    )
    if not identity:
        identity = mdb.employee_identities.find_one(
            {"employment_type_code": {"$in": ["REGULAR", "REG"]}},
            {"_id": 0, "employee_id": 1, "employee_code": 1},
        )
    if not identity:
        return None
    return str(identity.get("employee_code") or identity.get("employee_id") or "").strip() or None


def fetch_service_event_stream(employee_ref: str, token: str | None):
    return safe_get(
        f"{BASE}/service-book/records/employees/{quote(employee_ref, safe='')}",
        headers=auth(token),
    )


def create_temporary_service_event(employee_ref: str, token: str | None) -> tuple[bool, str]:
    response = safe_post(
        f"{BASE}/service-book/records/record",
        headers={**auth(token), "Content-Type": "application/json"},
        json_payload={
            "employee_id": employee_ref,
            "event_type": "GENERIC",
            "part_code": "IV",
            "payload": {
                "remarks": "Temporary service-event document attach smoke record",
            },
            "effective_from": "2026-01-01",
            "source_context": SOURCE_CONTEXT,
            "source_reference_id": f"smoke-{int(time.time())}",
        },
    )
    payload = response_json(response) if response is not None else {}
    service_event_id = str(payload.get("service_event_id") or "")
    return response is not None and response.status_code == 200 and bool(service_event_id), service_event_id


def cleanup_attachment(*, employee_id: str, service_event_id: str, document_id: str) -> tuple[bool, str]:
    result = mdb.service_book_records.update_one(
        {"employee_id": employee_id, "service_event_id": service_event_id},
        {"$pull": {"documents": {"document_id": document_id}}},
    )
    ok = result.modified_count == 1
    detail = f"matched={result.matched_count}, modified={result.modified_count}, document_id={document_id}"
    return ok, detail


def print_summary() -> None:
    print("\n" + "=" * 72)
    print(f"  RESULTS:  {PASS} passed,  {FAIL} failed,  {PASS + FAIL} total")
    print("=" * 72)
    if FAIL > 0:
        print("\n  Failed steps:")
        for result in RESULTS:
            if not result["ok"]:
                print(f"    FAIL {result['step']}: {result['desc']}  ->  {result['detail']}")


print("\n" + "=" * 72)
print("  IEMS Service Event Document Attach Smoke Test")
print("=" * 72)

token = login(DE_CREDS["email"], DE_CREDS["password"])
log("1.1", "Data Entry operator login", token is not None, DE_CREDS["email"])

employee_id = ""
service_event_id = ""
uploaded_document_id = ""
uploaded_filename = ""
attach_verified = False
temporary_service_event_created = False

try:
    resolved_employee_ref = EMPLOYEE_REF
    stream_response = fetch_service_event_stream(resolved_employee_ref, token)
    if stream_response is None or stream_response.status_code in (403, 404):
        fallback_ref = find_regular_service_event_ref()
        if fallback_ref and fallback_ref != resolved_employee_ref:
            print(
                f"    INFO: Falling back service-event employee ref from {resolved_employee_ref} to {fallback_ref}"
            )
            resolved_employee_ref = fallback_ref
            stream_response = fetch_service_event_stream(resolved_employee_ref, token)
    if stream_response is None or stream_response.status_code in (403, 404) or not (response_json(stream_response).get("events") if stream_response is not None else []):
        fallback_ref = resolve_regular_employee_ref(resolved_employee_ref) or find_regular_employee_ref()
        if fallback_ref:
            print(f"    INFO: Creating temporary service event for {fallback_ref}")
            resolved_employee_ref = fallback_ref
            created_ok, created_event_id = create_temporary_service_event(resolved_employee_ref, token)
            temporary_service_event_created = created_ok
            if created_ok:
                stream_response = fetch_service_event_stream(resolved_employee_ref, token)
                if not TARGET_EVENT_ID:
                    print(f"    INFO: Temporary service_event_id={created_event_id}")
    stream_ok = stream_response is not None and stream_response.status_code == 200
    stream_payload = response_json(stream_response) if stream_response is not None else {}
    employee_id = str(stream_payload.get("employee_id") or "")
    log(
        "2.1",
        "Resolve seeded service-event stream",
        stream_ok,
        employee_id or f"ref={resolved_employee_ref}, status={getattr(stream_response, 'status_code', 'request-failed')}",
    )

    target_event = select_target_event(stream_payload) if stream_ok else None
    service_event_id = str((target_event or {}).get("service_event_id") or "")
    target_ok = target_event is not None
    target_detail = service_event_id or (
        f"requested={TARGET_EVENT_ID}" if TARGET_EVENT_ID else "no non-voided events found"
    )
    log("2.2", "Select target service event", target_ok, target_detail)

    if not token or not stream_ok or not target_ok:
        print_summary()
        sys.exit(1)

    timestamp = int(time.time())
    original_name = f"service-event-attach-smoke-{timestamp}.pdf"
    upload_response = safe_post(
        f"{BASE}/documents/document",
        headers=auth(token),
        params={
            "document_type": DOCUMENT_TYPE,
            "category": CATEGORY,
            "source_context": SOURCE_CONTEXT,
        },
        files={
            "file": (
                original_name,
                b"%PDF-1.4\n%smoke\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<<>>\n%%EOF\n",
                "application/pdf",
            )
        },
    )
    upload_ok = upload_response is not None and upload_response.status_code == 200
    upload_payload = response_json(upload_response) if upload_response is not None else {}
    uploaded_document_id = str(upload_payload.get("document_id") or "")
    uploaded_filename = str(upload_payload.get("filename") or "")
    log(
        "3.1",
        "Upload temporary document through documents context",
        upload_ok,
        uploaded_document_id or f"status={getattr(upload_response, 'status_code', 'request-failed')}",
    )

    list_response = safe_get(
        f"{BASE}/documents/files",
        headers=auth(token),
        params={
            "query": original_name,
            "source_context": SOURCE_CONTEXT,
            "limit": 20,
        },
    )
    list_payload = response_json(list_response) if list_response is not None else {}
    list_items = list_payload.get("items") or []
    library_ok = any(item.get("document_id") == uploaded_document_id for item in list_items)
    log(
        "3.2",
        "Uploaded document appears in the document library",
        library_ok,
        f"items={len(list_items)}",
    )

    attach_response = safe_post(
        f"{BASE}/service-book/records/{quote(service_event_id, safe='')}/documents",
        headers={**auth(token), "Content-Type": "application/json"},
        json_payload={
            "service_event_id": "ignored-by-path",
            "document_id": uploaded_document_id,
            "document_type": DOCUMENT_TYPE,
        },
    )
    attach_ok = attach_response is not None and attach_response.status_code == 200
    attach_payload = response_json(attach_response) if attach_response is not None else {}
    log(
        "4.1",
        "Attach uploaded document to the live service event",
        attach_ok,
        f"documents_count={attach_payload.get('documents_count', '??')}",
    )

    verify_response = safe_get(
        f"{BASE}/service-book/records/employees/{quote(employee_id or resolved_employee_ref, safe='')}",
        headers=auth(token),
    )
    verify_payload = response_json(verify_response) if verify_response is not None else {}
    verify_events = verify_payload.get("events") or []
    attached_event = next(
        (event for event in verify_events if str(event.get("service_event_id") or "") == service_event_id),
        None,
    )
    attached_documents = (attached_event or {}).get("documents") or []
    attach_verified = any(doc.get("document_id") == uploaded_document_id for doc in attached_documents)
    log(
        "4.2",
        "Service-event stream reflects the attachment",
        attach_verified,
        f"documents={len(attached_documents)}",
    )
finally:
    if uploaded_document_id and employee_id and service_event_id:
        cleanup_ok, cleanup_detail = cleanup_attachment(
            employee_id=employee_id,
            service_event_id=service_event_id,
            document_id=uploaded_document_id,
        )
        log(
            "5.1",
            "Cleanup removes the service-event document reference",
            cleanup_ok or not attach_verified,
            cleanup_detail,
        )

    if temporary_service_event_created and service_event_id:
        delete_result = mdb.service_book_records.delete_one({"service_event_id": service_event_id})
        log(
            "5.1b",
            "Cleanup deletes the temporary service event",
            delete_result.deleted_count == 1,
            f"deleted={delete_result.deleted_count}, service_event_id={service_event_id}",
        )

    if uploaded_filename:
        delete_response = safe_delete(
            f"{BASE}/documents/files/{quote(uploaded_filename, safe='')}",
            headers=auth(token),
        )
        delete_ok = delete_response is not None and delete_response.status_code == 200
        delete_payload = response_json(delete_response) if delete_response is not None else {}
        log(
            "5.2",
            "Cleanup deletes the temporary uploaded document",
            delete_ok,
            delete_payload.get("filename") or uploaded_filename or f"status={getattr(delete_response, 'status_code', 'request-failed')}",
        )

    mongo.close()

print_summary()
sys.exit(0 if FAIL == 0 else 1)