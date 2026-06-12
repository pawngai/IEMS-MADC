/**
 * Projection normalizer — builds a complete service book view from raw ledger entries.
 * This is domain projection logic, not API transport.
 */

const extractMeta = (entry) => {
  if (!entry) return null;
  return {
    id: entry.id || entry._id,
    status: entry.status,
    workflow_state: entry.workflow_state || entry.status,
    schema_key: entry.schema_key,
    part_key: entry.part_key,
    entry_kind: entry.entry_kind,
    created_by: entry.created_by,
    created_at: entry.created_at,
    submitted_by: entry.submitted_by,
    submitted_at: entry.submitted_at,
    verified_by: entry.verified_by,
    verified_at: entry.verified_at,
    approved_by: entry.approved_by,
    approved_at: entry.approved_at,
    locked_by: entry.locked_by,
    locked_at: entry.locked_at,
    is_active: entry.is_active,
    supersedes_entry_id: entry.supersedes_entry_id,
    audit_hash: entry.audit_hash,
  };
};

const pickLatest = (items) => {
  if (!Array.isArray(items) || items.length === 0) return null;
  return [...items].sort((a, b) => {
    const aTs = new Date(a?.updated_at || a?.created_at || 0).getTime();
    const bTs = new Date(b?.updated_at || b?.created_at || 0).getTime();
    return bTs - aTs;
  })[0];
};

const parseIsoDate = (value) => {
  if (!value || typeof value !== "string") return null;
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) return null;
  return new Date(Date.UTC(year, month - 1, day));
};

const addUtcDays = (date, days) => {
  if (!date) return null;
  const next = new Date(date.getTime());
  next.setUTCDate(next.getUTCDate() + days);
  return next;
};

const diffCalendarInclusive = (startValue, endValue) => {
  const start = parseIsoDate(startValue);
  const end = parseIsoDate(endValue);
  if (!start || !end || end < start) {
    return { years: 0, months: 0, days: 0 };
  }

  const inclusiveEnd = addUtcDays(end, 1);
  let years = inclusiveEnd.getUTCFullYear() - start.getUTCFullYear();
  let months = inclusiveEnd.getUTCMonth() - start.getUTCMonth();
  let days = inclusiveEnd.getUTCDate() - start.getUTCDate();

  if (days < 0) {
    const previousMonthLastDay = new Date(
      Date.UTC(inclusiveEnd.getUTCFullYear(), inclusiveEnd.getUTCMonth(), 0)
    ).getUTCDate();
    days += previousMonthLastDay;
    months -= 1;
  }

  if (months < 0) {
    months += 12;
    years -= 1;
  }

  return { years, months, days };
};

const deriveVerifiedServiceTotal = (entries) => {
  if (!Array.isArray(entries) || entries.length === 0) return null;

  const datedEntries = entries
    .map((entry) => ({
      from: entry?.period_from,
      to: entry?.period_to || entry?.period_from,
    }))
    .filter((entry) => entry.from && entry.to)
    .sort((a, b) => a.from.localeCompare(b.from));

  if (datedEntries.length === 0) return null;

  return diffCalendarInclusive(datedEntries[0].from, datedEntries[datedEntries.length - 1].to);
};

const VERIFIED_WORKFLOW_STATES = new Set(["VERIFIED", "APPROVED", "LOCKED"]);

const toIsoDateFromTimestamp = (value) => {
  if (!value || typeof value !== "string") return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString().slice(0, 10);
};

const resolveVerificationDate = (meta, explicitDate) => {
  if (explicitDate) return explicitDate;
  return (
    toIsoDateFromTimestamp(meta?.verified_at) ||
    toIsoDateFromTimestamp(meta?.approved_at) ||
    toIsoDateFromTimestamp(meta?.locked_at) ||
    null
  );
};

const derivePartVEntryFromPreviousService = (entry) => {
  const meta = entry?._meta || null;
  const workflowState = String(meta?.workflow_state || meta?.status || "").toUpperCase();

  return {
    period_from: entry?.service_from || null,
    period_to: entry?.service_to || entry?.service_from || null,
    post_held: entry?.post_held || null,
    purpose_of_qualification: entry?.purpose_of_qualification || null,
    verified: VERIFIED_WORKFLOW_STATES.has(workflowState),
    verified_by: entry?.verified_by || meta?.verified_by || meta?.approved_by || meta?.locked_by || null,
    certifying_officer: entry?.certified_by || entry?.verified_by || meta?.verified_by || meta?.approved_by || meta?.locked_by || null,
    certification_date: resolveVerificationDate(meta, entry?.verification_date),
    verification_date: resolveVerificationDate(meta, entry?.verification_date),
    remarks: entry?.organization || null,
    source_part: "III",
    source_kind: "PREVIOUS_SERVICE",
    _meta: meta,
  };
};

const derivePartVEntryFromForeignService = (entry) => {
  const meta = entry?._meta || null;
  const workflowState = String(meta?.workflow_state || meta?.status || "").toUpperCase();
  const remarks = [entry?.employer, entry?.remarks].filter(Boolean).join(" - ") || null;

  return {
    period_from: entry?.service_from || null,
    period_to: entry?.service_to || entry?.service_from || null,
    post_held: entry?.post_held || null,
    purpose_of_qualification: "FOREIGN SERVICE / DEPUTATION",
    verified: VERIFIED_WORKFLOW_STATES.has(workflowState),
    verified_by: meta?.verified_by || meta?.approved_by || meta?.locked_by || null,
    certifying_officer: meta?.verified_by || meta?.approved_by || meta?.locked_by || null,
    certification_date: resolveVerificationDate(meta, entry?.verification_date),
    verification_date: resolveVerificationDate(meta, entry?.verification_date),
    remarks,
    source_part: "III",
    source_kind: "FOREIGN_SERVICE",
    _meta: meta,
  };
};

const derivePartVEntryFromPartIV = (entry) => {
  const meta = entry?._meta || null;
  const workflowState = String(meta?.workflow_state || meta?.status || "").toUpperCase();

  return {
    period_from: entry?.period_from || null,
    period_to: entry?.period_to || entry?.period_from || null,
    post_held: entry?.post_held || entry?.event_type || null,
    purpose_of_qualification: entry?.event_type || null,
    verified: VERIFIED_WORKFLOW_STATES.has(workflowState),
    verified_by: meta?.verified_by || meta?.approved_by || meta?.locked_by || null,
    certifying_officer: meta?.verified_by || meta?.approved_by || meta?.locked_by || null,
    certification_date: resolveVerificationDate(meta, entry?.verification_date),
    verification_date: resolveVerificationDate(meta, entry?.verification_date),
    remarks: entry?.remarks || entry?.office_station || entry?.reason || null,
    source_part: "IV",
    source_kind: "SERVICE_HISTORY",
    _meta: meta,
  };
};

const dedupePartVEntries = (entries) => {
  const seen = new Set();

  return (entries || []).filter((entry) => {
    const metaId = entry?._meta?.id;
    const fingerprint = metaId || [
      entry?.period_from || "",
      entry?.period_to || "",
      entry?.post_held || "",
      entry?.purpose_of_qualification || "",
      entry?.certifying_officer || "",
      entry?.source_part || "",
      entry?.source_kind || "",
    ].join("|");

    if (seen.has(fingerprint)) return false;
    seen.add(fingerprint);
    return true;
  });
};

const normalizeProjectedPartIVEntry = (entry) => {
  const rootPayload = entry?.payload && typeof entry.payload === "object" ? entry.payload : {};
  const details = rootPayload?.payload && typeof rootPayload.payload === "object" ? rootPayload.payload : {};
  const workflowState = entry?.workflow_state || entry?.status;

  return {
    period_from: rootPayload.effective_from || rootPayload.effective_date || entry?.effective_date || null,
    period_to: rootPayload.effective_to || null,
    office_station: details.office_station || rootPayload.office_station || null,
    post_held: details.post_held || rootPayload.post_held || null,
    service: details.to_service || details.service || rootPayload.to_service || rootPayload.service || null,
    service_group:
      details.to_service_group ||
      details.service_group ||
      rootPayload.to_service_group ||
      rootPayload.service_group ||
      null,
    grade: details.to_grade || details.grade || rootPayload.to_grade || rootPayload.grade || null,
    pay_level: details.pay_level || rootPayload.pay_level || null,
    basic_pay: details.basic_pay || rootPayload.basic_pay || null,
    event_type: rootPayload.event_type || entry?.event_type || null,
    event_order_number:
      details.event_order_number ||
      details.order_no ||
      rootPayload.event_order_number ||
      rootPayload.order_no ||
      null,
    event_order_date: details.event_order_date || rootPayload.event_order_date || null,
    remarks: details.remarks || details.reason || rootPayload.remarks || null,
    reason: details.reason || rootPayload.reason || null,
    suspension_date: details.suspension_date || rootPayload.suspension_date || null,
    _meta: extractMeta({
      ...entry,
      status: workflowState,
      workflow_state: workflowState,
      schema_key: entry?.schema_key || "SB_IV_SERVICE_HISTORY_ROW",
      part_key: entry?.part_key || entry?.part_code || "IV",
    }),
  };
};

export const normalizeComplete = (employeeId, entries) => {
  const entriesBySchema = entries.reduce((acc, entry) => {
    const key = entry?.schema_key;
    if (!key) return acc;
    if (!acc[key]) acc[key] = [];
    acc[key].push(entry);
    return acc;
  }, {});

  const partIEntry = pickLatest(entriesBySchema.SB_I_BIODATA);
  const partI = partIEntry ? { ...(partIEntry.payload || {}), _meta: extractMeta(partIEntry) } : null;

  const partIIAEntry = pickLatest(entriesBySchema.SB_IIA_IMMUTABLE_CERTS);
  const partIIA = partIIAEntry ? { ...(partIIAEntry.payload || {}), _meta: extractMeta(partIIAEntry) } : null;

  const partIIBEntry = pickLatest(entriesBySchema.SB_IIB_FAMILY_SHEET);
  const partIIBBase = partIIBEntry?.payload || {};
  const partIIB = Object.keys(partIIBBase).length ? { ...partIIBBase } : {};
  if (partIIBEntry) partIIB._meta = extractMeta(partIIBEntry);

  const setFromLatestPayload = (schemaKey, fieldName) => {
    const payload = pickLatest(entriesBySchema[schemaKey])?.payload || null;
    if (payload && payload[fieldName] !== undefined) {
      partIIB[fieldName] = payload[fieldName];
    }
  };

  setFromLatestPayload("SB_IIB_BANK_DETAILS", "bank_account_number");
  setFromLatestPayload("SB_IIB_BANK_DETAILS", "bank_name");
  setFromLatestPayload("SB_IIB_BANK_DETAILS", "bank_ifsc");
  setFromLatestPayload("SB_IIB_NPS_PRAN", "nps_pran_number");

  const nominationRowsOrFallback = (schemaKey, dataField, dateField, extraFields = []) => {
    const rows = (entriesBySchema[schemaKey] || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) }));
    if (rows.length > 0) return rows;

    const fallbackItems = Array.isArray(partIIBBase[dataField]) ? partIIBBase[dataField] : [];
    if (fallbackItems.length === 0) return [];

    const fallbackRow = {
      [dataField]: fallbackItems.map((item) => ({ ...item })),
      _meta: extractMeta(partIIBEntry),
    };
    if (partIIBBase[dateField] !== undefined) {
      fallbackRow[dateField] = partIIBBase[dateField];
    }
    for (const fieldName of extraFields) {
      if (partIIBBase[fieldName] !== undefined) {
        fallbackRow[fieldName] = partIIBBase[fieldName];
      }
    }
    return [fallbackRow];
  };

  const familyMemberRows = (entriesBySchema.SB_IIB_FAMILY_MEMBER_ROW || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) }));
  if (familyMemberRows.length > 0) {
    partIIB.family_members = familyMemberRows;
  } else if (!partIIB.family_members) {
    partIIB.family_members = [];
  }

  partIIB.pcf_nomination = nominationRowsOrFallback(
    "SB_IIB_PCF_NOMINATION_ROW",
    "pcf_nomination",
    "pcf_nomination_date",
    ["pcf_account_number"]
  );
  partIIB.dcr_gratuity_nomination = nominationRowsOrFallback(
    "SB_IIB_DCRG_NOMINATION_ROW",
    "dcr_gratuity_nomination",
    "dcr_gratuity_nomination_date"
  );
  partIIB.nps_nomination = nominationRowsOrFallback(
    "SB_IIB_NPS_NOMINATION_ROW",
    "nps_nomination",
    "nps_nomination_date",
    ["nps_pran_number"]
  );
  partIIB.leave_encashment_nomination = nominationRowsOrFallback(
    "SB_IIB_LEAVE_ENCASHMENT_NOMINATION_ROW",
    "leave_encashment_nomination",
    "leave_encashment_nomination_date"
  );
  partIIB.family_pension_nomination = nominationRowsOrFallback(
    "SB_IIB_FAMILY_PENSION_NOMINATION_ROW",
    "family_pension_nomination",
    "family_pension_nomination_date"
  );
  const normalizedPartIIB = Object.keys(partIIB).length ? partIIB : null;

  const partIIISummaryEntry = pickLatest(entriesBySchema.SB_III_TOTAL_QS_SUMMARY);
  const partIII = {
    ...(partIIISummaryEntry?.payload || {}),
    _meta: extractMeta(partIIISummaryEntry),
    previous_services: (entriesBySchema.SB_III_PREVIOUS_SERVICE_ROW || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) })),
    foreign_services: (entriesBySchema.SB_III_FOREIGN_SERVICE_ROW || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) })),
  };
  const normalizedPartIII =
    Object.keys(partIII).length &&
    (partIII.previous_services?.length || partIII.foreign_services?.length || Object.keys(partIII).length > 3)
      ? partIII
      : null;

  // All approved service event projections belong to Part IV: History of Service.
  // Include entries by part_code "IV" OR by event_name for legacy projected rows.
  const projectedPartIVEntries = entries
    .filter((entry) => {
      if (entry?.schema_key) return false;
      const partKey = String(entry?.part_key || entry?.part_code || "").toUpperCase();
      const isServiceEvent = String(entry?.event_name || "").startsWith("ServiceEvent");
      return partKey === "IV" || partKey === "SB_PART_IV" || isServiceEvent;
    })
    .map(normalizeProjectedPartIVEntry);
  const partIVEntries = [
    ...(entriesBySchema.SB_IV_SERVICE_HISTORY_ROW || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) })),
    ...projectedPartIVEntries,
  ];
  const partIV = partIVEntries.length ? { entries: partIVEntries } : null;

  const explicitPartVEntries = (entriesBySchema.SB_V_SERVICE_VERIFICATION_ROW || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) }));
  const derivedPartVEntries = [
    ...((partIII.previous_services || []).map(derivePartVEntryFromPreviousService)),
    ...((partIII.foreign_services || []).map(derivePartVEntryFromForeignService)),
    ...(partIVEntries.map(derivePartVEntryFromPartIV)),
  ].filter((entry) => entry.period_from && entry.period_to && entry.post_held);
  const partVEntries = dedupePartVEntries([...explicitPartVEntries, ...derivedPartVEntries]);
  const partV = partVEntries.length
    ? {
        entries: partVEntries,
        verification_entries: partVEntries,
        total_verified_service: deriveVerifiedServiceTotal(partVEntries),
      }
    : null;

  const partVIOpeningEntry = pickLatest(entriesBySchema.SB_VI_LEAVE_OPENING_BALANCE);
  const partVIOpening = partVIOpeningEntry?.payload || {};
  const partVITransactions = (entriesBySchema.SB_VI_LEAVE_TRANSACTION_ROW || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) }));
  const partVI =
    Object.keys(partVIOpening).length || partVITransactions.length
      ? { ...partVIOpening, _meta: extractMeta(partVIOpeningEntry), transactions: partVITransactions }
      : null;

  const partVII = {
    ltc_records: (entriesBySchema.SB_VII_LTC_ROW || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) })),
    hba_records: (entriesBySchema.SB_VII_HBA_ROW || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) })),
    vehicle_advance_records: (entriesBySchema.SB_VII_VEHICLE_ADVANCE_ROW || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) })),
    festival_advance_records: (entriesBySchema.SB_VII_FESTIVAL_ADVANCE_ROW || []).map((x) => ({ ...(x.payload || {}), _meta: extractMeta(x) })),
  };
  const normalizedPartVII = Object.values(partVII).some((rows) => Array.isArray(rows) && rows.length > 0) ? partVII : null;

  const comments = (entriesBySchema.SB_VIII_AUDIT_COMMENT || []).map((x) => ({
    ...(x.payload || {}),
    _meta: extractMeta(x),
    status: x?.payload?.status || x.status || "OPEN",
  }));
  const resolvedCount = comments.filter((item) => String(item.status || "").toUpperCase() === "RESOLVED").length;
  const partVIII =
    comments.length > 0
      ? {
          comments,
          total_comments: comments.length,
          resolved_comments: resolvedCount,
          open_comments: comments.length - resolvedCount,
        }
      : null;

  const complete = {
    employee_id: employeeId,
    _raw_entries: entries,
    part_i: partI,
    part_ii_a: partIIA,
    part_ii_b: normalizedPartIIB,
    part_iii: normalizedPartIII,
    part_iv: partIV,
    part_v: partV,
    part_vi: partVI,
    part_vii: normalizedPartVII,
    part_viii: partVIII,
  };

  const partPresence = {
    I: !!complete.part_i,
    "II-A": !!complete.part_ii_a,
    "II-B": !!complete.part_ii_b,
    III: !!complete.part_iii,
    IV: !!complete.part_iv,
    V: !!complete.part_v,
    VI: !!complete.part_vi,
    VII: !!complete.part_vii,
    VIII: !!complete.part_viii,
  };

  complete.parts_completed = Object.entries(partPresence)
    .filter(([, present]) => present)
    .map(([key]) => key);
  complete.completion_percentage = Math.round((complete.parts_completed.length / 9) * 100);

  return complete;
};
