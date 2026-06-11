import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { employeeProfileApi } from "@/contexts/employee_master";
import { formatDirectoryEnumLabel } from "@/contexts/employee_master";
import { mastersAPI } from "@/contexts/masters";
import { toast } from "sonner";

const PAGE_SIZE = 20;

const EMPLOYEE_STATUSES = ["ACTIVE", "RETIRED", "SUSPENDED", "DECEASED"];
const RECRUITMENT_MODES = ["DIRECT", "PROMOTION", "DEPUTATION", "TRANSFER", "COMPASSIONATE"];

const parsePositiveInt = (value, fallback) => {
  const parsed = Number.parseInt(value || "", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
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
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = useMemo(
    () => new URLSearchParams(location.search || ""),
    [location.search],
  );

  // ── URL-synced state ──────────────────────────────────────────────
  const [query, _setQuery] = useState(() => searchParams.get("q") || "");
  const [activeStatusFilter, _setActiveStatusFilter] = useState(
    () => searchParams.get("status") || "ALL",
  );
  const [departmentFilter, _setDepartmentFilter] = useState(
    () => searchParams.get("dept") || "ALL",
  );
  const [typeFilter, _setTypeFilter] = useState(
    () => searchParams.get("type") || "ALL",
  );
  const [designationFilter, _setDesignationFilter] = useState(
    () => searchParams.get("desig") || "ALL",
  );
  const [officeFilter, _setOfficeFilter] = useState(
    () => searchParams.get("office") || "ALL",
  );
  const [employeeStatusFilter, _setEmployeeStatusFilter] = useState(
    () => searchParams.get("emp_status") || "ALL",
  );
  const [recruitmentFilter, _setRecruitmentFilter] = useState(
    () => searchParams.get("recruit") || "ALL",
  );
  const [payLevelFilter, _setPayLevelFilter] = useState(
    () => searchParams.get("pay") || "ALL",
  );
  const [serviceFilter, _setServiceFilter] = useState(
    () => searchParams.get("svc") || "ALL",
  );
  const [groupFilter, _setGroupFilter] = useState(
    () => searchParams.get("grp") || "ALL",
  );
  const [dateFromFilter, _setDateFromFilter] = useState(
    () => searchParams.get("date_from") || "",
  );
  const [dateToFilter, _setDateToFilter] = useState(
    () => searchParams.get("date_to") || "",
  );
  const [sortField, setSortField] = useState(
    () => searchParams.get("sort") || "full_name",
  );
  const [sortDir, setSortDir] = useState(
    () => searchParams.get("dir") || "asc",
  );
  const [page, setPage] = useState(() =>
    parsePositiveInt(searchParams.get("page"), 1),
  );

  // ── Loading / data state ──────────────────────────────────────────
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // ── Reference data ────────────────────────────────────────────────
  const [departments, setDepartments] = useState([]);
  const [employmentTypes, setEmploymentTypes] = useState([]);
  const [designations, setDesignations] = useState([]);
  const [offices, setOffices] = useState([]);
  const [payLevels, setPayLevels] = useState([]);
  const [services, setServices] = useState([]);
  const [serviceGroups, setServiceGroups] = useState([]);

  // ── Debounced search ──────────────────────────────────────────────
  const [debouncedQuery, setDebouncedQuery] = useState(query);
  const debounceRef = useRef(null);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(debounceRef.current);
  }, [query]);

  // ── Fetch employees from server ───────────────────────────────────
  const fetchEmployees = useCallback(
    async ({ mode = "initial" } = {}) => {
      if (mode === "initial") setLoading(true);
      else setRefreshing(true);

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
        setEmployees(Array.isArray(rows) ? rows.map((row) => normalizeDirectoryEmployee(row, rowSource)) : []);
        setTotal(data.total ?? rows.length);
        setTotalPages(data.total_pages ?? Math.max(1, Math.ceil((data.total ?? rows.length) / PAGE_SIZE)));
      } catch (error) {
        console.error("Failed to load employees:", error);
        toast.error("Failed to load employee directory");
        setEmployees([]);
        setTotal(0);
        setTotalPages(1);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [debouncedQuery, activeStatusFilter, departmentFilter, typeFilter, designationFilter, officeFilter, employeeStatusFilter, recruitmentFilter, payLevelFilter, serviceFilter, groupFilter, dateFromFilter, dateToFilter, sortField, sortDir, page, useUserDirectory, listUserDirectory, useIdentityDirectory, listIdentityDirectory],
  );

  useEffect(() => {
    fetchEmployees({ mode: "initial" });
  }, [fetchEmployees]);

  // ── Load reference data once ──────────────────────────────────────
  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const [deptRes, typeRes, desigRes, officeRes, payRes, svcRes, grpRes] = await Promise.all([
          mastersAPI.getDepartments().catch(() => ({ data: [] })),
          mastersAPI.getEmploymentTypes().catch(() => ({ data: [] })),
          mastersAPI.getDesignations().catch(() => ({ data: [] })),
          mastersAPI.getOffices().catch(() => ({ data: [] })),
          mastersAPI.getPayLevels().catch(() => ({ data: [] })),
          mastersAPI.getServices().catch(() => ({ data: [] })),
          mastersAPI.getServiceGroups().catch(() => ({ data: [] })),
        ]);
        if (!active) return;
        const depts = Array.isArray(deptRes.data)
          ? deptRes.data
          : deptRes.data?.departments || [];
        const types = Array.isArray(typeRes.data)
          ? typeRes.data
          : typeRes.data?.employment_types || [];
        const desigs = Array.isArray(desigRes.data)
          ? desigRes.data
          : desigRes.data?.designations || [];
        const offs = Array.isArray(officeRes.data)
          ? officeRes.data
          : officeRes.data?.offices || [];
        const pays = Array.isArray(payRes.data)
          ? payRes.data
          : payRes.data?.pay_levels || [];
        const svcs = Array.isArray(svcRes.data)
          ? svcRes.data
          : svcRes.data?.services || [];
        const grps = Array.isArray(grpRes.data)
          ? grpRes.data
          : grpRes.data?.service_groups || [];
        setDepartments(depts);
        setEmploymentTypes(types);
        setDesignations(desigs);
        setOffices(offs);
        setPayLevels(pays);
        setServices(svcs);
        setServiceGroups(grps);
      } catch {
        /* filter dropdowns will fall back to empty */
      }
    };
    load();
    return () => {
      active = false;
    };
  }, []);

  // ── URL sync ──────────────────────────────────────────────────────
  useEffect(() => {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (activeStatusFilter !== "ALL") params.set("status", activeStatusFilter);
    if (departmentFilter !== "ALL") params.set("dept", departmentFilter);
    if (typeFilter !== "ALL") params.set("type", typeFilter);
    if (designationFilter !== "ALL") params.set("desig", designationFilter);
    if (officeFilter !== "ALL") params.set("office", officeFilter);
    if (employeeStatusFilter !== "ALL") params.set("emp_status", employeeStatusFilter);
    if (recruitmentFilter !== "ALL") params.set("recruit", recruitmentFilter);
    if (payLevelFilter !== "ALL") params.set("pay", payLevelFilter);
    if (serviceFilter !== "ALL") params.set("svc", serviceFilter);
    if (groupFilter !== "ALL") params.set("grp", groupFilter);
    if (dateFromFilter) params.set("date_from", dateFromFilter);
    if (dateToFilter) params.set("date_to", dateToFilter);
    if (sortField !== "full_name") params.set("sort", sortField);
    if (sortDir !== "asc") params.set("dir", sortDir);
    if (page > 1) params.set("page", String(page));

    const nextSearch = params.toString();
    const normalizedCurrent = (location.search || "").replace(/^\?/, "");
    if (nextSearch === normalizedCurrent) return;

    navigate(
      { pathname: location.pathname, search: nextSearch ? `?${nextSearch}` : "" },
      { replace: true },
    );
  }, [activeStatusFilter, departmentFilter, typeFilter, designationFilter, officeFilter, employeeStatusFilter, recruitmentFilter, payLevelFilter, serviceFilter, groupFilter, dateFromFilter, dateToFilter, location.pathname, location.search, navigate, page, query, sortDir, sortField]);

  // ── Filter setters that auto-reset to page 1 ─────────────────────
  const setQuery = useCallback((v) => { _setQuery(v); }, []);
  const setActiveStatusFilter = useCallback((v) => { _setActiveStatusFilter(v); setPage(1); }, []);
  const setDepartmentFilter = useCallback((v) => { _setDepartmentFilter(v); setPage(1); }, []);
  const setTypeFilter = useCallback((v) => { _setTypeFilter(v); setPage(1); }, []);
  const setDesignationFilter = useCallback((v) => { _setDesignationFilter(v); setPage(1); }, []);
  const setOfficeFilter = useCallback((v) => { _setOfficeFilter(v); setPage(1); }, []);
  const setEmployeeStatusFilter = useCallback((v) => { _setEmployeeStatusFilter(v); setPage(1); }, []);
  const setRecruitmentFilter = useCallback((v) => { _setRecruitmentFilter(v); setPage(1); }, []);
  const setPayLevelFilter = useCallback((v) => { _setPayLevelFilter(v); setPage(1); }, []);
  const setServiceFilter = useCallback((v) => { _setServiceFilter(v); setPage(1); }, []);
  const setGroupFilter = useCallback((v) => { _setGroupFilter(v); setPage(1); }, []);
  const setDateFromFilter = useCallback((v) => { _setDateFromFilter(v); setPage(1); }, []);
  const setDateToFilter = useCallback((v) => { _setDateToFilter(v); setPage(1); }, []);

  // Reset page when debounced search changes (but not on mount)
  const prevDebouncedQuery = useRef(debouncedQuery);
  useEffect(() => {
    if (prevDebouncedQuery.current !== debouncedQuery) {
      prevDebouncedQuery.current = debouncedQuery;
      setPage(1);
    }
  }, [debouncedQuery]);

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
  const clearAllFilters = useCallback(() => {
    setActiveStatusFilter("ALL");
    setDepartmentFilter("ALL");
    setTypeFilter("ALL");
    setDesignationFilter("ALL");
    setOfficeFilter("ALL");
    setEmployeeStatusFilter("ALL");
    setRecruitmentFilter("ALL");
    setPayLevelFilter("ALL");
    setServiceFilter("ALL");
    setGroupFilter("ALL");
    setDateFromFilter("");
    setDateToFilter("");
    setQuery("");
  }, [setActiveStatusFilter, setDepartmentFilter, setTypeFilter, setDesignationFilter, setOfficeFilter, setEmployeeStatusFilter, setRecruitmentFilter, setPayLevelFilter, setServiceFilter, setGroupFilter, setDateFromFilter, setDateToFilter, setQuery]);

  const toggleSort = useCallback(
    (field) => {
      if (sortField === field) {
        setSortDir((d) => (d === "asc" ? "desc" : "asc"));
      } else {
        setSortField(field);
        setSortDir("asc");
      }
      setPage(1);
    },
    [sortField],
  );

  const refresh = useCallback(
    () => fetchEmployees({ mode: "refresh" }),
    [fetchEmployees],
  );

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
    loadEmployees: fetchEmployees,
    workflowFilterKind: useIdentityDirectory ? "Identity" : "Profile",
  };
}
