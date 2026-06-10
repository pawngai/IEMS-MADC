import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import Layout from "@/app/layout/Layout";
import { useDepartmentEmployeeDirectory } from "@/contexts/department/hooks/useDepartmentEmployeeDirectory";
import { useDepartmentScope } from "@/contexts/department/hooks/useDepartmentScope";
import { buildIdentityCreatePath } from "@/shared/lib/employeeEditorRoutes";
import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { EmployeeTableSkeleton, PageHeaderSkeleton, SearchBarSkeleton } from "@/shared/ui/skeletons";
import {
  AlertTriangle, ChevronLeft, ChevronRight, Lock, Plus, RefreshCw, Users,
} from "lucide-react";

import { DirectoryFilterBar } from "@/contexts/department/components/DirectoryFilterBar";
import { EmployeeCard } from "@/contexts/department/components/EmployeeCard";
import { EmployeeTableView } from "@/contexts/department/components/EmployeeTableView";

const DeptDirectoryPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    selectedDepartment,
    selectedDepartmentLabel,
    scopeError,
    canUseDepartmentPortal,
    canCreateProfile,
  } = useDepartmentScope();
  const dir = useDepartmentEmployeeDirectory({
    enabled: canUseDepartmentPortal && !!selectedDepartment,
  });

  const [viewMode, setViewMode] = useState("cards");
  const currentDirectoryPath = `${location.pathname}${location.search || ""}`;

  if (!canUseDepartmentPortal) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4">
          <Lock className="w-8 h-8 text-slate-400 mb-3" />
          <h2 className="text-lg font-semibold text-slate-800">Access Restricted</h2>
          <p className="text-sm text-slate-500">Department Operations Portal is available only for HOD and Data Entry roles.</p>
        </div>
      </Layout>
    );
  }

  if (dir.loading) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto space-y-6">
          <PageHeaderSkeleton />
          <SearchBarSkeleton />
          <EmployeeTableSkeleton rows={8} />
        </div>
      </Layout>
    );
  }

  if (scopeError) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4">
          <AlertTriangle className="w-8 h-8 text-amber-500 mb-3" />
          <h2 className="text-lg font-semibold text-slate-800">Department Not Mapped</h2>
          <p className="text-sm text-slate-500">{scopeError}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-5 animate-fade-in" data-testid="dept-directory-page">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Department Operations Portal</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Employee Directory</h2>
            <div className="flex items-center gap-3 mt-1.5">
              <p className="text-sm text-slate-500">{selectedDepartmentLabel}</p>
              {dir.total > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-xs font-medium text-slate-600">
                  <Users className="w-3 h-3" />
                  {dir.total} employee{dir.total !== 1 ? "s" : ""}
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {canCreateProfile && (
              <Button
                size="sm"
                className="gap-2"
                onClick={() =>
                  navigate(buildIdentityCreatePath("department"), {
                    state: { returnTo: currentDirectoryPath },
                  })
                }
              >
                <Plus className="w-4 h-4" />
                New Employee
              </Button>
            )}
            <Button variant="outline" size="sm" className="gap-2" onClick={() => dir.refresh()} disabled={dir.refreshing}>
              <RefreshCw className={cn("w-4 h-4", dir.refreshing && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Filter bar with search, filters, view toggle */}
        <DirectoryFilterBar dir={dir} viewMode={viewMode} onViewModeChange={setViewMode} />

        {/* Content area */}
        {dir.employees.length === 0 ? (
          <Card>
            <CardContent className="py-16">
              <div className="flex flex-col items-center justify-center text-center">
                <Users className="w-7 h-7 text-slate-300 mb-3" />
                <p className="text-sm font-medium text-slate-600">No employees found</p>
                <p className="text-xs text-slate-400 mt-1">{dir.query ? "Try a different search term" : "No employee records yet"}</p>
              </div>
            </CardContent>
          </Card>
        ) : viewMode === "cards" ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="dept-directory-cards">
            {dir.employees.map((employee) => (
              <EmployeeCard
                key={employee.employee_id}
                employee={employee}
              />
            ))}
          </div>
        ) : (
          <EmployeeTableView
            employees={dir.employees}
            sortField={dir.sortField}
            toggleSort={dir.toggleSort}
          />
        )}

        {/* Pagination */}
        {dir.total > 0 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
            <span>
              Showing {dir.showingFrom}-{dir.showingTo} of {dir.total} employee{dir.total !== 1 ? "s" : ""}
              {dir.activeStatusFilter !== "ALL" && ` (${dir.activeStatusFilter})`}
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
                  .filter((page) => page === 1 || page === dir.totalPages || Math.abs(page - dir.currentPage) <= 1)
                  .reduce((items, page, idx, src) => {
                    if (idx > 0 && page - src[idx - 1] > 1) items.push("...");
                    items.push(page);
                    return items;
                  }, [])
                  .map((item, idx) =>
                    item === "..."
                      ? <span key={`dots-${idx}`} className="px-1 text-slate-400">...</span>
                      : (
                        <Button
                          key={item}
                          variant={dir.currentPage === item ? "default" : "outline"}
                          size="icon"
                          className={cn("h-7 w-7 text-xs", dir.currentPage === item && "pointer-events-none")}
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
    </Layout>
  );
};

export default DeptDirectoryPage;

