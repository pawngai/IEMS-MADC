import { KANBAN_STAGES } from "@/modules/workflow/model/workQueue.constants";

const safeArray = (value) => (Array.isArray(value) ? value : []);

export const selectCountsByStage = (items) => {
  const counts = {};
  safeArray(items).forEach((item) => {
    counts[item.stage] = (counts[item.stage] || 0) + 1;
  });
  counts.ALL = safeArray(items).length;
  return counts;
};

export const selectCountsByType = (items) => {
  const counts = { identity: 0, profile: 0, service: 0, ess: 0, change_request: 0 };
  safeArray(items).forEach((item) => {
    const normalizedType = item.type === "service_opening" ? "service" : item.type;
    counts[normalizedType] = (counts[normalizedType] || 0) + 1;
  });
  return counts;
};

export const selectSlaCounts = (items) => {
  const counts = { GREEN: 0, YELLOW: 0, RED: 0, NONE: 0 };
  safeArray(items).forEach((item) => {
    counts[item.sla] = (counts[item.sla] || 0) + 1;
  });
  return counts;
};

export const selectFilteredQueueItems = ({ items, query, typeFilter, slaFilter }) => {
  const normalizedQuery = (query || "").trim().toLowerCase();
  return safeArray(items).filter((item) => {
    if (typeFilter !== "ALL") {
      const normalizedType = item.type === "service_opening" ? "service" : item.type;
      if (normalizedType !== typeFilter) return false;
    }
    if (slaFilter !== "ALL" && item.sla !== slaFilter) return false;
    if (!normalizedQuery) return true;

    return [
      item.title,
      item.subtitle,
      item.employeeId,
      item.employeeCode,
      item.type,
      item.statusLabel,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(normalizedQuery);
  });
};

export const selectKanbanColumns = (items) => {
  const columns = {};
  KANBAN_STAGES.forEach((stage) => {
    columns[stage] = [];
  });

  safeArray(items).forEach((item) => {
    const stage = KANBAN_STAGES.includes(item.stage) ? item.stage : "DRAFT";
    columns[stage].push(item);
  });

  return Object.entries(columns);
};
