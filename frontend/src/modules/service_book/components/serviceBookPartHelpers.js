/**
 * Format a date string (ISO or JS Date) to a consistent human-friendly format.
 * Returns "22 Mar 2026" style by default; returns "-" for missing/invalid input.
 */
export function formatDisplayDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

/**
 * Format a date as a lifecycle timestamp with time.
 * Returns "22 Mar 2026, 5:57 PM" style.
 */
export function formatLifecycleTimestamp(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString('en-GB', {
    timeZone: 'UTC',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function formatListForTextarea(value) {
  if (!value) return '';
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item?.description) return item.description;
        const parts = [item?.degree, item?.subject, item?.year, item?.university, item?.institute]
          .filter(Boolean)
          .join(' ');
        return parts || JSON.stringify(item);
      })
      .join('\n');
  }
  return String(value);
}

export function parseListFromTextarea(value) {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((description) => ({ description }));
}

export function formatMarksForTextarea(value) {
  return Array.isArray(value) ? value.join('\n') : '';
}

export function parseMarksFromTextarea(value) {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

export function listToDisplayLines(list) {
  if (!Array.isArray(list) || list.length === 0) return [];
  return list.map((item) => {
    if (typeof item === 'string') return item;
    if (item?.description) return item.description;
    const fallback = [item?.degree, item?.subject, item?.year, item?.university, item?.institute]
      .filter(Boolean)
      .join(' ');
    return fallback || JSON.stringify(item);
  });
}

export function resolveServiceBookAssetUrl(pathOrUrl) {
  if (!pathOrUrl) return null;
  if (pathOrUrl.startsWith('http')) return pathOrUrl;

  const runtimeHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  const envBackend = process.env.REACT_APP_BACKEND_URL || '';
  const isRuntimeLocalhost = runtimeHost === 'localhost' || runtimeHost === '127.0.0.1';

  let envBackendHost = '';
  if (envBackend) {
    try {
      envBackendHost = new URL(envBackend).hostname;
    } catch {
      envBackendHost = '';
    }
  }

  const isEnvLocalhost = envBackendHost === 'localhost' || envBackendHost === '127.0.0.1';
  const backend = envBackend && !(isEnvLocalhost && !isRuntimeLocalhost)
    ? envBackend
    : `http://${runtimeHost}:8000`;

  return `${backend}${pathOrUrl.startsWith('/') ? '' : '/'}${pathOrUrl}`;
}

export function getLinkedDocuments(source) {
  if (!source || !Array.isArray(source.supporting_documents)) return [];
  return source.supporting_documents;
}

export function extractFilename(doc) {
  if (doc?.filename) return doc.filename;
  if (!doc?.url || typeof doc.url !== 'string') return '';
  const tail = doc.url.split('/').pop() || '';
  return tail.split('?')[0] || '';
}
