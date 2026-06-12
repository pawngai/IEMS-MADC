import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { DEPT } from "@/shared/lib/routes";
import { useDepartmentScope } from "@/contexts/organization_master/hooks/useDepartmentScope";
import { departmentPortalAPI } from "@/contexts/organization_master/api/departmentApi";
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { toast } from "sonner";
import { TableSkeleton, PageHeaderSkeleton } from "@/shared/ui/skeletons";
import {
  AlertTriangle, ArrowUpRight, CheckCircle2, Edit3, FileText, Lock,
  RefreshCw, ShieldCheck, XCircle,
} from "lucide-react";

const STATUS_STYLES = {
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
};

const DeptPendingWorkPage = () => {
  const navigate = useNavigate();
  const {
    loading,
    setLoading,
    selectedDepartment,
    scopeError,
    canUseDepartmentPortal,
    isDataEntry,
  } = useDepartmentScope();
  const [refreshing, setRefreshing] = useState(false);
  const [pendingWork, setPendingWork] = useState([]);

  const loadPendingWork = useCallback(async ({ mode = "refresh" } = {}) => {
    if (mode === "initial") setLoading(true); else setRefreshing(true);
    try {
      const res = await departmentPortalAPI.getPendingWork();
      setPendingWork(Array.isArray(res.data?.items) ? res.data.items : []);
    } catch {
      toast.error("Failed to load pending work");
      setPendingWork([]);
    } finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => {
    if (!canUseDepartmentPortal || !selectedDepartment) return;
    loadPendingWork({ mode: "initial" });
  }, [canUseDepartmentPortal, loadPendingWork, selectedDepartment]);

  if (!canUseDepartmentPortal) {
    return (
      <>
        <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4">
          <Lock className="w-8 h-8 text-slate-400 mb-3" />
          <h2 className="text-lg font-semibold text-slate-800">Access Restricted</h2>
        </div>
      </>
    );
  }

  if (scopeError) {
    return (
      <>
        <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4" data-testid="department-pending-work-scope-error">
          <AlertTriangle className="w-8 h-8 text-amber-500 mb-3" />
          <h2 className="text-lg font-semibold text-slate-800">Department Not Mapped</h2>
          <p className="text-sm text-slate-500 max-w-md">{scopeError}</p>
        </div>
      </>
    );
  }

  if (loading) {
    return (
      <>
        <div className="max-w-6xl mx-auto space-y-6">
          <PageHeaderSkeleton />
          <TableSkeleton rows={6} columns={4} />
        </div>
      </>
    );
  }

  const draftCount = pendingWork.filter((i) => i.workflow_status === "DRAFT").length;
  const rejectedCount = pendingWork.filter((i) => i.workflow_status === "REJECTED").length;

  return (
    <>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in" data-testid="dept-pending-work-page">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Department Operations Portal</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Pending Work</h2>
            <p className="text-sm text-slate-500 mt-1">Profiles that need your attention  edit drafts or address rejections.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {pendingWork.length > 0 && (
              <>
                <Badge className="bg-slate-100 text-slate-700 gap-1"><FileText className="w-3 h-3" />{draftCount} Draft</Badge>
                <Badge className="bg-red-100 text-red-700 gap-1"><XCircle className="w-3 h-3" />{rejectedCount} Rejected</Badge>
              </>
            )}
            <Button variant="outline" size="sm" className="gap-2" onClick={() => loadPendingWork({ mode: "refresh" })} disabled={refreshing}>
              <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Content */}
        {pendingWork.length === 0 ? (
          <Card>
            <CardContent className="py-16">
              <div className="flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center mb-4">
                  <ShieldCheck className="w-8 h-8 text-green-400" />
                </div>
                <p className="text-sm font-medium text-slate-700">All Clear!</p>
                <p className="text-xs text-slate-400 mt-1">No profiles need attention right now.</p>
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
                      <TableHead className="w-[35%]">Employee</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="hidden md:table-cell">Action Needed</TableHead>
                      <TableHead className="text-right">Go</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingWork.map((item) => {
                      const initials = (item.full_name || "E").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();
                      return (
                        <TableRow key={item.employee_id} className="hover:bg-amber-50/40 cursor-pointer" onClick={() => navigate(DEPT.EMPLOYEE(item.employee_id))}>
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <div className={cn("w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0", item.workflow_status === "REJECTED" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-600")}>{initials}</div>
                              <div className="min-w-0">
                                <p className="font-medium text-slate-900 truncate">{item.full_name || "Employee"}</p>
                                <p className="text-xs text-slate-500 font-mono truncate">{item.employee_code || item.employee_id}</p>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge className={cn("text-xs", STATUS_STYLES[item.workflow_status] || "bg-slate-100 text-slate-700")}>{item.workflow_status}</Badge>
                          </TableCell>
                          <TableCell className="hidden md:table-cell">
                            <p className="text-sm text-slate-600">{item.action_needed}</p>
                            {item.rejection_reason && (
                              <p className="text-xs text-red-500 mt-0.5 flex items-center gap-1"><XCircle className="w-3 h-3 flex-shrink-0" />{item.rejection_reason}</p>
                            )}
                          </TableCell>
                          <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-end gap-1">
                              {isDataEntry && ["DRAFT", "REJECTED"].includes(item.workflow_status) && (
                                <Button variant="default" size="sm" className="gap-1" onClick={() => navigate(DEPT.EMPLOYEE(item.employee_id))}>
                                  <Edit3 className="w-3 h-3" />Edit
                                </Button>
                              )}
                              <Button variant="outline" size="sm" className="gap-1" onClick={() => navigate(DEPT.EMPLOYEE(item.employee_id))}>
                                Open <ArrowUpRight className="w-3 h-3" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
};

export default DeptPendingWorkPage;

