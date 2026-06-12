import { useCallback, useMemo, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useEmployeeDirectory } from "@/modules/employee_master/hooks/useEmployeeDirectory";
import { employeeIdentityApi } from "@/modules/employee_master/api/employeeIdentityApi";
import { userManagementAPI } from "@/modules/identity_access";
import { Permissions } from "@/platform/permissions";
import { usePermissions } from "@/modules/identity_access";
import { buildIdentityCreatePath } from "@/shared/lib/employeeEditorRoutes";
import { cn, getApiErrorMessage } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import { toast } from "sonner";
import {
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  UserPlus,
} from "lucide-react";
import {
  STATUS_STYLES,
  buildLabelMap,
  getReadableEnumLabel,
  loadSavedColumns,
  toTitleCase,
} from "@/modules/employee_master/pages/EmployeeDirectoryPage.support";
import EmployeeDirectoryFilters from "@/modules/employee_master/pages/EmployeeDirectoryFilters";
import EmployeeDirectoryTable from "@/modules/employee_master/pages/EmployeeDirectoryTable";
const EmployeeDirectoryPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { can, canAny, getPrimaryAuthority, isAny } = usePermissions();
  const primaryAuthority = getPrimaryAuthority();
  const useIdentityDirectory = ["GLOBAL_DATA_ENTRY", "VERIFIER", "APPROVING_AUTHORITY"].includes(primaryAuthority);
  const useUserDirectory = primaryAuthority === "SYSTEM_ADMIN";

  // ── Hook: all directory data, filtering, pagination, sorting ──────
  const dir = useEmployeeDirectory({
    useUserDirectory,
    listUserDirectory: userManagementAPI.getEmployees,
    useIdentityDirectory,
    listIdentityDirectory: employeeIdentityApi.list,
  });
  const labelMaps = useMemo(() => ({
    department: buildLabelMap(dir.departmentOptions),
    designation: buildLabelMap(dir.designationOptions),
    office: buildLabelMap(dir.officeOptions),
    employmentType: buildLabelMap(dir.employmentTypeOptions),
    employeeStatus: buildLabelMap(
      dir.employeeStatusOptions.map((option) => ({
        ...option,
        label: toTitleCase(option.label || option.value),
      })),
    ),
    workflowStatus: new Map(Object.keys(STATUS_STYLES).map((status) => [status, toTitleCase(status)])),
  }), [
    dir.departmentOptions,
    dir.designationOptions,
    dir.officeOptions,
    dir.employmentTypeOptions,
    dir.employeeStatusOptions,
  ]);
  const getWorkflowStatusLabel = (status) => getReadableEnumLabel([status], labelMaps.workflowStatus);
  const getEmployeeStatusLabel = (status) => getReadableEnumLabel([status], labelMaps.employeeStatus);

  // ── Local UI state ────────────────────────────────────────────────
  const [actionLoading, setActionLoading] = useState("");
  const [showFilters, setShowFilters] = useState(() => {
    const sp = new URLSearchParams(location.search);
    return !!(sp.get("dept") || sp.get("type") || sp.get("desig") || sp.get("office") || sp.get("emp_status") || sp.get("recruit") || sp.get("pay") || sp.get("svc") || sp.get("grp") || sp.get("date_from") || sp.get("date_to"));
  });
  const [visibleColumns, setVisibleColumns] = useState(loadSavedColumns);
  const tableRef = useRef(null);
  const currentDirectoryPath = `${location.pathname}${location.search || ""}`;

  // Detect if we're inside the /portal/* route group
  const isPortalPath = location.pathname.startsWith("/portal");

  const canSeeEmployees =
    canAny([
      Permissions.PROFILE_READ_ALL,
      Permissions.PROFILE_CREATE,
      Permissions.PROFILE_UPDATE_ALL,
      Permissions.PROFILE_UPDATE_OWN_LIMITED,
      Permissions.AUDIT_READ_ALL,
    ]);

  const canCreateEmployee =
    isAny(["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"]) &&
    can(Permissions.PROFILE_CREATE);

  const canManageEmployeeAccounts = isAny(["SYSTEM_ADMIN", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"]);

  const resolveProvisioningEmail = useCallback((employee) => (
    employee?.official_email ||
    employee?.email_official ||
    employee?.email_personal ||
    employee?.personal_email ||
    employee?.contact?.email_official ||
    employee?.contact?.email_personal ||
    ""
  ), []);

  const canProvisionEmployeeAccount = useCallback((employee) => {
    const identityWorkflowStatus = String(employee?.identity_workflow_status || employee?.workflow_status || "").trim().toUpperCase();
    return identityWorkflowStatus === "ACTIVE";
  }, []);

  const getProvisioningAvailability = useCallback((employee) => {
    if (employee?.has_login_account) {
      return {
        canProvision: false,
        label: "Login ready",
        reason: employee?.account_email || "Employee account already exists",
      };
    }

    if (!canProvisionEmployeeAccount(employee)) {
      return {
        canProvision: false,
        label: "Awaiting approval",
        reason: "Login available after identity activation",
      };
    }

    if (!resolveProvisioningEmail(employee)) {
      return {
        canProvision: false,
        label: "Email required",
        reason: "Add an account email first",
      };
    }

    return {
      canProvision: true,
      label: "Provision login",
      reason: "Create or link an employee login",
    };
  }, [canProvisionEmployeeAccount, resolveProvisioningEmail]);

  const handleProvisionAccount = useCallback(
    async (employee) => {
      const employeeId = employee?.employee_id;
      const email = resolveProvisioningEmail(employee);

      if (!employeeId) return;
      if (!canManageEmployeeAccounts) {
        toast.error("Only System Admin, Global Data Entry, or Dealing Assistant can provision login accounts");
        return;
      }
      if (!canProvisionEmployeeAccount(employee)) {
        toast.error("Login account provisioning is available only after the employee identity is active");
        return;
      }
      if (!email) {
        toast.error("Add an account email in the employee profile before provisioning a login account");
        return;
      }

      setActionLoading(`provision-${employeeId}`);
      try {
        const res = await userManagementAPI.provisionEmployeeAccount({
          employee_id: employeeId,
          email,
        });
        if (res.data?.already_exists) {
          toast.success(
            res.data?.message || `Account already exists for ${res.data?.email || email}`,
            { duration: 7000 }
          );
        } else {
          toast.success(
            `Account created. Temp password: ${res.data?.temp_password || "(see admin)"}`,
            { duration: 10000 }
          );
        }
        await dir.refresh();
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Failed to provision account"));
      } finally {
        setActionLoading("");
      }
    },
    [canManageEmployeeAccounts, canProvisionEmployeeAccount, dir, resolveProvisioningEmail]
  );

  if (!canSeeEmployees) {
    return (
      <>
        <div
          className="max-w-4xl mx-auto p-8 text-center text-slate-500"
          data-testid="employees-denied"
        >
          Employee directory is not available for your role/module access.
        </div>
      </>
    );
  }

  return (
    <>
      <div
        className="max-w-full space-y-6 animate-fade-in"
        data-testid="employees-page"
      >
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">
              Directory
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">
              Employee Directory
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              {dir.total} identit{dir.total === 1 ? "y" : "ies"} in system
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {canCreateEmployee && (
              <>
                <Button
                  className="gap-2"
                  onClick={() =>
                    navigate(buildIdentityCreatePath(isPortalPath ? "portal" : "default"), {
                      state: { returnTo: currentDirectoryPath },
                    })
                  }
                  data-testid="employees-new"
                >
                  <UserPlus className="w-4 h-4" />
                  Regular Employee
                </Button>
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={() =>
                    navigate(buildIdentityCreatePath(isPortalPath ? "portal" : "default"), {
                      state: { returnTo: currentDirectoryPath, creationMode: "non_regular" },
                    })
                  }
                  data-testid="employees-new-non-regular"
                >
                  <UserPlus className="w-4 h-4" />
                  Non-Regular Employee
                </Button>
              </>
            )}
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => dir.refresh()}
              disabled={dir.refreshing}
              data-testid="employees-refresh"
            >
              <RefreshCw className={cn("w-4 h-4", dir.refreshing && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>

        <EmployeeDirectoryFilters
          dir={dir}
          getEmployeeStatusLabel={getEmployeeStatusLabel}
          getWorkflowStatusLabel={getWorkflowStatusLabel}
          setShowFilters={setShowFilters}
          setVisibleColumns={setVisibleColumns}
          showFilters={showFilters}
          visibleColumns={visibleColumns}
        />

        <EmployeeDirectoryTable
          actionLoading={actionLoading}
          canManageEmployeeAccounts={canManageEmployeeAccounts}
          dir={dir}
          getProvisioningAvailability={getProvisioningAvailability}
          handleProvisionAccount={handleProvisionAccount}
          isPortalPath={isPortalPath}
          labelMaps={labelMaps}
          tableRef={tableRef}
          visibleColumns={visibleColumns}
        />

        {/* Pagination + Count */}
        {dir.total > 0 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
            <span>
              Showing {dir.showingFrom}-{dir.showingTo} of {dir.total} employee
              {dir.total !== 1 ? "s" : ""}
              {dir.activeStatusFilter !== "ALL" && ` (${dir.workflowFilterKind} ${getWorkflowStatusLabel(dir.activeStatusFilter)})`}
            </span>
            {dir.totalPages > 1 && (
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  disabled={dir.currentPage <= 1}
                  onClick={() => dir.setPage((p) => p - 1)}
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </Button>
                {Array.from({ length: dir.totalPages }, (_, i) => i + 1)
                  .filter(
                    (p) =>
                      p === 1 ||
                      p === dir.totalPages ||
                      Math.abs(p - dir.currentPage) <= 1
                  )
                  .reduce((acc, p, idx, arr) => {
                    if (idx > 0 && p - arr[idx - 1] > 1) acc.push("...");
                    acc.push(p);
                    return acc;
                  }, [])
                  .map((item, idx) =>
                    item === "..." ? (
                      <span key={`dots-${idx}`} className="px-1 text-slate-400">
                        
                      </span>
                    ) : (
                      <Button
                        key={item}
                        variant={dir.currentPage === item ? "default" : "outline"}
                        size="icon"
                        className={cn(
                          "h-7 w-7 text-xs",
                          dir.currentPage === item && "pointer-events-none"
                        )}
                        onClick={() => dir.setPage(item)}
                      >
                        {item}
                      </Button>
                    )
                  )}
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  disabled={dir.currentPage >= dir.totalPages}
                  onClick={() => dir.setPage((p) => p + 1)}
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

    </>
  );
};

export default EmployeeDirectoryPage;


