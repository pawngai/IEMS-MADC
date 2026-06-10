import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Layout from "@/app/layout/Layout";
import { employeeProfileApi } from "@/contexts/employee_profile/api/employeeProfileApi";
import EmployeeProfileExtensionEditor from "@/contexts/employee_profile/components/EmployeeProfileExtensionEditor";
import {
  buildEmployeeFilePath,
  getEmployeeEditorScope,
} from "@/shared/lib/employeeEditorRoutes";
import {
  appendNoticeToPath,
  readNoticeFromSearch,
  stripNoticeFromSearch,
} from "@/shared/lib/routeNotice";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { toast } from "sonner";

const EmployeeProfileEditorPage = () => {
  const { employeeId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const scope = useMemo(() => getEmployeeEditorScope(location.pathname), [location.pathname]);
  const returnTo = location.state?.returnTo;
  const nonRegular = Boolean(location.state?.nonRegular);

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const fallbackReturnPath = useMemo(
    () => buildEmployeeFilePath(scope, employeeId),
    [employeeId, scope]
  );

  const loadProfile = useCallback(async () => {
    if (!employeeId) return;
    setLoading(true);
    try {
      const response = await employeeProfileApi.get(employeeId);
      setProfile(response.data || null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to load employee profile"));
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, [employeeId]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    const notice = readNoticeFromSearch(location.search);
    const message = notice.message || location.state?.successMessage;
    if (!message) return;
    const noticeKey = notice.context || location.pathname;
    toast.success(message, { id: `route-notice:${noticeKey}:${message}` });
    navigate(
      {
        pathname: location.pathname,
        search: stripNoticeFromSearch(location.search),
      },
      { replace: true, state: {} }
    );
  }, [location.pathname, location.search, location.state, navigate]);

  const handleCancel = () => {
    navigate(returnTo || fallbackReturnPath);
  };

  const handleSubmit = async (payload) => employeeProfileApi.update(employeeId, payload);

  const handleSuccess = async () => {
    const targetPath = returnTo || fallbackReturnPath;
    navigate(
      appendNoticeToPath(
        targetPath,
        "Employee profile updated successfully",
        "profile-updated"
      )
    );
  };

  if (loading) {
    return (
      <Layout>
        <div className="max-w-5xl mx-auto py-8">
          <Card>
            <CardContent className="py-12 text-center text-slate-500">Loading employee profile...</CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  if (!profile) {
    return (
      <Layout>
        <div className="max-w-5xl mx-auto py-8">
          <Card>
            <CardContent className="py-12 text-center text-slate-500">Employee profile not found.</CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  const identityWorkflowStatus = String(profile?.identity_workflow_status || "").trim().toUpperCase();
  if (identityWorkflowStatus && identityWorkflowStatus !== "ACTIVE") {
    return (
      <Layout>
        <div className="max-w-5xl mx-auto py-8">
          <Card>
            <CardHeader>
              <CardTitle>Profile editing unavailable</CardTitle>
              <CardDescription>Profile editing is available after the identity workflow is completed.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="gap-2" onClick={handleCancel}>
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
            </CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6 animate-fade-in" data-testid="employee-profile-editor-page">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Employee Profile</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Edit Employee Profile</h2>
            <p className="text-sm text-slate-500 mt-1">
              Profile extension is managed separately from employee identity creation.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="gap-2" onClick={handleCancel}>
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            {profile?.employee_code && (
              <Badge variant="outline" className="font-mono text-xs h-fit">
                {profile.employee_code}
              </Badge>
            )}
          </div>
        </div>

        <EmployeeProfileExtensionEditor
          profile={profile}
          nonRegular={nonRegular}
          submitAction={handleSubmit}
          onCancel={handleCancel}
          onSuccess={handleSuccess}
        />
      </div>
    </Layout>
  );
};

export default EmployeeProfileEditorPage;
