const toTitleCase = (value) => String(value || "")
  .trim()
  .toLowerCase()
  .replace(/\b\w/g, (char) => char.toUpperCase());

const isSyntheticSeedName = (value) => /^TEST(?:[_\s-]|$)/i.test(String(value || "").trim());

export const getReadablePersonName = (value) => {
  const trimmed = String(value || "").trim();
  if (!trimmed) return "";
  if (!isSyntheticSeedName(trimmed)) return trimmed;

  const normalized = trimmed
    .replace(/[_-]+/g, " ")
    .replace(/\b(?:[0-9a-f]{6,}|\d{8,})\b/gi, " ")
    .replace(/\s+/g, " ")
    .trim();

  return toTitleCase(normalized || trimmed);
};

export default getReadablePersonName;