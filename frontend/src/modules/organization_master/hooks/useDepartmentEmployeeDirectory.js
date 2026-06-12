import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { departmentPortalAPI } from "@/modules/organization_master/api/departmentApi";
import { mastersAPI } from "@/modules/organization_master";

const PAGE_SIZE = 20;

const EMPLOYEE_STATUSES = ["ACTIVE", "RETIRED", "SUSPENDED", "DECEASED"];
const RECRUITMENT_MODES = ["DIRECT", "PROMOTION", "DEPUTATION", "TRANSFER", "COMPASSIONATE"];

const parsePositiveInt = (value, fallback) => {
  const parsed = Number.parseInt(value || "", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
};

const parseDirectorySearch = (search = "") => {
  const params = new URLSearchParams(search || "");
  return {
    query: params.get("q") || "",
    activeStatusFilter: params.get("status") || "ALL",
    typeFilter: params.get("type") || "ALL",
    designationFilter: params.get("desig") || "ALL",
    officeFilter: params.get("office") || "ALL",
    employeeStatusFilter: params.get("emp_status") || "ALL",
    recruitmentFilter: params.get("recruit") || "ALL",
    payLevelFilter: params.get("pay") || "ALL",
    serviceFilter: params.get("svc") || "ALL",
    groupFilter: params.get("grp") || "ALL",
    dateFromFilter: params.get("date_from") || "",
    dateToFilter: params.get("date_to") || "",
    sortField: params.get("sort") || "full_name",
    sortDir: params.get("dir") || "asc",
    page: parsePositiveInt(params.get("page"), 1),
  };
};

const buildSearchParams = (state) => {
  const params = new URLSearchParams();
  if (state.query) params.set("q", state.query);
  if (state.activeStatusFilter !== "ALL") params.set("status", state.activeStatusFilter);
  if (state.typeFilter !== "ALL") params.set("type", state.typeFilter);
  if (state.designationFilter !== "ALL") params.set("desig", state.designationFilter);
  if (state.officeFilter !== "ALL") params.set("office", state.officeFilter);
  if (state.employeeStatusFilter !== "ALL") params.set("emp_status", state.employeeStatusFilter);
  if (state.recruitmentFilter !== "ALL") params.set("recruit", state.recruitmentFilter);
  if (state.payLevelFilter !== "ALL") params.set("pay", state.payLevelFilter);
  if (state.serviceFilter !== "ALL") params.set("svc", state.serviceFilter);
  if (state.groupFilter !== "ALL") params.set("grp", state.groupFilter);
  if (state.dateFromFilter) params.set("date_from", state.dateFromFilter);
  if (state.dateToFilter) params.set("date_to", state.dateToFilter);
  if (state.sortField !== "full_name") params.set("sort", state.sortField);
  if (state.sortDir !== "asc") params.set("dir", state.sortDir);
  if (state.page > 1) params.set("page", String(state.page));
  return params.toString();
};

const shallowStateEqual = (left, right) =>
  left.query === right.query
  && left.activeStatusFilter === right.activeStatusFilter
  && left.typeFilter === right.typeFilter
  && left.designationFilter === right.designationFilter
  && left.officeFilter === right.officeFilter
  && left.employeeStatusFilter === right.employeeStatusFilter
  && left.recruitmentFilter === right.recruitmentFilter
  && left.payLevelFilter === right.payLevelFilter
  && left.serviceFilter === right.serviceFilter
  && left.groupFilter === right.groupFilter
  && left.dateFromFilter === right.dateFromFilter
  && left.dateToFilter === right.dateToFilter
  && left.sortField === right.sortField
  && left.sortDir === right.sortDir
  && left.page === right.page;

const toSortedOptions = (items, valueKeys, labelKeys) =>
  (items || [])
    .map((item) => {
      const value = valueKeys.map((key) => item?.[key]).find(Boolean);
      const label = labelKeys.map((key) => item?.[key]).find(Boolean) || value;
      if (!value || !label) return null;
      return { value, label };
    })
    .filter(Boolean)
    .sort((left, right) => left.label.localeCompare(right.label));

export function useDepartmentEmployeeDirectory({ enabled }) {
  const navigate = useNavigate();
  const location = useLocation();

  const [directoryState, setDirectoryState] = useState(() => parseDirectorySearch(location.search));
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [employmentTypes, setEmploymentTypes] = useState([]);
  const [designations, setDesignations] = useState([]);
  const [offices, setOffices] = useState([]);
  const [payLevels, setPayLevels] = useState([]);
  const [services, setServices] = useState([]);
  const [serviceGroups, setServiceGroups] = useState([]);
  const [debouncedQuery, setDebouncedQuery] = useState(directoryState.query);
  const debounceRef = useRef(null);

  useEffect(() => {
    const nextState = parseDirectorySearch(location.search);
    setDirectoryState((currentState) => (
      shallowStateEqual(currentState, nextState) ? currentState : nextState
    ));
  }, [location.search]);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedQuery(directoryState.query), 300);
    return () => clearTimeout(debounceRef.current);
  }, [directoryState.query]);

  useEffect(() => {
    const nextSearch = buildSearchParams(directoryState);
    const currentSearch = (location.search || "").replace(/^\?/, "");
    if (nextSearch === currentSearch) return;
    navigate(
      {
        pathname: location.pathname,
        search: nextSearch ? `?${nextSearch}` : "",
      },
      { replace: true },
    );
  }, [directoryState, location.pathname, location.search, navigate]);

  const fetchEmployees = useCallback(async ({ mode = "initial" } = {}) => {
    if (!enabled) {
      setEmployees([]);
      setTotal(0);
      setTotalPages(1);
      setLoading(false);
      setRefreshing(false);
      return;
    }

    if (mode === "initial") setLoading(true);
    else setRefreshing(true);

    const params = {
      page: directoryState.page,
      page_size: PAGE_SIZE,
      sort_by: directoryState.sortField || undefined,
      sort_dir: directoryState.sortDir || undefined,
    };
    const trimmedQuery = debouncedQuery.trim();
    if (trimmedQuery) params.q = trimmedQuery;
    if (directoryState.activeStatusFilter !== "ALL") params.workflow_status = directoryState.activeStatusFilter;
    if (directoryState.typeFilter !== "ALL") params.employment_type = directoryState.typeFilter;
    if (directoryState.designationFilter !== "ALL") params.designation_id = directoryState.designationFilter;
    if (directoryState.officeFilter !== "ALL") params.office_id = directoryState.officeFilter;
    if (directoryState.employeeStatusFilter !== "ALL") params.employee_status = directoryState.employeeStatusFilter;
    if (directoryState.recruitmentFilter !== "ALL") params.recruitment_mode = directoryState.recruitmentFilter;
    if (directoryState.payLevelFilter !== "ALL") params.pay_level = directoryState.payLevelFilter;
    if (directoryState.serviceFilter !== "ALL") params.service = directoryState.serviceFilter;
    if (directoryState.groupFilter !== "ALL") params.service_group = directoryState.groupFilter;
    if (directoryState.dateFromFilter) params.date_from = directoryState.dateFromFilter;
    if (directoryState.dateToFilter) params.date_to = directoryState.dateToFilter;

    try {
      const response = await departmentPortalAPI.getEmployees(params);
      const data = response.data || {};
      const rows = Array.isArray(data.employees) ? data.employees : [];
      const nextTotal = Number(data.total || 0);
      setEmployees(rows);
      setTotal(nextTotal);
      setTotalPages(Number(data.total_pages || Math.max(1, Math.ceil(nextTotal / PAGE_SIZE))));
    } catch (error) {
      console.error("Failed to load department employees:", error);
      toast.error("Failed to load employees");
      setEmployees([]);
      setTotal(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [debouncedQuery, directoryState, enabled]);

  useEffect(() => {
    fetchEmployees({ mode: "initial" });
  }, [fetchEmployees]);

  useEffect(() => {
    let active = true;
    const loadReferenceData = async () => {
      try {
        const [
          employmentTypeResponse,
          designationResponse,
          officeResponse,
          payLevelResponse,
          serviceResponse,
          serviceGroupResponse,
        ] = await Promise.all([
          mastersAPI.getEmploymentTypes().catch(() => ({ data: [] })),
          mastersAPI.getDesignations().catch(() => ({ data: [] })),
          mastersAPI.getOffices().catch(() => ({ data: [] })),
          mastersAPI.getPayLevels().catch(() => ({ data: [] })),
          mastersAPI.getServices().catch(() => ({ data: [] })),
          mastersAPI.getServiceGroups().catch(() => ({ data: [] })),
        ]);
        if (!active) return;

        setEmploymentTypes(toSortedOptions(employmentTypeResponse.data, ["code", "employment_type_code", "name"], ["name", "label", "code", "employment_type_code"]));
        setDesignations(toSortedOptions(designationResponse.data, ["code", "name"], ["name", "code"]));
        setOffices(toSortedOptions(officeResponse.data, ["code", "name"], ["name", "code"]));
        setPayLevels(toSortedOptions(payLevelResponse.data, ["code", "name"], ["description", "name", "code"]));
        setServices(toSortedOptions(serviceResponse.data, ["code", "name"], ["description", "name", "code"]));
        setServiceGroups(toSortedOptions(serviceGroupResponse.data, ["code", "name"], ["description", "name", "code"]));
      } catch {
        // Empty reference-data lists are acceptable for the directory.
      }
    };

    loadReferenceData();
    return () => {
      active = false;
    };
  }, []);

  const updateDirectoryState = useCallback((updater) => {
    setDirectoryState((currentState) => {
      const nextState = typeof updater === "function"
        ? updater(currentState)
        : { ...currentState, ...updater };
      return shallowStateEqual(currentState, nextState) ? currentState : nextState;
    });
  }, []);

  const setQuery = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, query: value, page: 1 }));
  }, [updateDirectoryState]);

  const setActiveStatusFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, activeStatusFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setTypeFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, typeFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setDesignationFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, designationFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setOfficeFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, officeFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setEmployeeStatusFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, employeeStatusFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setRecruitmentFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, recruitmentFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setPayLevelFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, payLevelFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setServiceFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, serviceFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setGroupFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, groupFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setDateFromFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, dateFromFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setDateToFilter = useCallback((value) => {
    updateDirectoryState((currentState) => ({ ...currentState, dateToFilter: value, page: 1 }));
  }, [updateDirectoryState]);

  const setPage = useCallback((valueOrUpdater) => {
    updateDirectoryState((currentState) => {
      const nextPage = typeof valueOrUpdater === "function"
        ? valueOrUpdater(currentState.page)
        : valueOrUpdater;
      return {
        ...currentState,
        page: Math.max(1, Number(nextPage) || 1),
      };
    });
  }, [updateDirectoryState]);

  const clearAllFilters = useCallback(() => {
    updateDirectoryState((currentState) => ({
      ...currentState,
      query: "",
      activeStatusFilter: "ALL",
      typeFilter: "ALL",
      designationFilter: "ALL",
      officeFilter: "ALL",
      employeeStatusFilter: "ALL",
      recruitmentFilter: "ALL",
      payLevelFilter: "ALL",
      serviceFilter: "ALL",
      groupFilter: "ALL",
      dateFromFilter: "",
      dateToFilter: "",
      page: 1,
    }));
  }, [updateDirectoryState]);

  const toggleSort = useCallback((field) => {
    updateDirectoryState((currentState) => ({
      ...currentState,
      sortField: currentState.sortField === field ? field : field,
      sortDir: currentState.sortField === field && currentState.sortDir === "asc" ? "desc" : "asc",
      page: 1,
    }));
  }, [updateDirectoryState]);

  const refresh = useCallback(() => fetchEmployees({ mode: "refresh" }), [fetchEmployees]);

  const statusCounts = useMemo(() => {
    const counts = {};
    employees.forEach((employee) => {
      const workflowStatus = employee?.workflow_status || "DRAFT";
      counts[workflowStatus] = (counts[workflowStatus] || 0) + 1;
    });
    return counts;
  }, [employees]);

  const activeFilterCount = [
    directoryState.activeStatusFilter,
    directoryState.typeFilter,
    directoryState.designationFilter,
    directoryState.officeFilter,
    directoryState.employeeStatusFilter,
    directoryState.recruitmentFilter,
    directoryState.payLevelFilter,
    directoryState.serviceFilter,
    directoryState.groupFilter,
  ].filter((value) => value !== "ALL").length
    + (directoryState.dateFromFilter ? 1 : 0)
    + (directoryState.dateToFilter ? 1 : 0);

  const currentPage = Math.min(directoryState.page, totalPages);
  const showingFrom = total > 0 ? (currentPage - 1) * PAGE_SIZE + 1 : 0;
  const showingTo = Math.min(currentPage * PAGE_SIZE, total);

  return {
    employees,
    total,
    totalPages,
    currentPage,
    showingFrom,
    showingTo,
    PAGE_SIZE,
    loading,
    refreshing,
    query: directoryState.query,
    setQuery,
    activeStatusFilter: directoryState.activeStatusFilter,
    setActiveStatusFilter,
    typeFilter: directoryState.typeFilter,
    setTypeFilter,
    designationFilter: directoryState.designationFilter,
    setDesignationFilter,
    officeFilter: directoryState.officeFilter,
    setOfficeFilter,
    employeeStatusFilter: directoryState.employeeStatusFilter,
    setEmployeeStatusFilter,
    recruitmentFilter: directoryState.recruitmentFilter,
    setRecruitmentFilter,
    payLevelFilter: directoryState.payLevelFilter,
    setPayLevelFilter,
    serviceFilter: directoryState.serviceFilter,
    setServiceFilter,
    groupFilter: directoryState.groupFilter,
    setGroupFilter,
    dateFromFilter: directoryState.dateFromFilter,
    setDateFromFilter,
    dateToFilter: directoryState.dateToFilter,
    setDateToFilter,
    sortField: directoryState.sortField,
    sortDir: directoryState.sortDir,
    toggleSort,
    page: directoryState.page,
    setPage,
    employmentTypeOptions: employmentTypes,
    designationOptions: designations,
    officeOptions: offices,
    employeeStatusOptions: EMPLOYEE_STATUSES.map((value) => ({ value, label: value })),
    recruitmentModeOptions: RECRUITMENT_MODES.map((value) => ({ value, label: value })),
    payLevelOptions: payLevels,
    serviceOptions: services,
    serviceGroupOptions: serviceGroups,
    statusCounts,
    activeFilterCount,
    clearAllFilters,
    refresh,
  };
}