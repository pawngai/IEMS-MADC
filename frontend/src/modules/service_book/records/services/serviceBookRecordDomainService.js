import { apiClient as api } from "@/platform/api/httpClient";

const BASE = "/service-book/records";

const EVENT_TYPE_ALIASES = {
  APPOINTMENT: "APPOINTMENT",
  CONFIRMATION: "CONFIRMATION",
  PROMOTION: "PROMOTION",
  TRANSFER: "TRANSFER",
  PAY: "PAY",
  INCREMENT: "INCREMENT",
  DEPUTATION: "DEPUTATION",
  SUSPENSION: "SUSPENSION",
  REINSTATEMENT: "REINSTATEMENT",
  RETIREMENT: "RETIREMENT",
  DISCIPLINARY: "DISCIPLINARY",
  CUSTOM: "GENERIC",
  GENERIC: "GENERIC",
  FINANCIAL_UPGRADATION: "FINANCIAL_UPGRADATION",
  CPC_PAY_FIXATION: "CPC_PAY_FIXATION",
  CPC_CHANGE_FIXATION: "CPC_PAY_FIXATION",
};

const isCpcChangeFixationCommand = (payload) => {
  const eventType = String(payload?.event_type || payload?.eventType || payload?.type || "").trim().toUpperCase();
  return eventType === "CPC_CHANGE_FIXATION" || eventType === "CPC_PAY_FIXATION";
};

export const classifyServiceRecord = (payloadOrType) => {
  const raw =
    typeof payloadOrType === "object" && payloadOrType !== null
      ? payloadOrType.event_type || payloadOrType.eventType || payloadOrType.type || payloadOrType.event_name
      : payloadOrType;

  const normalized = String(raw || "GENERIC").trim().toUpperCase() || "GENERIC";
  const eventType = EVENT_TYPE_ALIASES[normalized] || "GENERIC";

  return {
    input: normalized,
    event_type: eventType,
    classification: eventType,
    can_route_to_service_book: true,
  };
};

export const validateServiceRecordPayload = (payload) => {
  if (!payload || typeof payload !== "object") {
    throw new Error("Service Book record payload must be an object");
  }
  if (!String(payload.employee_id || "").trim()) {
    throw new Error("employee_id is required");
  }

  if (isCpcChangeFixationCommand(payload)) {
    return {
      ...payload,
      event_type: "CPC_PAY_FIXATION",
    };
  }

  const eventPayload = payload.payload || {};
  if (typeof eventPayload !== "object" || Array.isArray(eventPayload)) {
    throw new Error("payload must be an object");
  }
  if (Object.keys(eventPayload).length === 0) {
    throw new Error("payload cannot be empty");
  }

  if (payload.effective_from && payload.effective_to) {
    const fromDate = new Date(payload.effective_from);
    const toDate = new Date(payload.effective_to);
    if (!Number.isNaN(fromDate.getTime()) && !Number.isNaN(toDate.getTime()) && toDate < fromDate) {
      throw new Error("effective_to cannot be earlier than effective_from");
    }
  }

  const classification = classifyServiceRecord(payload);
  return {
    ...payload,
    event_type: classification.event_type,
  };
};

export const routeServiceRecordToServiceBook = (approvedEvent) => ({
  routed: String(approvedEvent?.status || "").toUpperCase() === "APPROVED",
  target: "service_book",
  mode: "event_bus_projection",
  service_book_remains_authoritative: true,
});

export const recordServiceBookRecord = async (payload) => {
  const normalized = validateServiceRecordPayload(payload);
  return api.post(BASE, normalized);
};

export const applyApprovedServiceRecord = async (serviceEventId) => {
  const response = await api.post(`${BASE}/${serviceEventId}/approve`);
  return {
    ...response,
    service_book_route: routeServiceRecordToServiceBook(response?.data || response),
  };
};
