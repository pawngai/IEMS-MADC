import { Link } from "react-router-dom";
import { ArrowLeft, BookOpen, RefreshCw } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Card, CardHeader, CardTitle } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import OpeningStatusBadge from "@/contexts/service_book/opening/components/OpeningStatusBadge";

const OpeningHeader = ({ employeeId, employeeName, employeeCode, status, loading, onRefresh }) => (
  <Card>
    <CardHeader className="pb-3">
      <Link
        to={employeeId ? `/employees/${employeeId}` : "/employees"}
        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-2 w-fit"
      >
        <ArrowLeft className="w-3 h-3" />
        Back to Employee
      </Link>
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Opening Workflow</p>
          <CardTitle className="text-2xl font-bold text-foreground flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            Service Book Opening
          </CardTitle>
          <p className="text-sm font-medium text-foreground mt-1">{employeeName}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {employeeCode && (
              <Badge variant="outline" className="bg-surface-container-low font-mono text-xs">
                {employeeCode}
              </Badge>
            )}
            <OpeningStatusBadge status={status} />
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={onRefresh} disabled={loading} className="gap-1">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>
    </CardHeader>
  </Card>
);

export default OpeningHeader;
