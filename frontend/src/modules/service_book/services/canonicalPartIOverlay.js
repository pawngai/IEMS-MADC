export function applyCanonicalPartIOverlay(serviceBook, partIDefaults) {
  if (!serviceBook || !partIDefaults) return serviceBook;

  const partI = serviceBook.part_i || {};
  const nextPartI = { ...partI };
  let changed = false;

  if (partIDefaults.name_in_block_letters && partIDefaults.name_in_block_letters !== partI.name_in_block_letters) {
    nextPartI.name_in_block_letters = partIDefaults.name_in_block_letters;
    changed = true;
  }

  if (partIDefaults.employee_code && partIDefaults.employee_code !== partI.employee_code) {
    nextPartI.employee_code = partIDefaults.employee_code;
    changed = true;
  }

  if (partIDefaults.photograph_url && !partI.photograph_url) {
    nextPartI.photograph_url = partIDefaults.photograph_url;
    changed = true;
  }

  if (!changed && (!partIDefaults.employee_code || partIDefaults.employee_code === serviceBook.employee_code)) {
    return serviceBook;
  }

  return {
    ...serviceBook,
    employee_code: partIDefaults.employee_code || serviceBook.employee_code,
    part_i: nextPartI,
  };
}