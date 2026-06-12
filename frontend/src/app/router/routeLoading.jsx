import { useLocation } from "react-router-dom";
import { useAuth } from "@/modules/identity_access";
import Layout from "@/app/layout/Layout";
import { Skeleton } from "@/shared/ui/skeleton";
import {
  CardSkeleton,
  DashboardSkeleton,
  EmployeeTableSkeleton,
  PageHeaderSkeleton,
  SearchBarSkeleton,
  StatGridSkeleton,
  TableSkeleton,
  WorkQueueSkeleton,
} from "@/shared/ui/skeletons";

export const PageLoader = ({ pathname = "" }) => (
  <div
    className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(15,23,42,0.06),_transparent_48%),linear-gradient(180deg,_#f8fafc_0%,_#eef2ff_100%)]"
    data-testid="boot-loader"
  >
    <div className="border-b border-slate-200/80 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold tracking-[0.2em] text-white shadow-sm">
            IEMS
          </div>
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">MADC-HRMS</p>
            <p className="text-sm font-medium text-slate-900">Preparing your workspace</p>
          </div>
        </div>
        <div className="hidden items-center gap-2 sm:flex">
          <Skeleton className="h-8 w-24 rounded-full" />
          <Skeleton className="h-8 w-20 rounded-full" />
        </div>
      </div>
    </div>

    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <RouteShellSkeleton pathname={pathname} />
    </div>
  </div>
);

export const resolveRouteLoadingVariant = (pathname = "") => {
  if (pathname === "/employees" || pathname.startsWith("/employees/") || pathname.startsWith("/portal/employees")) {
    return "employees";
  }
  if (
    pathname === "/work" ||
    pathname.startsWith("/portal/work")
  ) {
    return "work";
  }
  if (
    pathname === "/admin" ||
    pathname.startsWith("/admin/") ||
    pathname === "/auditor" ||
    pathname === "/analytics" ||
    pathname === "/leave" ||
    pathname.startsWith("/department-portal/") ||
    pathname === "/department-portal" ||
    pathname === "/ess/dashboard" ||
    pathname === "/portal/dashboard"
  ) {
    return "dashboard";
  }
  if (
    pathname.startsWith("/service-book") ||
    pathname.startsWith("/ess/") ||
    pathname === "/seniority"
  ) {
    return "detail";
  }
  return "generic";
};

export const RouteShellSkeleton = ({ pathname }) => {
  const variant = resolveRouteLoadingVariant(pathname);

  if (variant === "employees") {
    return (
      <div className="max-w-7xl mx-auto space-y-6" data-testid="route-shell-fallback">
        <PageHeaderSkeleton />
        <SearchBarSkeleton />
        <EmployeeTableSkeleton rows={8} />
      </div>
    );
  }

  if (variant === "work") {
    return (
      <div className="max-w-7xl mx-auto space-y-6" data-testid="route-shell-fallback">
        <PageHeaderSkeleton />
        <WorkQueueSkeleton items={8} />
      </div>
    );
  }

  if (variant === "dashboard") {
    return (
      <div className="max-w-6xl mx-auto space-y-6" data-testid="route-shell-fallback">
        <PageHeaderSkeleton />
        <StatGridSkeleton />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <CardSkeleton lines={4} />
          <CardSkeleton lines={4} />
        </div>
      </div>
    );
  }

  if (variant === "detail") {
    return (
      <div className="max-w-6xl mx-auto space-y-6" data-testid="route-shell-fallback">
        <PageHeaderSkeleton />
        <CardSkeleton lines={6} />
        <TableSkeleton rows={5} columns={4} />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto" data-testid="route-shell-fallback">
      <DashboardSkeleton />
    </div>
  );
};

export const RouteShellFallback = () => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading || !user) {
    return <PageLoader pathname={location.pathname} />;
  }

  return (
    <Layout>
      <RouteShellSkeleton pathname={location.pathname} />
    </Layout>
  );
};
