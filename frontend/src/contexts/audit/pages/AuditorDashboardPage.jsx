import { useState, useEffect, useCallback } from "react";
import Layout from "@/app/layout/Layout";
import { auditAPI, dashboardAPI } from "@/contexts/audit/api/auditApi";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { ScrollArea } from "@/shared/ui/scroll-area";
import { CardSkeleton, PageHeaderSkeleton, StatGridSkeleton, TableSkeleton } from "@/shared/ui/skeletons";
import { toast } from "sonner";
import {
  Eye,
  Search,
  Users,
  FileText,
  Clock,
  Activity,
  BookOpen,
  AlertTriangle,
} from "lucide-react";

const AuditorDashboard = () => {
  const [auditLogs, setAuditLogs] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    resourceType: "all",
    action: "all",
  });

  const fetchData = useCallback(async () => {
    try {
      const [logsRes, statsRes] = await Promise.all([
        auditAPI.getLogs({ limit: 100 }).catch(() => ({ data: [] })),
        dashboardAPI.getStats().catch(() => ({ data: {} })),
      ]);

      setAuditLogs(logsRes.data || []);
      setStats(statsRes.data || {});
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("Failed to load audit data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const fetchFilteredLogs = async () => {
    setLoading(true);
    try {
      const params = { limit: 100 };
      if (filters.resourceType && filters.resourceType !== "all") params.resource_type = filters.resourceType;
      if (filters.action && filters.action !== "all") params.action = filters.action;

      const res = await auditAPI.getLogs(params);
      setAuditLogs(res.data || []);
    } catch (error) {
      toast.error("Failed to fetch logs");
    } finally {
      setLoading(false);
    }
  };

  const getActionColor = (action) => {
    if (!action) return "bg-slate-100 text-slate-800";
    if (action.includes("CREATE") || action.includes("APPEND")) return "bg-green-100 text-green-800";
    if (action.includes("UPDATE")) return "bg-blue-100 text-blue-800";
    if (action.includes("DELETE") || action.includes("REJECT")) return "bg-red-100 text-red-800";
    if (action.includes("LOGIN")) return "bg-purple-100 text-purple-800";
    if (action.includes("WORKFLOW") || action.includes("VERIFY") || action.includes("APPROVE") || action.includes("ATTEST")) return "bg-amber-100 text-amber-800";
    if (action.includes("SUPERSEDE")) return "bg-orange-100 text-orange-800";
    return "bg-slate-100 text-slate-800";
  };

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6" data-testid="auditor-dashboard-loading">
          <PageHeaderSkeleton />
          <CardSkeleton lines={2} />
          <StatGridSkeleton count={3} />
          <TableSkeleton rows={8} columns={4} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="auditor-dashboard">
        {/* Header */}
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">
            Audit & Compliance Dashboard
          </h2>
          <p className="text-slate-500 mt-1 text-sm sm:text-base">
            Read-only access to all system logs and audit trail
          </p>
        </div>

        {/* Authority Info */}
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-3">
            <Eye className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-800">AUDITOR Authority</p>
              <p className="text-sm text-red-700">
                You have read-only access across all layers. You cannot initiate, modify, or approve any data.
                Focus on identifying anomalies and compliance gaps.
              </p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <Card className="dashboard-stat-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xl sm:text-2xl font-bold">{stats.total_employees || 0}</p>
                  <p className="text-xs sm:text-sm text-slate-500">Employees</p>
                </div>
                <Users className="w-6 h-6 sm:w-8 sm:h-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="dashboard-stat-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xl sm:text-2xl font-bold">{stats.total_service_book_entries || 0}</p>
                  <p className="text-xs sm:text-sm text-slate-500">Service Book Entries</p>
                </div>
                <BookOpen className="w-6 h-6 sm:w-8 sm:h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="dashboard-stat-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xl sm:text-2xl font-bold">{stats.total_audit_logs || auditLogs.length}</p>
                  <p className="text-xs sm:text-sm text-slate-500">Audit Logs</p>
                </div>
                <Activity className="w-6 h-6 sm:w-8 sm:h-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

        </div>

        {/* System Audit Trail */}
        <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Activity className="w-5 h-5" />
                      System Audit Trail
                    </CardTitle>
                    <CardDescription>
                      All system actions logged with timestamp and authority
                    </CardDescription>
                  </div>
                  <Badge className="bg-red-100 text-red-800 w-fit">
                    READ ONLY
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {/* Filters */}
                <div className="flex flex-wrap gap-3 mb-6">
                  <Select
                    value={filters.resourceType}
                    onValueChange={(v) => setFilters({ ...filters, resourceType: v })}
                  >
                    <SelectTrigger className="w-36 sm:w-48">
                      <SelectValue placeholder="Resource Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Resources</SelectItem>
                      <SelectItem value="employee_profile">Employee Profile</SelectItem>
                      <SelectItem value="service_book">Service Book</SelectItem>
                      <SelectItem value="auth">Authentication</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select
                    value={filters.action}
                    onValueChange={(v) => setFilters({ ...filters, action: v })}
                  >
                    <SelectTrigger className="w-36 sm:w-48">
                      <SelectValue placeholder="Action Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Actions</SelectItem>
                      <SelectItem value="LOGIN">Login</SelectItem>
                      <SelectItem value="CREATE">Create</SelectItem>
                      <SelectItem value="UPDATE">Update</SelectItem>
                      <SelectItem value="WORKFLOW">Workflow</SelectItem>
                    </SelectContent>
                  </Select>

                  <Button onClick={fetchFilteredLogs} variant="outline" size="sm" className="gap-2">
                    <Search className="w-4 h-4" />
                    Filter
                  </Button>
                </div>

                {/* Logs */}
                <ScrollArea className="h-[400px] sm:h-[500px]">
                  <div className="space-y-2">
                    {auditLogs.length === 0 ? (
                      <div className="text-center py-12 text-slate-500">
                        <Activity className="w-16 h-16 mx-auto mb-4 opacity-50" />
                        <p>No audit logs found</p>
                      </div>
                    ) : (
                      auditLogs.map((log, idx) => (
                        <div
                          key={log.id || idx}
                          className="p-3 sm:p-4 rounded-lg border border-slate-200 hover:bg-slate-50"
                          data-testid={`audit-log-${idx}`}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex flex-wrap items-center gap-2 mb-2">
                                <Badge className={getActionColor(log.action)}>
                                  {log.action}
                                </Badge>
                                <Badge variant="outline" className="text-xs">{log.authority}</Badge>
                                <span className="text-xs text-slate-500">
                                  {new Date(log.timestamp).toLocaleString()}
                                </span>
                              </div>

                              <div className="text-sm">
                                <span className="font-medium truncate">{log.user_name}</span>
                                <span className="text-slate-500 mx-2">?</span>
                                <span className="text-slate-600 truncate">
                                  {log.resource_type}/{log.resource_id?.slice(0, 8)}...
                                </span>
                              </div>

                              {log.details && Object.keys(log.details).length > 0 && (
                                <div className="mt-2 text-xs text-slate-500 font-mono bg-slate-100 p-2 rounded overflow-x-auto">
                                  {JSON.stringify(log.details, null, 2)}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

        {/* Compliance Notice */}
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">Compliance Reminder</p>
              <p className="text-sm text-amber-700">
                All system actions are logged for audit purposes. Review audit trails regularly
                to ensure compliance with organizational policies.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default AuditorDashboard;

