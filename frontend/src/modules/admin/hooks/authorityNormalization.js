const AUTHORITY_ALIAS_MAP = {
  ADMIN: "SYSTEM_ADMIN",
};

export const normalizeAuthorityCode = (code) => {
  if (!code) return code;
  const normalized = String(code).trim().toUpperCase();
  return AUTHORITY_ALIAS_MAP[normalized] || normalized;
};

export const dedupeAuthorityCodes = (authorities) => {
  const seen = new Set();
  const deduped = [];

  for (const authority of authorities || []) {
    const normalized = normalizeAuthorityCode(authority);
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    deduped.push(normalized);
  }

  return deduped;
};

export const normalizeAuthorityList = (authorities) => {
  const seen = new Set();
  const normalizedList = [];

  for (const authority of authorities || []) {
    const rawCode = typeof authority === "string" ? authority : authority?.code;
    const code = normalizeAuthorityCode(rawCode);
    if (!code || seen.has(code)) continue;

    seen.add(code);

    if (typeof authority === "string") {
      normalizedList.push(code);
      continue;
    }

    normalizedList.push({
      ...authority,
      code,
      name: authority?.name || code,
    });
  }

  return normalizedList;
};