import { useMemo } from "react";
import { ALLOWED_TABS } from "@/modules/admin/pages/systemAdminConsole.constants";
import useAdminConsolePermissions from "@/modules/admin/hooks/useAdminConsolePermissions";

const useAdminConsoleTabs = () => {
  const { canAccessTab, tabOwnership } = useAdminConsolePermissions();

  const tabs = useMemo(
    () => ALLOWED_TABS.filter((tab) => canAccessTab(tab.id)).map((tab) => ({ ...tab, owner: tabOwnership[tab.id] || "system_admin" })),
    [canAccessTab, tabOwnership]
  );

  const defaultTab = tabs[0]?.id || "dashboard";

  return {
    tabs,
    defaultTab,
  };
};

export default useAdminConsoleTabs;
