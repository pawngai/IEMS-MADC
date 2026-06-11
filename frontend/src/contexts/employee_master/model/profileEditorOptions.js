export const mapMasterOptions = (items, mapper) => (items || []).map(mapper);

export const buildPayLevelOptions = (payLevels) =>
  mapMasterOptions(payLevels, (level) => ({
    value: level.code,
    label: level.basic_min
      ? `${level.description || level.code} (${level.basic_min}-${level.basic_max})`
      : level.description || level.code,
    search: `${level.description || ""} ${level.code || ""}`,
  }));

export const buildServiceOptions = (services) =>
  mapMasterOptions(services, (service) => ({
    value: service.code || service.service_code,
    label: service.description || service.name || service.code || service.service_code,
    search: `${service.description || ""} ${service.name || ""} ${service.code || ""} ${service.service_code || ""}`,
  }));

export const buildGroupOptions = (serviceGroups) => {
  const seen = new Set();
  return mapMasterOptions(serviceGroups, (group) => ({
    value: group.group_code || group.code,
    label: group.group_code || group.code,
  }))
    .filter((option) => {
      if (!option.value) return false;
      if (seen.has(option.value)) return false;
      seen.add(option.value);
      return true;
    })
    .map((option) => ({ ...option, search: option.label }));
};
