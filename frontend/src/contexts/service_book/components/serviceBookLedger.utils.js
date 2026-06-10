export function getPartStats(partKey, data) {
  if (!data) return { entryCount: 0, hasDrafts: false };
  const workflowCounts = {};

  const collect = (items) => {
    if (!Array.isArray(items)) return;
    items.forEach((item) => {
      const state = item?._meta?.workflow_state || item?._meta?.status;
      if (state) workflowCounts[state] = (workflowCounts[state] || 0) + 1;
    });
  };

  if (partKey === "IV") collect(data.entries);
  if (partKey === "VI") collect(data.transactions);
  if (partKey === "VIII") collect(data.comments);
  if (partKey === "III") {
    collect(data.previous_services);
    collect(data.foreign_services);
  }
  if (partKey === "V") collect(data.verification_entries);
  if (partKey === "VII") {
    collect(data.ltc_records);
    collect(data.hba_records);
    collect(data.festival_advance_records);
    collect(data.vehicle_advance_records);
  }
  if (partKey === "II-B") {
    collect(data.pcf_nomination);
    collect(data.dcr_gratuity_nomination);
    collect(data.nps_nomination);
    collect(data.leave_encashment_nomination);
    collect(data.family_pension_nomination);
  }

  const entryCount = Object.values(workflowCounts).reduce((a, b) => a + b, 0);
  const hasDrafts = (workflowCounts.DRAFT || 0) > 0;
  return { entryCount, hasDrafts };
}
