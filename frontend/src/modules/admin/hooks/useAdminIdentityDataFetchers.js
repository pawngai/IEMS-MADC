import { useCallback } from "react";
import { userManagementAPI } from "@/modules/identity_access";
import { normalizeAuthorityList } from "@/modules/admin/hooks/authorityNormalization";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/shared/lib/utils";

const useAdminIdentityDataFetchers = ({
  setUsers,
  setAvailableAuthorities,
  setAuthorityHolders,
  employeePagination,
  debouncedEmployeeSearch,
  employeeFilters,
  setEmployees,
  setEmployeePagination,
  setRoleChangeHistory,
  setRoleChangeStats,
}) => {
  const fetchDashboardData = useCallback(async () => {
    try {
      const [usersRes, authRes, holdersRes] = await Promise.all([
        userManagementAPI.list({ limit: 100 }).catch(() => ({ data: [] })),
        userManagementAPI.getAuthorities().catch(() => ({ data: { authorities: [] } })),
        userManagementAPI.getAuthorityHolders().catch(() => ({ data: { holders: {} } })),
      ]);

      const usersList = Array.isArray(usersRes.data) ? usersRes.data : (usersRes.data?.users || []);
      setUsers(usersList);
      setAvailableAuthorities(normalizeAuthorityList(authRes.data?.authorities || []));
      setAuthorityHolders(holdersRes.data?.holders || {});
    } catch (error) {
      console.error("Failed to fetch admin access data:", error);
      toast.error(getApiErrorMessage(error, "Failed to load admin access data"));
    }
  }, [setUsers, setAvailableAuthorities, setAuthorityHolders]);

  const fetchEmployeeData = useCallback(async () => {
    try {
      const res = await userManagementAPI.getEmployees({
        limit: employeePagination.limit,
        offset: employeePagination.offset,
        search: debouncedEmployeeSearch || undefined,
        department: employeeFilters.department || undefined,
        employment_type: employeeFilters.employment_type || undefined,
        workflow_status: employeeFilters.workflow_status || undefined,
      });
      setEmployees(res.data?.employees || []);
      setEmployeePagination((prev) => ({ ...prev, total: res.data?.total || 0 }));
    } catch (error) {
      console.error("Failed to fetch employees:", error);
      toast.error(getApiErrorMessage(error, "Failed to load employee identity data"));
    }
  }, [employeePagination.limit, employeePagination.offset, debouncedEmployeeSearch, employeeFilters, setEmployees, setEmployeePagination]);

  const fetchRoleChangeData = useCallback(async () => {
    try {
      const [historyRes, statsRes] = await Promise.all([
        userManagementAPI.getRoleChangeHistory({ limit: 20 }),
        userManagementAPI.getRoleChangeStats(),
      ]);

      const historyPayload = historyRes.data || {};
      const historyItems = historyPayload.changes || historyPayload.history || [];
      setRoleChangeHistory(Array.isArray(historyItems) ? historyItems : []);

      const statsPayload = statsRes.data || {};
      const groupedStats = Array.isArray(statsPayload.stats) ? statsPayload.stats : [];
      const computedTotal = groupedStats.reduce((total, item) => total + Number(item?.count || 0), 0);
      setRoleChangeStats({
        total_changes: Number(statsPayload.total_changes ?? computedTotal),
        changes_last_7_days: Number(statsPayload.changes_last_7_days ?? computedTotal),
      });
    } catch (error) {
      console.error("Failed to fetch role change data:", error);
      toast.error(getApiErrorMessage(error, "Failed to load role change data"));
    }
  }, [setRoleChangeHistory, setRoleChangeStats]);

  return {
    fetchDashboardData,
    fetchEmployeeData,
    fetchRoleChangeData,
  };
};

export default useAdminIdentityDataFetchers;
