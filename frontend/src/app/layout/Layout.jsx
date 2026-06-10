import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/identity/model/authContext";
import { isRegularEssEmployee } from "@/contexts/ess/services/essEligibility";
import { canAccessEssDocuments } from "@/contexts/ess/services/essDomainService";
import { Permissions } from "@/contexts/identity/model/rbac";
import { ESS, DEPT, OPS, MAIN, ADMIN, AUTH } from "@/shared/lib/routes";
import { Button } from "@/shared/ui/button";
import { Avatar, AvatarFallback } from "@/shared/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import {
  Shield,
  LayoutDashboard,
  Users,
  LogOut,
  Menu,
  X,
  Eye,
  Calendar,
  GitBranch,
  User,
  Bell,
  Building2,
  ArrowLeftRight,
  ChevronDown,
  Edit3,
  ClipboardList,
  AlertTriangle,
  BookOpen,
  BarChart3,
  ListOrdered,
  FileText,
  Lock,
} from "lucide-react";
import ChangePasswordDialog from "@/contexts/identity/model/changePasswordDialogAdapter";

export const buildSwitchTargets = ({
  isSystemAdmin,
  canDepartmentScopedPortal,
  hasDepartmentalAuthority,
  hasNonEmployeeAuthority,
  canAdminPortal,
  isGlobalRole,
  canEssPortal,
  essHomePath,
  authorities,
}) => {
  if (isSystemAdmin) return [];

  const pickDepartmentRole = () => {
    if (authorities.includes("HOD")) return "HOD";
    if (authorities.includes("DEPT_DATA_ENTRY")) return "DEPT_DATA_ENTRY";
    return null;
  };

  const pickGlobalRole = () => {
    if (authorities.includes("GLOBAL_DATA_ENTRY")) return "GLOBAL_DATA_ENTRY";
    if (authorities.includes("DEALING_ASSISTANT")) return "DEALING_ASSISTANT";
    const fallback = authorities.find((authority) => authority && authority !== "EMPLOYEE" && authority !== "SYSTEM_ADMIN");
    return fallback || null;
  };

  const targets = [];
  const canSwitchToDepartmental = canDepartmentScopedPortal && hasDepartmentalAuthority;
  const canSwitchToGlobalPortal =
    hasNonEmployeeAuthority &&
    !canAdminPortal &&
    (isGlobalRole || !canSwitchToDepartmental);

  if (canSwitchToDepartmental) {
    targets.push({
      id: "departmental",
      label: "Department Operations Portal",
      path: DEPT.DASHBOARD,
      role: pickDepartmentRole(),
      icon: Building2,
      dataTestId: "switch-departmental-portal",
    });
  }
  if (canSwitchToGlobalPortal) {
    targets.push({
      id: "portal",
      label: "Central Operations Portal",
      path: OPS.EMPLOYEES,
      role: pickGlobalRole(),
      icon: GitBranch,
      dataTestId: "switch-global-portal",
    });
  }
  if (canEssPortal) {
    targets.push({
      id: "ess",
      label: "Employee Self-Service Portal",
      path: essHomePath,
      role: authorities.includes("EMPLOYEE") ? "EMPLOYEE" : null,
      icon: LayoutDashboard,
      dataTestId: "switch-ess-portal",
    });
  }
  if (canAdminPortal) {
    targets.push({
      id: "admin",
      label: "System Administration Console",
      path: ADMIN.HOME,
      role: "SYSTEM_ADMIN",
      icon: Shield,
      dataTestId: "switch-admin-portal",
    });
  }

  return targets;
};

export const canEnterEssPortal = ({
  authorities,
  employeeId,
  canAccessEssPortal,
  hasEssPermissions,
}) => {
  return (
    Array.isArray(authorities) &&
    authorities.includes("EMPLOYEE") &&
    Boolean(employeeId) &&
    Boolean(canAccessEssPortal) &&
    Boolean(hasEssPermissions)
  );
};

const NAV_COLLAPSED_KEY = "iems_nav_collapsed";

const readCollapsed = () => {
  try {
    const raw = localStorage.getItem(NAV_COLLAPSED_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch { return {}; }
};

const Layout = ({ children }) => {
  const { user, logout, can, canAny, canAccessModule, canAccessEssPortal, getPrimaryAuthority, getAuthorityDisplayName, setActiveRole } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [essServiceBookEligible, setEssServiceBookEligible] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState(readCollapsed);

  const primaryAuthority = getPrimaryAuthority();
  const authorities = Array.isArray(user?.authorities) ? user.authorities : [];
  const departmentPortalLabel = (() => {
    try {
      const saved = String(localStorage.getItem("iems_department_label") || "").trim();
      if (saved) return saved;
    } catch { /* ignore */ }
    const departmentCode = String(user?.department_code || "").trim().toUpperCase();
    return departmentCode || "Department";
  })();
  const hasNonEmployeeAuthority = authorities.some((a) => a && a !== "EMPLOYEE");
  const isSystemAdmin = primaryAuthority === "SYSTEM_ADMIN";
  const isGlobalRole = authorities.includes("GLOBAL_DATA_ENTRY") || authorities.includes("DEALING_ASSISTANT");
  const hasDepartmentalAuthority = authorities.some((a) => ["DEPT_DATA_ENTRY", "HOD"].includes(a));

  // ── Permission flags ──────────────────────────────────────────────
  const hasEssPermissions = canAny([
    Permissions.DOCUMENT_READ_OWN,
    Permissions.PROFILE_READ_OWN, Permissions.SERVICE_BOOK_READ_OWN,
    Permissions.LEAVE_APPLY_OWN, Permissions.LEAVE_READ_OWN,
    Permissions.PROFILE_UPDATE_OWN_LIMITED, Permissions.PROFILE_UPDATE_ALL,
  ]);
  const canEssPortal = canEnterEssPortal({
    authorities, employeeId: user?.employee_id,
    canAccessEssPortal: canAccessEssPortal(), hasEssPermissions,
  });
  const canDepartmentScopedPortal =
    hasDepartmentalAuthority &&
    can(Permissions.PROFILE_READ_ALL);
  const canAdminPortal =
    isSystemAdmin && can(Permissions.USER_MANAGEMENT) && can(Permissions.SYSTEM_CONFIG) && canAccessModule("admin_console");
  const canEssDashboard = can(Permissions.PROFILE_READ_OWN) || can(Permissions.SERVICE_BOOK_READ_OWN);
  const canEssProfile = can(Permissions.PROFILE_READ_OWN) || can(Permissions.PROFILE_READ_ALL);
  const canEssDocuments = canAccessEssDocuments({ user, can });
  const canEssServiceBookPermission = can(Permissions.SERVICE_BOOK_READ_OWN);
  const canEssServiceBook = canEssServiceBookPermission && essServiceBookEligible;
  const canEssLeave = can(Permissions.LEAVE_APPLY_OWN) || can(Permissions.LEAVE_READ_OWN);
  const canDeptLeaveWorkflow = (can(Permissions.LEAVE_RECOMMEND) || can(Permissions.LEAVE_SANCTION)) && canAccessModule("leave");
  const canGlobalLeaveWorkflow = (can(Permissions.LEAVE_RECOMMEND) || can(Permissions.LEAVE_SANCTION)) && canAccessModule("leave");
  const canGlobalAudit = can(Permissions.AUDIT_READ_ALL) && canAccessModule("audit");
  const canAnalytics = can(Permissions.PROFILE_READ_ALL);
  const canSeniority = authorities.some((a) =>
    ["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT", "VERIFIER", "APPROVING_AUTHORITY", "SYSTEM_ADMIN"].includes(a)
  );
  const canDocumentManagement = isGlobalRole || isSystemAdmin;
  const canGlobalDirectory = canAny([
    Permissions.PROFILE_READ_ALL, Permissions.PROFILE_CREATE,
    Permissions.PROFILE_UPDATE_ALL, Permissions.SERVICE_BOOK_READ_ALL,
    Permissions.SERVICE_BOOK_ENTRY_CREATE,
  ]);

  // ── ESS service-book eligibility ──────────────────────────────────
  const isEssPortalPath = location.pathname === "/ess" || location.pathname.startsWith("/ess/");
  useEffect(() => {
    let active = true;
    const loadEssEligibility = async () => {
      if (!canEssPortal || !canEssServiceBookPermission || !isEssPortalPath) {
        if (active) setEssServiceBookEligible(false);
        return;
      }
      try {
        const eligible = await isRegularEssEmployee();
        if (active) setEssServiceBookEligible(eligible);
      } catch { if (active) setEssServiceBookEligible(false); }
    };
    loadEssEligibility();
    return () => { active = false; };
  }, [canEssPortal, canEssServiceBookPermission, isEssPortalPath, user?.employee_id]);

  const essHomePath = (() => {
    if (canEssDashboard) return ESS.DASHBOARD;
    if (canEssProfile) return ESS.PROFILE;
    if (canEssDocuments) return ESS.DOCUMENTS;
    if (canEssServiceBook) return ESS.SERVICE_BOOK;
    if (canEssLeave) return ESS.LEAVE;
    return ESS.DASHBOARD;
  })();

  // ── Unified nav sections (permission-based, not path-based) ───────
  const buildNavSections = () => {
    const sections = [];

    // My Work — ESS
    if (canEssPortal) {
      const items = [];
      if (canEssDashboard) items.push({ icon: LayoutDashboard, label: "Dashboard", path: ESS.DASHBOARD });
      if (canEssProfile) items.push({ icon: User, label: "My Profile", path: ESS.PROFILE });
      if (canEssServiceBook) items.push({ icon: BookOpen, label: "Service Book", path: ESS.SERVICE_BOOK });
      if (canEssLeave) items.push({ icon: Calendar, label: "Leave", path: ESS.LEAVE });
      items.push({ icon: Edit3, label: "Change Requests", path: ESS.CHANGE_REQUESTS });
      if (canEssDocuments) items.push({ icon: FileText, label: "My Documents", path: ESS.DOCUMENTS });
      if (can(Permissions.PROFILE_READ_OWN)) items.push({ icon: Bell, label: "Notifications", path: ESS.NOTIFICATIONS });
      if (items.length) sections.push({ id: "my-work", label: "My Work", items });
    }

    // Department
    if (canDepartmentScopedPortal && hasDepartmentalAuthority) {
      const items = [];
      items.push({ icon: LayoutDashboard, label: "Dashboard", path: DEPT.DASHBOARD });
      items.push({ icon: Users, label: "Directory", path: DEPT.DIRECTORY });
      items.push({ icon: AlertTriangle, label: "Pending Work", path: DEPT.PENDING_WORK });
      if (canDeptLeaveWorkflow) items.push({ icon: ClipboardList, label: "Leave Requests", path: DEPT.LEAVE });
      sections.push({ id: "department", label: departmentPortalLabel, items });
    }

    // Operations (global back-office)
    if (hasNonEmployeeAuthority && !isSystemAdmin) {
      const items = [];
      if (canGlobalDirectory) items.push({ icon: Users, label: "Employee Directory", path: OPS.EMPLOYEES });
      items.push({ icon: GitBranch, label: "Work Queue", path: OPS.WORK_QUEUE });
      if (canDocumentManagement) items.push({ icon: FileText, label: "Document Management", path: OPS.DOCUMENTS });
      if (canGlobalLeaveWorkflow) items.push({ icon: Calendar, label: "Leave Management", path: OPS.LEAVE });
      if (canSeniority) items.push({ icon: ListOrdered, label: "Seniority", path: ADMIN.SENIORITY });
      if (canGlobalAudit) items.push({ icon: Eye, label: "Audit Logs", path: OPS.AUDIT });
      if (canAnalytics) items.push({ icon: BarChart3, label: "Analytics", path: OPS.ANALYTICS });
      if (items.length) sections.push({ id: "operations", label: "Operations", items });
    }

    // Administration
    if (isSystemAdmin) {
      const items = [];
      if (canGlobalDirectory) items.push({ icon: Users, label: "Employee Directory", path: MAIN.EMPLOYEES });
      if (canDocumentManagement) items.push({ icon: FileText, label: "Document Management", path: MAIN.DOCUMENTS });
      if (canAdminPortal) items.push({ icon: Shield, label: "System Admin", path: ADMIN.HOME });
      items.push({ icon: ListOrdered, label: "Seniority", path: ADMIN.SENIORITY });
      if (canAccessModule("audit")) items.push({ icon: Eye, label: "Audit Logs", path: MAIN.AUDITOR });
      if (canAnalytics) items.push({ icon: BarChart3, label: "Analytics", path: MAIN.ANALYTICS });
      if (items.length) sections.push({ id: "admin", label: "Administration", items });
    }

    return sections;
  };

  const navSections = buildNavSections();

  // ── Portal switch (kept for role-context switching) ───────────────
  const switchTargets = buildSwitchTargets({
    isSystemAdmin, canDepartmentScopedPortal, hasDepartmentalAuthority,
    hasNonEmployeeAuthority, canAdminPortal, isGlobalRole,
    canEssPortal, essHomePath, authorities,
  });
  const isDepartmentPortalPath = location.pathname === "/department-portal" || location.pathname.startsWith("/department-portal/");
  const isAdminPath = location.pathname === "/admin" || location.pathname.startsWith("/admin/");
  const isSeniorityPath = location.pathname === "/seniority";
  const isGlobalPortalPath = location.pathname === "/portal" || location.pathname.startsWith("/portal/");
  const currentPortalId = (isAdminPath || isSeniorityPath) ? "admin" : isDepartmentPortalPath ? "departmental" : isEssPortalPath ? "ess" : "portal";
  const portalSwitchTargets = switchTargets.filter((t) => t.id !== currentPortalId);

  // ── Sidebar filtering for dual-role users ─────────────────────────
  // When inside a specific portal path, show only that portal's sidebar
  // section. At the root "/" (unified dashboard), show all sections.
  const filteredNavSections = (() => {
    const isRootPath = location.pathname === "/";
    if (isRootPath || navSections.length <= 1) return navSections;
    const portalToSection = { ess: "my-work", departmental: "department", portal: "operations", admin: "admin" };
    const targetId = portalToSection[currentPortalId];
    if (!targetId) return navSections;
    const filtered = navSections.filter((s) => s.id === targetId);
    return filtered.length > 0 ? filtered : navSections;
  })();

  // ── Handlers ──────────────────────────────────────────────────────
  const handleLogout = () => { logout(); navigate(AUTH.LOGIN); };
  const [showChangePassword, setShowChangePassword] = useState(false);

  const handlePortalSwitch = (target) => {
    setActiveRole(target?.role || null);
    try { localStorage.setItem("iems_switch_target", target?.path); } catch { /* ignore */ }
    navigate(target?.path);
  };

  const toggleSection = (sectionId) => {
    setCollapsedSections((prev) => {
      const next = { ...prev, [sectionId]: !prev[sectionId] };
      try { localStorage.setItem(NAV_COLLAPSED_KEY, JSON.stringify(next)); } catch { /* ignore */ }
      return next;
    });
  };

  // ── Active-item helper ────────────────────────────────────────────
  const isNavActive = (path) => {
    if (path === DEPT.HOME) {
      return location.pathname === DEPT.HOME || location.pathname.startsWith(DEPT.HOME + "/");
    }
    const aliases = {
      [OPS.WORK_QUEUE]: MAIN.WORK_QUEUE,
      [OPS.EMPLOYEES]: MAIN.EMPLOYEES,
      [OPS.DOCUMENTS]: MAIN.DOCUMENTS,
      [OPS.LEAVE]: MAIN.LEAVE,
      [OPS.AUDIT]: MAIN.AUDITOR,
      [OPS.ANALYTICS]: MAIN.ANALYTICS,
      [OPS.SERVICE_BOOK]: MAIN.SERVICE_BOOK,
      [OPS.SERVICE_BOOK_RECORDS]: MAIN.SERVICE_BOOK_RECORDS,
    };
    return location.pathname === path || location.pathname === aliases[path];
  };

  return (
    <div className="min-h-screen w-full overflow-x-clip bg-slate-50">
      {/* Mobile Menu Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full bg-slate-900 text-white transition-all duration-300 z-50 ${
          sidebarOpen ? "w-64 translate-x-0" : "w-64 -translate-x-full lg:translate-x-0 lg:w-20"
        }`}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-800">
            <Shield className="w-7 h-7 text-blue-400 flex-shrink-0" />
            <span className={`text-lg font-bold tracking-wide ${!sidebarOpen ? "lg:hidden" : ""}`}>IEMS</span>
          </div>

          {/* Navigation — sectioned */}
          <nav className="flex-1 py-3 overflow-y-auto">
            {filteredNavSections.map((section) => {
              const isCollapsed = filteredNavSections.length > 1 && !!collapsedSections[section.id];
              return (
                <div key={section.id} className="mb-1">
                  {/* Section heading (visible only when sidebar is expanded) */}
                  {filteredNavSections.length > 1 && (
                    <button
                      onClick={() => toggleSection(section.id)}
                      className={`w-full flex items-center justify-between px-4 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500 hover:text-slate-300 transition-colors ${!sidebarOpen ? "lg:hidden" : ""}`}
                      data-testid={`nav-section-${section.id}`}
                    >
                      {section.label}
                      <ChevronDown className={`w-3 h-3 transition-transform ${isCollapsed ? "-rotate-90" : ""}`} />
                    </button>
                  )}
                  {!isCollapsed && (
                    <ul className="space-y-0.5 px-2">
                      {section.items.map((item) => {
                        const Icon = item.icon;
                        const active = isNavActive(item.path);
                        return (
                          <li key={item.path}>
                            <Link
                              to={item.path}
                              onClick={() => setSidebarOpen(false)}
                              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                                active ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-white"
                              }`}
                              data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, "-")}`}
                            >
                              <Icon className="w-5 h-5 flex-shrink-0" />
                              <span className={!sidebarOpen ? "lg:hidden" : ""}>{item.label}</span>
                            </Link>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              );
            })}
          </nav>

          {/* Version Tag */}
          <div className={`px-4 py-3 border-t border-slate-800 ${!sidebarOpen && "lg:hidden"}`}>
            <p className="text-xs text-slate-400">MADC-HRMS</p>
            <p className="text-[10px] text-slate-500 mt-1">&copy; {new Date().getFullYear()} Mara Autonomous District Council</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`flex h-screen w-full min-w-0 max-w-full flex-col overflow-hidden transition-all duration-300 lg:ml-20 lg:w-[calc(100%-5rem)] ${sidebarOpen ? "lg:ml-64 lg:w-[calc(100%-16rem)]" : ""}`}>
        {/* Header */}
        <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b flex-shrink-0">
          <div className="flex min-w-0 items-center justify-between px-3 py-2.5 sm:px-6 sm:py-3 lg:px-8">
            <div className="flex min-w-0 items-center gap-3">
              {/* Mobile Menu Button */}
              <Button variant="ghost" size="sm" className="shrink-0 lg:hidden" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label={sidebarOpen ? "Close navigation menu" : "Open navigation menu"} title={sidebarOpen ? "Close navigation menu" : "Open navigation menu"} data-testid="mobile-menu-toggle">
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </Button>
              {/* Desktop Sidebar Toggle */}
              <Button variant="ghost" size="sm" className="hidden shrink-0 lg:flex" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"} title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"} data-testid="sidebar-toggle">
                <Menu className="w-5 h-5" />
              </Button>
              <div className="hidden sm:block">
                <h1 className="text-base sm:text-lg font-semibold text-slate-900">IEMS</h1>
              </div>
              <div className="sm:hidden">
                <h1 className="text-sm font-semibold text-slate-900">IEMS</h1>
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-2 sm:gap-4">
              {/* User menu */}
              <DropdownMenu modal={false}>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex h-10 min-w-[40px] max-w-full items-center gap-2 px-2" aria-label={`Open user menu for ${user?.name || "current user"}`} title="Open user menu" data-testid="user-menu-trigger">
                    <Avatar className="w-8 h-8 flex-shrink-0">
                      <AvatarFallback className="bg-slate-900 text-white text-sm">
                        {user?.name?.charAt(0) || "U"}
                      </AvatarFallback>
                    </Avatar>
                    <div className="hidden sm:flex flex-col items-start leading-tight">
                      <span className="text-sm font-medium max-w-36 truncate" title={user?.name}>{user?.name}</span>
                      <span className="text-[10px] text-slate-500 font-normal">{getAuthorityDisplayName(primaryAuthority)}</span>
                    </div>
                    <ChevronDown className="w-3.5 h-3.5 opacity-40 hidden sm:block" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 sm:w-64" data-testid="user-menu-content" sideOffset={8}>
                  <DropdownMenuLabel className="pb-2">
                    <div className="flex flex-col gap-1">
                      <span className="truncate font-semibold">{user?.name}</span>
                      <span className="text-xs text-slate-500 font-normal truncate">{user?.email}</span>
                    </div>
                  </DropdownMenuLabel>
                  {portalSwitchTargets.length > 0 && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuLabel className="text-xs text-slate-500 font-normal">Switch role context</DropdownMenuLabel>
                      {portalSwitchTargets.map((target) => {
                        const TargetIcon = target.icon || ArrowLeftRight;
                        return (
                          <DropdownMenuItem key={target.id} onClick={() => handlePortalSwitch(target)} className="cursor-pointer text-xs" data-testid={target.dataTestId}>
                            <TargetIcon className="w-4 h-4 mr-2" />
                            {target.label}
                          </DropdownMenuItem>
                        );
                      })}
                    </>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => setShowChangePassword(true)} className="cursor-pointer" data-testid="change-password-btn">
                    <Lock className="w-4 h-4 mr-2" />
                    Change Password
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600 cursor-pointer" data-testid="logout-btn">
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <ChangePasswordDialog open={showChangePassword} onOpenChange={setShowChangePassword} onLogout={handleLogout} />
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 min-h-0 min-w-0 overflow-x-hidden overflow-y-auto">
          <div className="min-w-0 max-w-full p-3 sm:p-6 lg:p-8">{children}</div>
        </div>

        {/* Global Footer */}
        <footer className="flex-shrink-0 z-20 border-t border-slate-200 bg-white/80 backdrop-blur-md px-3 sm:px-6 lg:px-8 py-3">
          <div className="text-center text-xs text-slate-500 space-y-0.5">
            <div>Mara Autonomous District Council</div>
            <div>&copy; {new Date().getFullYear()} MADC-HRMS. All rights reserved.</div>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default Layout;

