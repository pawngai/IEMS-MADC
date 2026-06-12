import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useUrlTableState } from "@/shared/lib/useUrlTableState";
import { employeeProfileApi } from "@/modules/employee_master";
import { formatDirectoryEnumLabel } from "@/modules/employee_master";
import { employeeMasterKeys } from "@/modules/employee_master/queries/keys";
import { mastersAPI } from "@/modules/organization_master";
import { toast } from "sonner";

const EMPTY_LIST = [];
const EMPTY_DIRECTORY_PAGE = { employees: EMPTY_LIST, total: 0, totalPages: 1 };

const unwrapMasterList = (response, key) =>
  Array.isArray(response.data) ? response.data : response.data?.[key] || [];

const PAGE_SIZE = 20;

const EMPLOYEE_STATUSES = ["ACTIVE", "RETIRED", "SUSPENDED", "DECEASED"];
const RECRUITMENT_MODES = ["DIRECT", "PROMOTION", "DEPUTATION", "TRANSFER", "COMPASSIONATE"];

const DIRECTORY_FILTERS = {
  query: { param: "q", defaultValue: "" },
  status: { param: "status", defaultValue: "ALL" },
  department: { param: "dept", defaultValue: "ALL" },
  type: { param: "type", defaultValue: "ALL" },
  designation: { param: "desig", defaultValue: "ALL" },
  office: { param: "office", defaultValue: "ALL" },
  employeeStatus: { param: "emp_status", defaultValue: "ALL" },
  recruitment: { param: "recruit", defaultValue: "ALL" },
  payLevel: { param: "pay", defaultValue: "ALL" },
  service: { param: "svc", defaultValue: "ALL" },
  group: { param: "grp", defaultValue: "ALL" },
  dateFrom: { param: "date_from", defaultValue: "" },
  dateTo: { param: "date_to", defaultValue: "" },
};

const normalizeDirectoryEmployee = (employee, source = "profile") => {
  if (!employee || typeof employee !== "object") return employee;
  const isIdentitySource = source === "identity";
  const identityWorkflowStatus = isIdentitySource
    ? employee.identity_workflow_status || employee.workflow_status || "DRAFT"
    : employee.identity_workflow_status || employee.employee_identity_workflow_status || "-";
  const profileWorkflowStatus = isIdentitySource
    ? employee.profile_workflow_status || "-"
    : employee.profile_workflow_status || employee.workflow_status || "DRAFT";

  return {
    ...employee,
    identity_workflow_status: identityWorkflowStatus,
    profile_workflow_status: profileWorkflowStatus,
  };
};

/**
 * Encapsulates employee directory state: server-side search, filtering,
 * sorting, pagination, and reference data loading.
 */
export function useEmployeeDirectory({
  useUserDirectory = false,
  listUserDirectory = null,
  useIdentityDirectory = false,
  listIdentityDirectory = null,
} = {}) {
  // ── URL-derived state (filters / sort / pagination) ───────────────
  const {
    values: filterValues,
    setValue: setFilterValue,
    page,
    setPage,
    sortField,
    sortDir,
    toggleSort,
    clearFilters,
  } = useUrlTableState({
    filters: DIRECTORY_FILTERS,
    sort: { fieldParam: "sort", dirParam: "dir", defaultField: "full_name", defaultDir: "asc" },
    pageParam: "page",
  });

  const {
    query,
    status: activeStatusFilter,
    department: departmentFilter,
    type: typeFilter,
    designation: designationFilter,
    office: officeFilter,
    employeeStatus: employeeStatusFilter,
    recruitment: recruitmentFilter,
    payLevel: payLevelFilter,
    service: serviceFilter,
    group: groupFilter,
    dateFrom: dateFromFilter,
    dateTo: dateToFilter,
  } = filterValues;

  // ── Debounced search ──────────────────────────────────────────────
  const [debouncedQuery, setDebouncedQuery] = useState(query);
  const debounceRef = useRef(null);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(debounceRef.current);
  }, [query]);

  // ── Fetch employees from server (TanStack Query) ─────────────────
  const directorySource =
    useIdentityDirectory && listIdentityDirectory
      ? "identity"
      : useUserDirectory && listUserDirectory
        ? "user"
        : "profile";

  const listFilters = {
    source: directorySource,
    page,
    q: debouncedQuery.trim(),
    status: activeStatusFilter,
    department: departmentFilter,
    type: typeFilter,
    designation: designationFilter,
    office: officeFilter,
    employeeStatus: employeeStatusFilter,
    recruitment: recruitmentFilter,
    payLevel: payLevelFilter,
    service: serviceFilter,
    group: groupFilter,
    dateFrom: dateFromFilter,
    dateTo: dateToFilter,
    sortField,
    sortDir,
  };

  const fetchDirectoryPage = useCallback(
    async () => {
      const params = {
        page,
        page_size: PAGE_SIZE,
        sort_by: sortField || undefined,
        sort_dir: sortDir || undefined,
      };
      const q = debouncedQuery.trim();
      if (q) params.q = q;
      if (activeStatusFilter !== "ALL")
        params.profile_workflow_status = activeStatusFilter;
      if (departmentFilter !== "ALL") params.department_id = departmentFilter;
      if (typeFilter !== "ALL") params.employment_type = typeFilter;
      if (designationFilter !== "ALL") params.designation_id = designationFilter;
      if (officeFilter !== "ALL") params.office_id = officeFilter;
      if (employeeStatusFilter !== "ALL") params.employee_status = employeeStatusFilter;
      if (recruitmentFilter !== "ALL") params.recruitment_mode = recruitmentFilter;
      if (payLevelFilter !== "ALL") params.pay_level = payLevelFilter;
      if (serviceFilter !== "ALL") params.service = serviceFilter;
      if (groupFilter !== "ALL") params.service_group = groupFilter;
      if (dateFromFilter) params.date_from = dateFromFilter;
      if (dateToFilter) params.date_to = dateToFilter;

      try {
        let res;
        let rowSource = "profile";
        if (useIdentityDirectory && listIdentityDirectory) {
          rowSource = "identity";
          res = await listIdentityDirectory({
            page,
            page_size: PAGE_SIZE,
            search: q || undefined,
            status: activeStatusFilter !== "ALL" ? activeStatusFilter : undefined,
            department_id: departmentFilter !== "ALL" ? departmentFilter : undefined,
            employment_type: typeFilter !== "ALL" ? typeFilter : undefined,
            sort_by: sortField || undefined,
            sort_dir: sortDir || undefined,
          });
        } else if (useUserDirectory && listUserDirectory) {
          res = await listUserDirectory({
            skip: (page - 1) * PAGE_SIZE,
            limit: PAGE_SIZE,
            search: q || undefined,
            profile_workflow_status: activeStatusFilter !== "ALL" ? activeStatusFilter : undefined,
            department: departmentFilter !== "ALL" ? departmentFilter : undefined,
            employment_type: typeFilter !== "ALL" ? typeFilter : undefined,
            designation_id: designationFilter !== "ALL" ? designationFilter : undefined,
            office_id: officeFilter !== "ALL" ? officeFilter : undefined,
            employee_status: employeeStatusFilter !== "ALL" ? employeeStatusFilter : undefined,
            recruitment_mode: recruitmentFilter !== "ALL" ? recruitmentFilter : undefined,
            pay_level: payLevelFilter !== "ALL" ? payLevelFilter : undefined,
            service: serviceFilter !== "ALL" ? serviceFilter : undefined,
            service_group: groupFilter !== "ALL" ? groupFilter : undefined,
            date_from: dateFromFilter || undefined,
            date_to: dateToFilter || undefined,
            sort_by: sortField || undefined,
            sort_dir: sortDir || undefined,
          });
        } else {
          res = await employeeProfileApi.list(params);
        }
        const data = res.data || {};
        const rows = data.employees || data.profiles || data.identities || data || [];
        const total = data.total ?? rows.length;
        return {
          employees: Array.isArray(rows) ? rows.map((row) => normalizeDirectoryEmployee(row, rowSource)) : [],
          total,
          totalPages: data.total_pages ?? Math.max(1, Math.ceil(total / PAGE_SIZE)),
        };
      } catch (error) {
        console.error("Failed to load employees:", error);
        toast.error("Failed to load employee directory");
        return EMPTY_DIRECTORY_PAGE;
      }
    },
    [debouncedQuery, activeStatusFilter, departmentFilter, typeFilter, designationFilter, officeFilter, employeeStatusFilter, recruitmentFilter, payLevelFilter, serviceFilter, groupFilter, dateFromFilter, dateToFilter, sortField, sortDir, page, useUserDirectory, listUserDirectory, useIdentityDirectory, listIdentityDirectory],
  );

  const directoryQuery = useQuery({
    queryKey: employeeMasterKeys.directoryList(listFilters),
    queryFn: fetchDirectoryPage,
    placeholderData: keepPreviousData,
  });

  const directoryPage = directoryQuery.data ?? EMPTY_DIRECTORY_PAGE;
  const employees = directoryPage.employees;
  const total = directoryPage.total;
  const totalPages = directoryPage.totalPages;
  const loading = directoryQuery.isPending;
  const refreshing = directoryQuery.isFetching && !directoryQuery.isPending;

  // ── Reference data (cached indefinitely; master data rarely changes) ─
  const referenceQuery = useQuery({
    queryKey: employeeMasterKeys.directoryReference(),
    staleTime: Infinity,
    queryFn: async () => {
      const [deptRes, typeRes, desigRes, officeRes, payRes, svcRes, grpRes] = await Promise.all([
        mastersAPI.getDepartments().catch(() => ({ data: [] })),
        mastersAPI.getEmploymentTypes().catch(() => ({ data: [] })),
        mastersAPI.getDesignations().catch(() => ({ data: [] })),
        mastersAPI.getOffices().catch(() => ({ data: [] })),
        mastersAPI.getPayLevels().catch(() => ({ data: [] })),
        mastersAPI.getServices().catch(() => ({ data: [] })),
        mastersAPI.getServiceGroups().catch(() => ({ data: [] })),
      ]);
      return {
        departments: unwrapMasterList(deptRes, "departments"),
        employmentTypes: unwrapMasterList(typeRes, "employment_types"),
        designations: unwrapMasterList(desigRes, "designations"),
        offices: unwrapMasterList(officeRes, "offices"),
        payLevels: unwrapMasterList(payRes, "pay_levels"),
        services: unwrapMasterList(svcRes, "services"),
        serviceGroups: unwrapMasterList(grpRes, "service_groups"),
      };
    },
  });

  const departments = referenceQuery.data?.departments ?? EMPTY_LIST;
  const employmentTypes = referenceQuery.data?.employmentTypes ?? EMPTY_LIST;
  const designations = referenceQuery.data?.designations ?? EMPTY_LIST;
  const offices = referenceQuery.data?.offices ?? EMPTY_LIST;
  const payLevels = referenceQuery.data?.payLevels ?? EMPTY_LIST;
  const services = referenceQuery.data?.services ?? EMPTY_LIST;
  const serviceGroups = referenceQuery.data?.serviceGroups ?? EMPTY_LIST;

  // ── Filter setters (URL-backed; changing a filter resets the page) ─
  const setQuery = useCallback((v) => setFilterValue("query", v), [setFilterValue]);
  const setActiveStatusFilter = useCallback((v) => setFilterValue("status", v), [setFilterValue]);
  const setDepartmentFilter = useCallback((v) => setFilterValue("department", v), [setFilterValue]);
  const setTypeFilter = useCallback((v) => setFilterValue("type", v), [setFilterValue]);
  const setDesignationFilter = useCallback((v) => setFilterValue("designation", v), [setFilterValue]);
  const setOfficeFilter = useCallback((v) => setFilterValue("office", v), [setFilterValue]);
  const setEmployeeStatusFilter = useCallback((v) => setFilterValue("employeeStatus", v), [setFilterValue]);
  const setRecruitmentFilter = useCallback((v) => setFilterValue("recruitment", v), [setFilterValue]);
  const setPayLevelFilter = useCallback((v) => setFilterValue("payLevel", v), [setFilterValue]);
  const setServiceFilter = useCallback((v) => setFilterValue("service", v), [setFilterValue]);
  const setGroupFilter = useCallback((v) => setFilterValue("group", v), [setFilterValue]);
  const setDateFromFilter = useCallback((v) => setFilterValue("dateFrom", v), [setFilterValue]);
  const setDateToFilter = useCallback((v) => setFilterValue("dateTo", v), [setFilterValue]);

  // ── Derived data ──────────────────────────────────────────────────
  const statusCounts = useMemo(() => {
    const counts = {};
    employees.forEach((e) => {
      const s = useIdentityDirectory
        ? e?.identity_workflow_status || e?.workflow_status || "DRAFT"
        : e?.profile_workflow_status || e?.workflow_status || "DRAFT";
      counts[s] = (counts[s] || 0) + 1;
    });
    return counts;
  }, [employees, useIdentityDirectory]);

  const departmentOptions = useMemo(() => {
    if (departments.length > 0) {
      return departments
        .map((d) => ({
          value: d.code || d.department_code || d.name,
          label: d.name || d.code || d.department_code,
        }))
        .sort((a, b) => a.label.localeCompare(b.label));
    }
    const set = new Set();
    employees.forEach((e) => {
      const dept = e.current_department_id || e.department_code;
      if (dept) set.add(dept);
    });
    return [...set].sort().map((d) => ({ value: d, label: d }));
  }, [departments, employees]);

  const employmentTypeOptions = useMemo(() => {
    if (employmentTypes.length > 0) {
      return employmentTypes
        .map((t) => ({
          value: t.code || t.employment_type_code || t.name,
          label: t.name || t.label || t.code || t.employment_type_code,
        }))
        .sort((a, b) => a.label.localeCompare(b.label));
    }
    const set = new Set();
    employees.forEach((e) => {
      const t = e.employment_type || e.employment_type_code;
      if (t) set.add(t);
    });
    return [...set].sort().map((t) => ({ value: t, label: t }));
  }, [employmentTypes, employees]);

  const designationOptions = useMemo(() => {
    if (designations.length > 0) {
      return designations
        .map((d) => ({ value: d.code || d.name, label: d.name || d.code }))
        .sort((a, b) => a.label.localeCompare(b.label));
    }
    const set = new Set();
    employees.forEach((e) => { if (e.current_designation_id) set.add(e.current_designation_id); });
    return [...set].sort().map((d) => ({ value: d, label: d }));
  }, [designations, employees]);

  const officeOptions = useMemo(() => {
    if (offices.length > 0) {
      return offices
        .map((o) => ({ value: o.code || o.name, label: o.name || o.code }))
        .sort((a, b) => a.label.localeCompare(b.label));
    }
    const set = new Set();
    employees.forEach((e) => { if (e.current_office_id) set.add(e.current_office_id); });
    return [...set].sort().map((o) => ({ value: o, label: o }));
  }, [offices, employees]);

  const employeeStatusOptions = useMemo(
    () => EMPLOYEE_STATUSES.map((status) => ({ value: status, label: formatDirectoryEnumLabel(status) })),
    [],
  );

  const recruitmentModeOptions = useMemo(
    () => RECRUITMENT_MODES.map((mode) => ({ value: mode, label: formatDirectoryEnumLabel(mode) })),
    [],
  );

  const payLevelOptions = useMemo(() => {
    if (payLevels.length > 0) {
      return payLevels
        .map((p) => ({ value: p.code || p.name, label: p.description || p.name || p.code }))
        .sort((a, b) => a.label.localeCompare(b.label));
    }
    return [];
  }, [payLevels]);

  const serviceOptions = useMemo(() => {
    if (services.length > 0) {
      return services
        .map((s) => ({ value: s.code || s.name, label: s.description || s.name || s.code }))
        .sort((a, b) => a.label.localeCompare(b.label));
    }
    return [];
  }, [services]);

  const serviceGroupOptions = useMemo(() => {
    if (serviceGroups.length > 0) {
      return serviceGroups
        .map((g) => ({ value: g.code || g.name, label: g.description || g.name || g.code }))
        .sort((a, b) => a.label.localeCompare(b.label));
    }
    return [];
  }, [serviceGroups]);

  const activeFilterCount = [
    activeStatusFilter,
    departmentFilter,
    typeFilter,
    designationFilter,
    officeFilter,
    employeeStatusFilter,
    recruitmentFilter,
    payLevelFilter,
    serviceFilter,
    groupFilter,
  ].filter((f) => f !== "ALL").length
    + (dateFromFilter ? 1 : 0)
    + (dateToFilter ? 1 : 0);

  // ── Actions ───────────────────────────────────────────────────────
  const clearAllFilters = clearFilters;

  const { refetch: refetchDirectory } = directoryQuery;
  const refresh = useCallback(() => refetchDirectory(), [refetchDirectory]);

  // ── Pagination helpers ────────────────────────────────────────────
  const currentPage = Math.min(page, totalPages);
  const showingFrom = total > 0 ? (currentPage - 1) * PAGE_SIZE + 1 : 0;
  const showingTo = Math.min(currentPage * PAGE_SIZE, total);

  return {
    // data
    employees,
    total,
    totalPages,
    currentPage,
    showingFrom,
    showingTo,
    PAGE_SIZE,

    // loading state
    loading,
    refreshing,

    // search
    query,
    setQuery,

    // filters
    activeStatusFilter,
    setActiveStatusFilter,
    departmentFilter,
    setDepartmentFilter,
    typeFilter,
    setTypeFilter,
    designationFilter,
    setDesignationFilter,
    officeFilter,
    setOfficeFilter,
    employeeStatusFilter,
    setEmployeeStatusFilter,
    recruitmentFilter,
    setRecruitmentFilter,
    payLevelFilter,
    setPayLevelFilter,
    serviceFilter,
    setServiceFilter,
    groupFilter,
    setGroupFilter,
    dateFromFilter,
    setDateFromFilter,
    dateToFilter,
    setDateToFilter,
    activeFilterCount,
    clearAllFilters,

    // filter options
    statusCounts,
    departmentOptions,
    employmentTypeOptions,
    designationOptions,
    officeOptions,
    employeeStatusOptions,
    recruitmentModeOptions,
    payLevelOptions,
    serviceOptions,
    serviceGroupOptions,

    // sort
    sortField,
    sortDir,
    toggleSort,

    // pagination
    page,
    setPage,

    // actions
    refresh,
    loadEmployees: refresh,
    workflowFilterKind: useIdentityDirectory ? "Identity" : "Profile",
  };
}
