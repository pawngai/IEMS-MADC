import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/modules/identity_access";
import { usePermissions } from "@/modules/identity_access";
import {
  DEPARTMENT_SCOPED_AUTHORITIES,
  hasAnyAuthority,
  hasAuthority,
} from "@/platform/permissions";
import { authAPI } from "@/modules/identity_access";
import { mastersAPI } from "@/modules/organization_master";
import { Permissions } from "@/platform/permissions";
import { setTokens } from "@/platform/api/httpClient";
import { toast } from "sonner";

/**
 * Normalize raw department rows from master API into { code, name } objects.
 */
export const normalizeDepartmentRows = (rows) =>
  (Array.isArray(rows) ? rows : [])
    .map((row) => {
      const code = String(row?.code || "").trim().toUpperCase();
      const name = String(row?.name || code || "").trim();
      return { code, name };
    })
    .filter((row) => row.code);

/**
 * Shared hook for department portal scope resolution.
 *
 * Handles permission checks, loading departments, resolving the user's
 * preferred department, computing the display label, and persisting it
 * to localStorage.
 */
export function useDepartmentScope() {
  const { user } = useAuth();
  const { can, canAccessModule } = usePermissions();

  const canUseDepartmentPortal =
    hasAnyAuthority(user, DEPARTMENT_SCOPED_AUTHORITIES) &&
    can(Permissions.PROFILE_READ_ALL);

  const canRecommend = can(Permissions.LEAVE_RECOMMEND);
  const canSanction = can(Permissions.LEAVE_SANCTION);
  const canLeaveWorkflow = (canRecommend || canSanction) && canAccessModule("leave");

  const isDataEntry = hasAuthority(user, "DEPT_DATA_ENTRY");
  const canCreateProfile = isDataEntry && can(Permissions.PROFILE_CREATE);
  const canManageSanctionedStrength = can(Permissions.PROFILE_UPDATE_ALL);

  const [loading, setLoading] = useState(true);
  const [departments, setDepartments] = useState([]);
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [scopeError, setScopeError] = useState("");

  const loadDepartments = useCallback(async () => {
    setLoading(true);
    try {
      const deptRes = await mastersAPI.getDepartments().catch(() => ({ data: [] }));

      const deptRows = normalizeDepartmentRows(deptRes.data);
      let preferredDepartment = String(user?.department_code || "").trim().toUpperCase();

      if (!preferredDepartment) {
        try {
          const meRes = await authAPI.getMe();
          const freshUser = meRes.data;
          if (freshUser?.department_code) {
            preferredDepartment = String(freshUser.department_code).trim().toUpperCase();
            setTokens({ user: { ...user, department_code: freshUser.department_code } });
          }
        } catch { /* ignore */ }
      }

      if (!preferredDepartment) {
        setScopeError("Department is not mapped for this user. Contact admin to assign a department.");
        setDepartments([]);
        setSelectedDepartment("");
        return;
      }

      const scopedDepartments = deptRows.filter((dept) => dept.code === preferredDepartment);
      const nextDepartments = scopedDepartments.length > 0
        ? scopedDepartments
        : [{ code: preferredDepartment, name: preferredDepartment }];

      setScopeError("");
      setDepartments(nextDepartments);
      setSelectedDepartment((current) => current === preferredDepartment ? current : preferredDepartment);
    } catch (error) {
      console.error("Failed to load departments:", error);
      toast.error("Failed to load departments");
      setScopeError("Unable to resolve department access right now.");
      setDepartments([]);
      setSelectedDepartment("");
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Auto-load departments on mount when user has portal access
  useEffect(() => {
    if (canUseDepartmentPortal) loadDepartments();
    else setLoading(false);
  }, [canUseDepartmentPortal, loadDepartments]);

  const selectedDepartmentLabel = useMemo(() => {
    if (!selectedDepartment) return "Department";
    const match = departments.find((d) => d.code === selectedDepartment);
    if (!match) return selectedDepartment;
    const cleanName = String(match.name || "").trim();
    return cleanName || selectedDepartment;
  }, [departments, selectedDepartment]);

  // Persist label to localStorage for sibling pages
  useEffect(() => {
    if (!selectedDepartment) return;
    try { localStorage.setItem("iems_department_label", selectedDepartmentLabel); } catch { /* ignore */ }
  }, [selectedDepartment, selectedDepartmentLabel]);

  return {
    user,
    loading, setLoading,
    departments,
    selectedDepartment,
    scopeError,
    selectedDepartmentLabel,
    canUseDepartmentPortal,
    canLeaveWorkflow,
    isDataEntry,
    canCreateProfile,
    canManageSanctionedStrength,
  };
}
