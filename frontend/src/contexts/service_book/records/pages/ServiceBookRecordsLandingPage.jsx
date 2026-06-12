import { useLocation, useNavigate } from "react-router-dom";
import { OPS, MAIN } from "@/shared/lib/routes";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { GitBranch, Users, ArrowRight } from "lucide-react";

const ServiceBookRecordsLandingPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isPortalPath = location.pathname.startsWith("/portal");
  const directoryPath = isPortalPath ? OPS.EMPLOYEES : MAIN.EMPLOYEES;

  return (
    <>
      <div className="max-w-4xl mx-auto space-y-6 animate-fade-in" data-testid="service-records-landing-page">
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <GitBranch className="w-5 h-5" />
              <CardTitle className="text-2xl font-bold text-slate-900">Service Book Records</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <p className="text-sm text-slate-600">
              Service Book records are managed per employee. Select an employee from the directory to open the
              official record stream, record new entries, and manage corrections/documents.
            </p>

            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="text-xs">Per-employee timeline</Badge>
              <Badge variant="outline" className="text-xs">Record / Correct / Void / Attach docs</Badge>
              <Badge variant="outline" className="text-xs">Permission & module controlled</Badge>
            </div>

            <div className="pt-1">
              <Button onClick={() => navigate(directoryPath)} className="gap-2" data-testid="service-records-open-directory-btn">
                <Users className="w-4 h-4" />
                Open Employee Directory
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
};

export default ServiceBookRecordsLandingPage;
