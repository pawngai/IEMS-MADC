import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ESS } from "@/shared/lib/routes";
import EmployeeProfile from "@/contexts/employee_master/components/EmployeeProfileSummary";
import EmployeeProfileExtensionEditor from "@/contexts/employee_master/components/EmployeeProfileExtensionEditor";
import { employeeProfileApi } from "@/contexts/employee_master/api/employeeProfileApi";
import { serviceBookAPI } from "@/contexts/service_book";
import { isServiceBookEligible } from "@/contexts/service_book";
import { useAuth } from "@/contexts/identity_access";
import { usePermissions } from "@/contexts/identity_access";
import { essAPI } from "@/contexts/ess";
import { Permissions } from "@/platform/permissions";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { formatServiceBookPartsIncompleteMessage, getApiErrorMessage } from "@/shared/lib/utils";
import { Edit, Loader2, RefreshCw, Send } from "lucide-react";
import { toast } from "sonner";
import { ProfileSkeleton } from "@/shared/ui/skeletons";

const STATUS_STYLES = {
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
};

const EssProfilePage = () => {
  const navigate = useNavigate();
  const { can } = usePermissions();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [serviceBook, setServiceBook] = useState(null);
  const [showWizard, setShowWizard] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const canViewProfile = can(Permissions.PROFILE_READ_OWN) || can(Permissions.PROFILE_READ_ALL);
  const canEditProfile = can(Permissions.PROFILE_UPDATE_OWN_LIMITED) || can(Permissions.PROFILE_UPDATE_ALL);
  const canReadOwnServiceBook = can(Permissions.SERVICE_BOOK_READ_OWN);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    try {
      const res = await essAPI.getMyProfile().catch(() => ({ data: null }));
      const nextProfile = res.data || null;
      let nextServiceBook = null;

      if (nextProfile?.employee_id && canReadOwnServiceBook && isServiceBookEligible(nextProfile)) {
        const serviceBookRes = await serviceBookAPI.getComplete(nextProfile.employee_id).catch(() => ({ data: null }));
        nextServiceBook = serviceBookRes.data || null;
      }

      setProfile(nextProfile);
      setServiceBook(nextServiceBook);
    } catch (error) {
      toast.error("Failed to load profile");
      setProfile(null);
      setServiceBook(null);
    } finally {
      setLoading(false);
    }
  }, [canReadOwnServiceBook]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  if (loading) {
    return (
      <>
        <div className="max-w-6xl mx-auto">
          <ProfileSkeleton />
        </div>
      </>
    );
  }

  const profileStatus = profile?.workflow_status || "DRAFT";
  const statusClass = STATUS_STYLES[profileStatus] || STATUS_STYLES.DRAFT;
  const editableStage = ["DRAFT", "REJECTED", "APPROVED"].includes(profileStatus);
  const submittableStage = ["DRAFT", "REJECTED"].includes(profileStatus);
  const reviewStage = ["SUBMITTED", "VERIFIED"].includes(profileStatus);
  const canShowEditButton = canEditProfile && profile && editableStage;
  const canSubmitProfile =
    canEditProfile &&
    profile &&
    submittableStage &&
    !!profile?.employee_section_completed &&
    !!profile?.data_entry_section_completed;
  const autoShowWizard = false;

  const handleSubmitProfile = async () => {
    if (!profile?.employee_id || !canSubmitProfile) return;
    setSubmitting(true);
    try {
      await employeeProfileApi.submit(profile.employee_id);
      setShowWizard(false);
      await loadProfile();
      toast.success("Profile submitted for verification");
    } catch (error) {
      const validationMessage = formatServiceBookPartsIncompleteMessage(error);
      toast.error(validationMessage || getApiErrorMessage(error, "Failed to submit profile"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in" data-testid="ess-profile-page">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Employee Self-Service Portal</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">My Profile</h2>
            <p className="text-sm text-slate-500 mt-1">
              {showWizard || autoShowWizard
                ? "Update your personal profile details."
                : "Your personal profile and current service details."}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={statusClass}>{profileStatus}</Badge>
            {canShowEditButton && !(showWizard || autoShowWizard) && (
              <Button className="gap-2" onClick={() => setShowWizard(true)}>
                <Edit className="w-4 h-4" />
                Edit Profile
              </Button>
            )}
            {canSubmitProfile && !(showWizard || autoShowWizard) && (
              <Button
                className="gap-2 bg-blue-600 hover:bg-blue-700"
                onClick={handleSubmitProfile}
                disabled={submitting}
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Submit for Review
              </Button>
            )}
            {(showWizard || autoShowWizard) && (
              <Button variant="outline" className="gap-2" onClick={() => setShowWizard(false)}>
                View Profile
              </Button>
            )}
            <Button variant="outline" className="gap-2" onClick={loadProfile}>
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
        </div>

        {/* No access */}
        {!canViewProfile && !profile && (
          <Card>
            <CardHeader>
              <CardTitle>Access not granted</CardTitle>
              <CardDescription>You do not have permission to view your profile.</CardDescription>
            </CardHeader>
          </Card>
        )}

        {/* No profile */}
        {canViewProfile && !profile && (
          <Card>
            <CardHeader>
              <CardTitle>Profile not available</CardTitle>
              <CardDescription>Your account is not linked to an employee profile yet.</CardDescription>
            </CardHeader>
          </Card>
        )}

        {/* Profile under creation workflow banner */}
        {canEditProfile && profile && submittableStage && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 flex items-center justify-between gap-3">
            <div className="text-sm text-amber-800 space-y-1">
              <p>Complete your employee-owned profile section here.</p>
              <p>
                Data Entry must complete their section too. Either you or Data Entry can submit once
                both sections have the required details.
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={() => navigate(ESS.DASHBOARD)}>
              Dashboard
            </Button>
          </div>
        )}

        {canEditProfile && profile && reviewStage && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 flex items-center justify-between gap-3">
            <p className="text-sm text-blue-700">
              Profile is under review in
              <Badge variant="outline" className="mx-1">{profileStatus}</Badge>
              stage and cannot be edited until the review is complete.
            </p>
            <Button variant="outline" size="sm" onClick={() => navigate(ESS.DASHBOARD)}>
              Dashboard
            </Button>
          </div>
        )}

        {/* Locked profile banner */}
        {canEditProfile && profile && profileStatus === "LOCKED" && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 flex items-center justify-between">
            <p className="text-sm text-blue-700">
              Profile is in <Badge variant="outline" className="mx-1">{profileStatus}</Badge> stage and cannot be edited directly.
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => navigate(ESS.CHANGE_REQUESTS)}>
                Change Requests
              </Button>
              <Button variant="outline" size="sm" onClick={() => navigate(ESS.DASHBOARD)}>
                Dashboard
              </Button>
            </div>
          </div>
        )}

        {canEditProfile && profile && submittableStage && !canSubmitProfile && (
          <Card className="border-amber-200 bg-amber-50/50">
            <CardContent className="py-3 px-4">
              <p className="text-sm text-amber-700">
                {!profile?.employee_section_completed && !profile?.data_entry_section_completed
                  ? "Both your section and the Data Entry section must be completed before submission."
                  : !profile?.employee_section_completed
                  ? "Complete the required employee-owned profile details before submitting."
                  : "Waiting for Data Entry to finish the required establishment details before submission."}
              </p>
            </CardContent>
          </Card>
        )}

        {/* EDIT VIEW */}
        {profile && (showWizard || autoShowWizard) && (
          <Card className="border-0 bg-white/90 shadow-sm">
            <CardHeader>
              <CardTitle>Update My Profile</CardTitle>
              <CardDescription>
                {submittableStage
                  ? "Complete your personal and contact profile details. Completion status is derived automatically from the saved details."
                  : "Update the employee-owned personal and contact details available to you after approval."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <EmployeeProfileExtensionEditor
                essMode
                profile={profile}
                submitAction={(payload) => employeeProfileApi.update(profile.employee_id, payload)}
                onSuccess={async () => {
                  setShowWizard(false);
                  await loadProfile();
                  toast.success("Profile updated");
                }}
                onCancel={() => setShowWizard(false)}
              />
            </CardContent>
          </Card>
        )}

        {/* PROFILE VIEW */}
        {profile && !(showWizard || autoShowWizard) && (
          <EmployeeProfile profile={profile} serviceBook={serviceBook} />
        )}

        {!canEditProfile && profile && (
          <Card className="border-slate-200 bg-slate-50/70">
            <CardContent className="py-3 px-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-slate-700">
                  Your profile is view-only in the employee portal. Contact the Establishment/Data Entry team for corrections or use change requests where applicable.
                </p>
                <Button variant="outline" size="sm" onClick={() => navigate(ESS.CHANGE_REQUESTS)}>
                  Open Change Requests
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
};

export default EssProfilePage;

