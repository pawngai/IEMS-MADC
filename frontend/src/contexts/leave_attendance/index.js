import { lazy } from "react";

export const LeaveDashboardPage = lazy(() => import("./pages/LeaveDashboardPage"));
export const EssLeavePage = lazy(() => import("./pages/EssLeavePage"));
export { leaveAPI } from "./api/leaveApi";
export { fetchMyLeaves, fetchPendingLeaveActions } from "./model/leaveHomeGateway";
