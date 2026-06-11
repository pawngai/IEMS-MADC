import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import Layout from "@/app/layout/Layout";
import EmployeeProfile from "@/contexts/employee_profile/components/EmployeeProfileSummary";
import { useAuth } from "@/contexts/identity_access";
import { usePermissions } from "@/contexts/identity_access";
import {
  buildIdentityEditPath,
  buildProfileEditPath,
} from "@/shared/lib/employeeEditorRoutes";
import { readNoticeFromSearch, stripNoticeFromSearch } from "@/shared/lib/routeNotice";
import { cn, formatServiceBookPartsIncompleteMessage, getApiErrorMessage } from "@/shared/lib/utils";
import { employeeProfileApi } from "@/contexts/employee_profile/api/employeeProfileApi";
import { mastersAPI } from "@/contexts/masters";
import { serviceBookAPI } from "@/contexts/service_book";
import { serviceRecordsApi } from "@/contexts/service_book";
import { normalizeWorkflowStage } from "@/platform/permissions";
import { Permissions } from "@/platform/permissions";
import { isNonRegularEmploymentType, isServiceBookEligible } from "@/contexts/service_book";
import { resolveServiceBookStatus } from "@/contexts/service_book";
import { getOpeningActionLabel } from "@/contexts/service_book";
import {
  buildReferenceLabelMap,
  formatDirectoryEnumLabel,
  formatWorkflowStatusLabel,
} from "@/contexts/employee_profile/lib/directoryLabels";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ProfileSkeleton, PageHeaderSkeleton } from "@/shared/ui/skeletons";
import { toast } from "sonner";
import { BookOpen, Calendar, Edit3, IdCard, Loader2, RefreshCw, Send, User } from "lucide-react";

const STATUS_STYLES = {
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  SUPERSEDED: "bg-slate-100 text-slate-700",
};

const EmployeeFile = () => {
  const { employeeId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { can, canAny, canAccessModule, getPrimaryAuthority } = usePermissions();

  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [submittingProfile, setSubmittingProfile] = useState(false);
  const [serviceSummary, setServiceSummary] = useState(null);
  const [serviceBookEntries, setServiceBookEntries] = useState([]);
  const [referenceData, setReferenceData] = useState({
    departments: [],
    designations: [],
    offices: [],
    payLevels: [],
    services: [],
    serviceGroups: [],
  });

  const primaryAuthority = getPrimaryAuthority?.() || "";
  const isApprovingAuthority = primaryAuthority === "APPROVING_AUTHORITY";
  const isEmployeeFileEditReadOnly = ["APPROVING_AUTHORITY", "VERIFIER"].includes(primaryAuthority);
  const profileStatus = profile?.workflow_status || "DRAFT";
  const canEditEmployee =
    !isEmployeeFileEditReadOnly &&
    canAny([Permissions.PROFILE_UPDATE_ALL, Permissions.PROFILE_UPDATE_OWN_LIMITED]) &&
    ["DRAFT", "REJECTED"].includes(profileStatus);
  const canSubmitProfile =
    canEditEmployee &&
    Boolean(profile?.employee_section_completed) &&
    Boolean(profile?.data_entry_section_completed);
  const serviceBookStatusInput = serviceSummary || (profile ? { eligible_for_service_book: isServiceBookEligible(profile) } : null);
  const serviceBookStatus = useMemo(() => resolveServiceBookStatus({ summary: serviceBookStatusInput, entries: serviceBookEntries }), [serviceBookEntries, serviceBookStatusInput]);
  const hasServiceBookModuleAccess = canAccessModule("service_book");
  const canAccessServiceBookOpening = ["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"].includes(primaryAuthority);
  const canManageServiceBookOpening =
    canAccessServiceBookOpening &&
    (can(Permissions.SERVICE_BOOK_READ_ALL) ||
      can(Permissions.SERVICE_BOOK_OPENING_CREATE) ||
      can(Permissions.SERVICE_BOOK_OPENING_UPDATE)) &&
    hasServiceBookModuleAccess &&
    serviceBookStatus.canOpen;
  const isRegularEmployee = isServiceBookEligible(serviceSummary || profile);
  const canViewServiceBook =
    (can(Permissions.SERVICE_BOOK_READ_ALL) || can(Permissions.SERVICE_BOOK_PRINT)) &&
    hasServiceBookModuleAccess &&
    serviceBookStatus.canOpen;
  const canOpenServiceBook =
    serviceBookStatus.status === "OPENED" ? canViewServiceBook : canManageServiceBookOpening;
  const canOpenServiceBookRecords = !isEmployeeFileEditReadOnly && canViewServiceBook;
  const canCreateRegularisation =
    !isEmployeeFileEditReadOnly &&
    can(Permissions.SERVICE_BOOK_ENTRY_CREATE) &&
    isNonRegularEmploymentType(serviceSummary || profile);
  const currentEmployeeFilePath = `${location.pathname}${location.search}`;
  const canOpenLeaveHistory =
    canAccessModule("leave") &&
    (can(Permissions.LEAVE_READ_ALL) || can(Permissions.LEAVE_RECOMMEND) || can(Permissions.LEAVE_SANCTION));
  const isPortalPath = location.pathname.startsWith("/portal");
  const serviceBookRef = profile?.employee_code || employeeId;
  const leaveHistoryRef = profile?.employee_id || employeeId;
  const serviceBookPath = isPortalPath
    ? `/portal/service-book/${serviceBookRef}`
    : `/service-book/${serviceBookRef}`;
  const serviceBookOpeningPath = isPortalPath
    ? `/portal/service-book/opening/${serviceBookRef}`
    : `/service-book/opening/${serviceBookRef}`;
  const serviceBookActionPath =
    serviceBookStatus.status === "OPENED" ? serviceBookPath : serviceBookOpeningPath;
  const serviceBookActionLabel = getOpeningActionLabel(serviceBookStatus.status);
  const serviceBookRecordsPath = isPortalPath
    ? `/portal/service-book/records/${serviceBookRef}`
    : `/service-book/records/${serviceBookRef}`;
  const leaveHistoryPath = leaveHistoryRef
    ? `/leave?employee_id=${encodeURIComponent(leaveHistoryRef)}`
    : "/leave";

  const loadProfile = useCallback(async () => {
    if (!employeeId) return;
    setProfileLoading(true);
    try {
      const res = await employeeProfileApi.get(employeeId);
      setProfile(res.data || null);
    } catch (error) {
      console.error("Failed to load profile:", error);
      toast.error(getApiErrorMessage(error, "Failed to load employee profile"));
      setProfile(null);
    } finally {
      setProfileLoading(false);
    }
  }, [employeeId]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    let active = true;
    if (!employeeId) return undefined;

    serviceRecordsApi.getServiceSummary(employeeId)
      .then((response) => {
        if (active) setServiceSummary(response?.data || null);
      })
      .catch(() => {
        if (active) setServiceSummary(null);
      });

    serviceBookAPI.listEntries(employeeId)
      .then(({ entries }) => {
        if (active) setServiceBookEntries(entries || []);
      })
      .catch(() => {
        if (active) setServiceBookEntries([]);
      });

    return () => {
      active = false;
    };
  }, [employeeId, refreshing]);

  useEffect(() => {
    let active = true;

    const loadReferenceData = async () => {
      try {
        const [deptRes, desigRes, officeRes, payRes, svcRes, grpRes] = await Promise.all([
          mastersAPI.getDepartments().catch(() => ({ data: [] })),
          mastersAPI.getDesignations().catch(() => ({ data: [] })),
          mastersAPI.getOffices().catch(() => ({ data: [] })),
          mastersAPI.getPayLevels().catch(() => ({ data: [] })),
          mastersAPI.getServices().catch(() => ({ data: [] })),
          mastersAPI.getServiceGroups().catch(() => ({ data: [] })),
        ]);

        if (!active) return;

        setReferenceData({
          departments: Array.isArray(deptRes.data) ? deptRes.data : deptRes.data?.departments || [],
          designations: Array.isArray(desigRes.data) ? desigRes.data : desigRes.data?.designations || [],
          offices: Array.isArray(officeRes.data) ? officeRes.data : officeRes.data?.offices || [],
          payLevels: Array.isArray(payRes.data) ? payRes.data : payRes.data?.pay_levels || [],
          services: Array.isArray(svcRes.data) ? svcRes.data : svcRes.data?.services || [],
          serviceGroups: Array.isArray(grpRes.data) ? grpRes.data : grpRes.data?.service_groups || [],
        });
      } catch {
        if (!active) return;
        setReferenceData({
          departments: [],
          designations: [],
          offices: [],
          payLevels: [],
          services: [],
          serviceGroups: [],
        });
      }
    };

    loadReferenceData();

    return () => {
      active = false;
    };
  }, []);

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

  const handleSubmitProfile = async () => {
    if (!profile?.employee_id || !canSubmitProfile) return;
    setSubmittingProfile(true);
    try {
      await employeeProfileApi.submit(profile.employee_id);
      await loadProfile();
      toast.success("Profile submitted for verification");
    } catch (error) {
      const validationMessage = formatServiceBookPartsIncompleteMessage(error);
      toast.error(validationMessage || getApiErrorMessage(error, "Failed to submit profile"));
    } finally {
      setSubmittingProfile(false);
    }
  };

  const header = useMemo(() => {
    const name = profile?.full_name || profile?.name || employeeId || "Employee";
    const code = profile?.employee_code || "-";
    const type = formatDirectoryEnumLabel(profile?.employment_type || profile?.employment_type_code) || "-";
    const status = normalizeWorkflowStage(profile?.workflow_status || "DRAFT") || "DRAFT";
    const statusLabel = formatWorkflowStatusLabel(status);
    return { name, code, type, status, statusLabel };
  }, [profile, employeeId]);

  const referenceLabelMaps = useMemo(() => ({
    department: buildReferenceLabelMap(referenceData.departments),
    designation: buildReferenceLabelMap(referenceData.designations),
    office: buildReferenceLabelMap(referenceData.offices),
    payLevel: buildReferenceLabelMap(referenceData.payLevels),
    service: buildReferenceLabelMap(referenceData.services),
    serviceGroup: buildReferenceLabelMap(referenceData.serviceGroups),
  }), [referenceData]);

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in" data-testid="employee-profile-page">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Employee Identity</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 truncate">{header.name}</h2>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <Badge variant="outline" className="font-mono text-xs">
                {header.code}
              </Badge>
              <Badge className={STATUS_STYLES[header.status] || "bg-slate-100 text-slate-700"}>
                {header.statusLabel}
              </Badge>
              <Badge variant="outline" className="text-xs">
                {header.type}
              </Badge>

            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {employeeId && canOpenLeaveHistory && (
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => navigate(leaveHistoryPath, { state: { returnTo: currentEmployeeFilePath } })}
                data-testid="employee-profile-leave-history"
              >
                <Calendar className="w-4 h-4" />
                Leave History
              </Button>
            )}
            {employeeId && canViewServiceBook && (
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => navigate(serviceBookPath)}
                data-testid="employee-profile-view-servicebook"
              >
                <BookOpen className="w-4 h-4" />
                View Service Book
              </Button>
            )}
            {employeeId && canOpenServiceBookRecords && (
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => navigate(serviceBookRecordsPath)}
                data-testid="employee-profile-service-book-records"
              >
                Service Book Records
              </Button>
            )}
            {employeeId && canCreateRegularisation && (
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => navigate(isPortalPath ? `/portal/employees/${employeeId}/regularisation` : `/employees/${employeeId}/regularisation`)}
                data-testid="employee-profile-regularisation"
              >
                Regularisation
              </Button>
            )}
            <Button
              variant="outline"
              className="gap-2"
              onClick={handleRefresh}
              disabled={refreshing}
              data-testid="employee-profile-refresh"
            >
              <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
              Refresh
            </Button>
            {canEditEmployee && (
              <Button
                variant="outline"
                className="gap-2"
                onClick={() =>
                  navigate(buildIdentityEditPath(isPortalPath ? "portal" : "default", employeeId), {
                    state: { returnTo: currentEmployeeFilePath },
                  })
                }
                data-testid="employee-profile-edit-identity"
              >
                <IdCard className="w-4 h-4" />
                Edit Identity
              </Button>
            )}
            {canEditEmployee && (
              <Button
                className="gap-2"
                onClick={() =>
                  navigate(buildProfileEditPath(isPortalPath ? "portal" : "default", employeeId), {
                    state: {
                      returnTo: currentEmployeeFilePath,
                      nonRegular: isNonRegularEmploymentType(serviceSummary || profile),
                    },
                  })
                }
                data-testid="employee-profile-edit-profile"
              >
                <Edit3 className="w-4 h-4" />
                Edit Profile
              </Button>
            )}
            {canSubmitProfile && (
              <Button
                className="gap-2 bg-blue-600 hover:bg-blue-700"
                onClick={handleSubmitProfile}
                disabled={submittingProfile}
                data-testid="employee-profile-submit-profile"
              >
                {submittingProfile ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Submit for Review
              </Button>
            )}
          </div>
        </div>

        <div className="rounded-md border border-slate-200 bg-white px-4 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Service Book</p>
            <p className="text-sm font-semibold text-slate-900">{serviceBookStatus.label}</p>
            <p className="text-xs text-slate-500 mt-1">{serviceBookStatus.reason}</p>
          </div>
          {canOpenServiceBook && (
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => navigate(serviceBookActionPath)}
              data-testid="employee-profile-servicebook"
            >
              <BookOpen className="w-4 h-4" />
              {serviceBookActionLabel}
            </Button>
          )}
        </div>

        {profileLoading ? (
          <div data-testid="employee-profile-loading">
            <ProfileSkeleton />
          </div>
        ) : !profile ? (
          <div className="text-center py-12 text-slate-500" data-testid="employee-profile-not-found">
            <User className="w-16 h-16 mx-auto mb-4 opacity-50" />
            Employee profile not found or access denied.
          </div>
        ) : (
          <EmployeeProfile profile={profile} serviceSummary={serviceSummary} referenceLabelMaps={referenceLabelMaps} />
        )}
      </div>
    </Layout>
  );
};

export default EmployeeFile;

