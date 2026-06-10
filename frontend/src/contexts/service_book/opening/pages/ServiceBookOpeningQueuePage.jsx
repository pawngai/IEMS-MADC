import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/app/layout/Layout";
import { BookOpen, RefreshCw, Users } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { serviceBookOpeningApi } from "@/contexts/service_book/opening/api/serviceBookOpeningApi";
import OpeningStatusBadge from "@/contexts/service_book/opening/components/OpeningStatusBadge";
import { getOpeningCta } from "@/contexts/service_book/opening/services/openingDomainService";
import { OPENING_STATUS } from "@/contexts/service_book/opening/model/openingStatus";

const getRows = (response) => {
  const data = response?.data || response || {};
  if (Array.isArray(data)) return data;
  return data.items || data.results || data.openings || [];
};

const ServiceBookOpeningQueuePage = () => {
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const response = await serviceBookOpeningApi.listQueue();
      setRows(getRows(response));
    } catch {
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openRow = (row) => {
    const employeeId = row.employee_id || row.employee_code;
    if (!employeeId) return;
    const cta = getOpeningCta(row);
    navigate(cta.target === "service_book" ? `/service-book/${employeeId}` : `/service-book/opening/${employeeId}`);
  };

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6 animate-fade-in" data-testid="service-book-opening-queue-page">
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5" />
                <CardTitle className="text-2xl font-bold text-slate-900">Service Book Opening</CardTitle>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" className="gap-2" onClick={() => navigate("/employees")}>
                  <Users className="w-4 h-4" />
                  Employees
                </Button>
                <Button variant="outline" className="gap-2" onClick={load} disabled={loading}>
                  <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {rows.length === 0 ? (
              <div className="py-10 text-center text-sm text-slate-500">
                Select a regular employee from the directory to open or continue Service Book Opening.
              </div>
            ) : (
              <div className="rounded-md border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Employee</TableHead>
                      <TableHead>Code</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((row) => {
                      const status = row.status || row.workflow_status || OPENING_STATUS.NOT_STARTED;
                      const cta = getOpeningCta(row);
                      return (
                        <TableRow key={row.employee_id || row.employee_code}>
                          <TableCell>{row.full_name || row.employee_name || row.employee_id}</TableCell>
                          <TableCell className="font-mono text-xs">{row.employee_code || row.employee_id}</TableCell>
                          <TableCell><OpeningStatusBadge status={status} /></TableCell>
                          <TableCell className="text-right">
                            <Button size="sm" onClick={() => openRow(row)}>{cta.label}</Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default ServiceBookOpeningQueuePage;
