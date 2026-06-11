import { useMemo } from "react";
import { useAuth } from "@/contexts/identity_access";
import { hasAuthority } from "@/contexts/access_control";

const TAB_OWNERSHIP = {
  "policy-masters": "system_admin",
  "rbac-users": "identity",
};

const useAdminConsolePermissions = () => {
  const { user } = useAuth();

  const isSystemAdmin = useMemo(() => hasAuthority(user, "SYSTEM_ADMIN"), [user]);

  const canAccessTab = (tabId) => {
    void TAB_OWNERSHIP[tabId];
    return isSystemAdmin;
  };

  return {
    isSystemAdmin,
    canAccessTab,
    tabOwnership: TAB_OWNERSHIP,
  };
};

export default useAdminConsolePermissions;
