import { Fragment, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import AppShell from "@/app/layout/AppShell";
import { RouteShellFallback } from "@/app/router/routeLoading";
import { AdminRoutes } from "@/app/router/adminRoutes";
import { DepartmentRoutes } from "@/app/router/departmentRoutes";
import { EmployeeRoutes } from "@/app/router/employeeRoutes";
import { EssRoutes } from "@/app/router/essRoutes";
import { LandingRoutes, PublicRoutes } from "@/app/router/publicRoutes";

/** Route modules rendered inside the persistent AppShell layout route. */
const SHELL_ROUTE_MODULES = [
  LandingRoutes,
  AdminRoutes,
  DepartmentRoutes,
  EmployeeRoutes,
  EssRoutes,
];

const AppRouter = () => {
  return (
    <Suspense fallback={<RouteShellFallback />}>
      <Routes>
        <Route element={<AppShell />}>
          {SHELL_ROUTE_MODULES.map((RouteModule) => (
            <Fragment key={RouteModule.name}>{RouteModule()}</Fragment>
          ))}
        </Route>
        {PublicRoutes()}
      </Routes>
    </Suspense>
  );
};

export default AppRouter;
