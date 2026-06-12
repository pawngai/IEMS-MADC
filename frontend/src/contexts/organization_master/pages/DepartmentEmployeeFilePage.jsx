import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { DEPT } from "@/shared/lib/routes";
import DepartmentEmployeeProfileSummary from "@/contexts/organization_master/components/DepartmentEmployeeProfileSummary";
import { useAuth } from "@/contexts/identity_access";
import { usePermissions } from "@/contexts/identity_access";
import { useDepartmentScope } from "@/contexts/organization_master/hooks/useDepartmentScope";
import {
  getDepartmentEmployeeFile,
  submitDepartmentProfile,
} from "@/contexts/organization_master/model/departmentProfileGateway";
import { Permissions } from "@/platform/permissions";
import {
  buildIdentityEditPath,
  buildProfileEditPath,
} from "@/shared/lib/employeeEditorRoutes";
import { readNoticeFromSearch, stripNoticeFromSearch } from "@/shared/lib/routeNotice";
import { cn, formatServiceBookPartsIncompleteMessage, getApiErrorMessage } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { ProfileSkeleton } from "@/shared/ui/skeletons";
import { toast } from "sonner";
import {
  AlertTriangle,
  ArrowLeft,
  Edit3,
  IdCard,
  Loader2,
  RefreshCw,
  Send,
  Calendar,
  User,
  XCircle,
} from "lucide-react";

const STATUS_STYLES = {
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
};

const DepartmentEmployeeFilePage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { employeeId } = useParams();
  const { can, canAny, canAccessModule } = usePermissions();
  const {
    loading,
    setLoading,
    selectedDepartment,
    scopeError,
    canUseDepartmentPortal,
    isDataEntry,
  } = useDepartmentScope();
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const canEditProfile = useMemo(() => {
    if (!profile || !isDataEntry) return false;
    if (!canAny([Permissions.PROFILE_UPDATE_ALL])) return false;
    return ["DRAFT", "REJECTED"].includes(profile.workflow_status || "DRAFT");
  }, [profile, isDataEntry, canAny]);

  const canSubmit = useMemo(() => {
    if (!canEditProfile) return false;
    return (
      !!profile?.employee_section_completed &&
      !!profile?.data_entry_section_completed
    );
  }, [profile, canEditProfile]);
  const canOpenLeaveHistory =
    canAccessModule("leave") &&
    (can(Permissions.LEAVE_READ_ALL) || can(Permissions.LEAVE_RECOMMEND) || can(Permissions.LEAVE_SANCTION));
  const leaveHistoryPath = employeeId
    ? `/leave?employee_id=${encodeURIComponent(employeeId)}`
    : "/leave";

  const loadProfile = useCallback(async () => {
    if (!employeeId) {
      setError("Employee id is missing.");
      setLoading(false);
      return;
    }

    try {
      const nextProfile = await getDepartmentEmployeeFile(employeeId);
      setProfile(nextProfile || null);
      setError("");
    } catch (requestError) {
      setProfile(null);
      const detail = requestError?.response?.data?.detail;
      const message = typeof detail === "string" ? detail : "Unable to load employee details.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [employeeId, setLoading]);

  useEffect(() => {
    if (!canUseDepartmentPortal) {
      setError("Departmental portal access is required.");
      return;
    }
    if (!selectedDepartment) return;
    loadProfile();
  }, [canUseDepartmentPortal, loadProfile, selectedDepartment]);

  useEffect(() => {
    const message = readNoticeFromSearch(location.search).message || location.state?.successMessage;
    if (!message) return;
    toast.success(message);
    navigate(
      {
        pathname: location.pathname,
        search: stripNoticeFromSearch(location.search),
      },
      { replace: true, state: {} }
    );
  }, [location.pathname, location.search, location.state, navigate]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadProfile();
    } finally {
      setRefreshing(false);
    }
  };

  const handleSubmit = async () => {
    if (!canSubmit || !employeeId) return;
    setSubmitting(true);
    try {
      await submitDepartmentProfile(employeeId);
      toast.success("Profile submitted for verification");
      await loadProfile();
    } catch (err) {
      const validationMessage = formatServiceBookPartsIncompleteMessage(err);
      toast.error(validationMessage || getApiErrorMessage(err, "Failed to submit profile"));
    } finally {
      setSubmitting(false);
    }
  };

  const workflowStatus = profile?.workflow_status || "DRAFT";

  if (loading) {
    return (
      <>
        <div className="max-w-6xl mx-auto" data-testid="department-employee-file-loading">
          <ProfileSkeleton />
        </div>
      </>
    );
  }

  if (scopeError) {
    return (
      <>
        <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4" data-testid="department-employee-file-scope-error">
          <AlertTriangle className="w-8 h-8 text-amber-500 mb-3" />
          <h2 className="text-lg font-semibold text-slate-800">Department Not Mapped</h2>
          <p className="text-sm text-slate-500 max-w-md">{scopeError}</p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in" data-testid="department-employee-file-page">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Departmental Workspace</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 truncate">
              {profile?.full_name || "Employee Profile"}
            </h2>
            {profile && (
              <div className="flex flex-wrap items-center gap-2 mt-2">
                {profile.employee_code && (
                  <Badge variant="outline" className="font-mono text-xs">{profile.employee_code}</Badge>
                )}
                <Badge className={cn("text-xs", STATUS_STYLES[workflowStatus])}>
                  {workflowStatus}
                </Badge>
                {(profile.employment_type || profile.employment_type_code) && (
                  <Badge variant="outline" className="text-xs capitalize">
                    {(profile.employment_type || profile.employment_type_code).toLowerCase()}
                  </Badge>
                )}
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-2 flex-shrink-0">
            <Button variant="outline" size="sm" className="gap-2" onClick={() => navigate(DEPT.HOME)}>
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            {canOpenLeaveHistory && (
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => navigate(leaveHistoryPath, { state: { returnTo: location.pathname } })}
                data-testid="department-employee-leave-history"
              >
                <Calendar className="w-4 h-4" />
                Leave History
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
              Refresh
            </Button>
            {canEditProfile && (
              <Button
                size="sm"
                variant="outline"
                className="gap-2"
                onClick={() => navigate(buildIdentityEditPath("department", employeeId))}
              >
                <IdCard className="w-4 h-4" />
                Edit Identity
              </Button>
            )}
            {canEditProfile && (
              <Button
                size="sm"
                className="gap-2"
                onClick={() => navigate(buildProfileEditPath("department", employeeId))}
              >
                <Edit3 className="w-4 h-4" />
                Edit Profile
              </Button>
            )}
            {canSubmit && (
              <Button size="sm" className="gap-2" onClick={handleSubmit} disabled={submitting}>
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Submit
              </Button>
            )}
          </div>
        </div>

        {error ? (
          <Card>
            <CardContent className="py-10 flex flex-col items-center text-center">
              <XCircle className="w-8 h-8 text-red-500 mb-3" />
              <p className="text-sm font-medium text-slate-700">Unable to load employee details</p>
              <p className="text-sm text-slate-500 mt-1">{error}</p>
            </CardContent>
          </Card>
        ) : profile ? (
          <div className="grid gap-6">
            <DepartmentEmployeeProfileSummary profile={profile} compact />
          </div>
        ) : (
          <Card>
            <CardContent className="py-10 flex flex-col items-center text-center">
              <User className="w-8 h-8 text-slate-400 mb-3" />
              <p className="text-sm font-medium text-slate-700">Employee not found</p>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
};

export default DepartmentEmployeeFilePage;