import { Fragment, Suspense } from "react";
import { Routes } from "react-router-dom";
import { RouteShellFallback } from "@/app/router/routeLoading";
import { AdminRoutes } from "@/app/router/adminRoutes";
import { DepartmentRoutes } from "@/app/router/departmentRoutes";
import { EmployeeRoutes } from "@/app/router/employeeRoutes";
import { EssRoutes } from "@/app/router/essRoutes";
import { PublicRoutes } from "@/app/router/publicRoutes";

const ROUTE_MODULES = [
  PublicRoutes,
  AdminRoutes,
  DepartmentRoutes,
  EmployeeRoutes,
  EssRoutes,
];

const AppRouter = () => {
  return (
    <Suspense fallback={<RouteShellFallback />}>
      <Routes>
        {ROUTE_MODULES.map((RouteModule) => (
          <Fragment key={RouteModule.name}>{RouteModule()}</Fragment>
        ))}
      </Routes>
    </Suspense>
  );
};

export default AppRouter;
