import { Link, useLocation } from "react-router-dom";
import { AlertTriangle, ArrowLeft } from "lucide-react";
import { useAuth } from "@/contexts/identity/model/authContext";
import { getDefaultLandingPath } from "@/app/router/defaultLanding";
import { AUTH } from "@/shared/lib/routes";
import { Button } from "@/shared/ui/button";

const AccessDeniedPage = ({
  title = "Access denied",
  description = "You do not have permission to view this page.",
}) => {
  const location = useLocation();
  const auth = useAuth();
  const homePath = auth.user ? getDefaultLandingPath(auth) || "/" : AUTH.LOGIN;

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-6">
      <div className="max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 text-amber-700">
          <AlertTriangle className="h-7 w-7" />
        </div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-3 text-sm text-slate-600">{description}</p>
        <p className="mt-2 text-xs text-slate-400">Requested path: {location.pathname}</p>
        <div className="mt-6 flex justify-center">
          <Button asChild className="gap-2">
            <Link to={homePath}>
              <ArrowLeft className="h-4 w-4" />
              Go to your home
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default AccessDeniedPage;