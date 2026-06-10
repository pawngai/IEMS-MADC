import { useCallback, useEffect, useState } from "react";
import Layout from "@/app/layout/Layout";
import { useDepartmentScope } from "@/contexts/department/hooks/useDepartmentScope";
import { departmentPortalAPI } from "@/contexts/department/api/departmentApi";
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { PageHeaderSkeleton, TableSkeleton } from "@/shared/ui/skeletons";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { toast } from "sonner";
import { AlertTriangle, CheckCircle2, Lock, RefreshCw } from "lucide-react";

const formatDate = (isoDate) => {
  if (!isoDate) return "";
  const d = new Date(isoDate + "T00:00:00");
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
};

const LEAVE_STATUS_STYLES = {
  SUBMITTED: "bg-amber-100 text-amber-700",
  RECOMMENDED: "bg-blue-100 text-blue-700",
  SANCTIONED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  CANCELLED: "bg-slate-100 text-slate-700",
};

const DeptLeavePage = () => {
  const {
    loading,
    setLoading,
    selectedDepartment,
    scopeError,
    canUseDepartmentPortal,
    canLeaveWorkflow,
  } = useDepartmentScope();
  const [refreshing, setRefreshing] = useState(false);
  const [pendingLeaves, setPendingLeaves] = useState([]);

  const loadLeaves = useCallback(async ({ mode = "refresh" } = {}) => {
    if (mode === "initial") setLoading(true); else setRefreshing(true);
    try {
      const res = await departmentPortalAPI.getPendingLeaves();
      const leaves = Array.isArray(res.data?.leaves) ? res.data.leaves : [];
      leaves.sort((a, b) => (Date.parse(b?.applied_at || "") || 0) - (Date.parse(a?.applied_at || "") || 0));
      setPendingLeaves(leaves);
    } catch {
      toast.error("Failed to load leave requests");
      setPendingLeaves([]);
    } finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => {
    if (!canUseDepartmentPortal || !canLeaveWorkflow || !selectedDepartment) return;
    loadLeaves({ mode: "initial" });
  }, [canLeaveWorkflow, canUseDepartmentPortal, loadLeaves, selectedDepartment]);

  if (!canUseDepartmentPortal || !canLeaveWorkflow) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4">
          <Lock className="w-8 h-8 text-slate-400 mb-3" />
          <h2 className="text-lg font-semibold text-slate-800">Access Restricted</h2>
          <p className="text-sm text-slate-500">You need leave workflow permissions to view this page.</p>
        </div>
      </Layout>
    );
  }

  if (scopeError) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4" data-testid="department-leave-scope-error">
          <AlertTriangle className="w-8 h-8 text-amber-500 mb-3" />
          <h2 className="text-lg font-semibold text-slate-800">Department Not Mapped</h2>
          <p className="text-sm text-slate-500 max-w-md">{scopeError}</p>
        </div>
      </Layout>
    );
  }

  if (loading) {
    return (
      <Layout>
        <div className="max-w-6xl mx-auto space-y-6" data-testid="dept-leave-page-loading">
          <PageHeaderSkeleton />
          <TableSkeleton rows={6} columns={5} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in" data-testid="dept-leave-page">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Department Operations Portal</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Leave Requests</h2>
            <p className="text-sm text-slate-500 mt-1">Pending leave requests routed for this department.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="gap-2" onClick={() => loadLeaves({ mode: "refresh" })} disabled={refreshing}>
              <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Content */}
        {pendingLeaves.length === 0 ? (
          <Card>
            <CardContent className="py-16">
              <div className="flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center mb-4">
                  <CheckCircle2 className="w-8 h-8 text-green-400" />
                </div>
                <p className="text-sm font-medium text-slate-700">No Pending Requests</p>
                <p className="text-xs text-slate-400 mt-1">All leave requests have been processed.</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="shadow-sm">
            <CardContent className="p-0">
              <div className="rounded-xl overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50/80">
                      <TableHead className="w-[30%]">Employee</TableHead>
                      <TableHead>Leave Type</TableHead>
                      <TableHead className="hidden sm:table-cell">Period</TableHead>
                      <TableHead className="text-center">Days</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingLeaves.map((leave) => (
                      <TableRow key={leave.id} className="hover:bg-orange-50/30">
                        <TableCell>
                          <div className="min-w-0">
                            <p className="font-medium text-slate-900 truncate">{leave.employee_name || leave.employee_id}</p>
                            <p className="text-xs text-slate-500 font-mono truncate">{leave.employee_id}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs font-normal">{leave.leave_type_code}</Badge>
                        </TableCell>
                        <TableCell className="hidden sm:table-cell text-sm text-slate-600">
                          <span>{formatDate(leave.from_date)}</span>
                          <span className="text-slate-400 mx-1">&ndash;</span>
                          <span>{formatDate(leave.to_date)}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="font-semibold text-slate-900">{leave.days_applied}</span>
                        </TableCell>
                        <TableCell>
                          <Badge className={cn("text-xs", LEAVE_STATUS_STYLES[leave.status] || "bg-slate-100 text-slate-700")}>{leave.status}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
};

export default DeptLeavePage;

