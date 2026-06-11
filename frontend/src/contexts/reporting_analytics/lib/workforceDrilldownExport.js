const WORKFORCE_EXPORT_FIELD_CONFIG = {
  department: {
    header: "Department",
    getValue: ({ row, getDepartmentLabel }) => getDepartmentLabel(row),
  },
  designation: {
    header: "Designation",
    getValue: ({ row, getDesignationLabel }) => getDesignationLabel(row),
  },
  employmentType: {
    header: "Employment Type",
    getValue: ({ row, getEmploymentTypeLabel }) => getEmploymentTypeLabel(row),
  },
  status: {
    header: "Employee Status",
    getValue: ({ row, getStatusLabel }) => getStatusLabel(row),
  },
  gender: {
    header: "Gender",
    getValue: ({ row, getGenderLabel }) => getGenderLabel(row),
  },
  office: {
    header: "Office",
    getValue: ({ row, getOfficeLabel }) => getOfficeLabel(row),
  },
  workflowStatus: {
    header: "Workflow Status",
    getValue: ({ row, getWorkflowStatusLabel }) => getWorkflowStatusLabel(row),
  },
  service: {
    header: "Service",
    getValue: ({ row, getServiceLabel }) => getServiceLabel(row),
  },
  serviceGroup: {
    header: "Service Group",
    getValue: ({ row, getServiceGroupLabel }) => getServiceGroupLabel(row),
  },
  maritalStatus: {
    header: "Marital Status",
    getValue: ({ row, getMaritalStatusLabel }) => getMaritalStatusLabel(row),
  },
  dateOfBirth: {
    header: "Date of Birth",
    getValue: ({ row, getDateOfBirthLabel }) => getDateOfBirthLabel(row),
  },
  initialEngagement: {
    header: "Initial Engagement",
    getValue: ({ row, getInitialEngagementLabel }) => getInitialEngagementLabel(row),
  },
  statusEffectiveDate: {
    header: "Status Effective",
    getValue: ({ row, getStatusEffectiveDateLabel }) => getStatusEffectiveDateLabel(row),
  },
  reportingOfficer: {
    header: "Reporting Officer",
    getValue: ({ row, getReportingOfficerLabel }) => getReportingOfficerLabel(row),
  },
  createdAt: {
    header: "Created",
    getValue: ({ row, getCreatedAtLabel }) => getCreatedAtLabel(row),
  },
  updatedAt: {
    header: "Updated",
    getValue: ({ row, getUpdatedAtLabel }) => getUpdatedAtLabel(row),
  },
};

const escapeCsvCell = (value) => {
  const text = String(value ?? "");
  if (!/[",\n]/.test(text)) return text;
  return `"${text.replace(/"/g, '""')}"`;
};

export const buildCsvContent = ({ headers, rows }) => {
  const csvLines = [headers.map(escapeCsvCell).join(",")];

  rows.forEach((row) => {
    csvLines.push(headers.map((header) => escapeCsvCell(row?.[header] ?? "")).join(","));
  });

  return `${csvLines.join("\r\n")}\r\n`;
};

export const buildWorkforceDrilldownExportDataset = ({
  rows,
  visibleFieldKeys,
  getDepartmentLabel,
  getDesignationLabel,
  getEmploymentTypeLabel,
  getStatusLabel,
  getGenderLabel,
  getOfficeLabel,
  getWorkflowStatusLabel,
  getServiceLabel,
  getServiceGroupLabel,
  getMaritalStatusLabel,
  getDateOfBirthLabel,
  getInitialEngagementLabel,
  getStatusEffectiveDateLabel,
  getReportingOfficerLabel,
  getCreatedAtLabel,
  getUpdatedAtLabel,
}) => {
  const selectedFieldKeys = Array.isArray(visibleFieldKeys) ? visibleFieldKeys : [];
  const optionalFields = selectedFieldKeys.filter((fieldKey) => WORKFORCE_EXPORT_FIELD_CONFIG[fieldKey]);
  const headers = [
    "Employee ID",
    "Employee Code",
    "Employee Name",
    ...optionalFields.map((fieldKey) => WORKFORCE_EXPORT_FIELD_CONFIG[fieldKey].header),
  ];

  const exportRows = (Array.isArray(rows) ? rows : []).map((row) => {
    const exportRow = {
      "Employee ID": row?.employee_id || "",
      "Employee Code": row?.employee_code || "",
      "Employee Name": row?.employee_name || "",
    };

    optionalFields.forEach((fieldKey) => {
      const fieldConfig = WORKFORCE_EXPORT_FIELD_CONFIG[fieldKey];
      exportRow[fieldConfig.header] = fieldConfig.getValue({
        row,
        getDepartmentLabel,
        getDesignationLabel,
        getEmploymentTypeLabel,
        getStatusLabel,
        getGenderLabel,
        getOfficeLabel,
        getWorkflowStatusLabel,
        getServiceLabel,
        getServiceGroupLabel,
        getMaritalStatusLabel,
        getDateOfBirthLabel,
        getInitialEngagementLabel,
        getStatusEffectiveDateLabel,
        getReportingOfficerLabel,
        getCreatedAtLabel,
        getUpdatedAtLabel,
      });
    });

    return exportRow;
  });

  return { headers, rows: exportRows };
};