import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { essAPI } from "@/contexts/ess";
import { useAuth, usePermissions } from "@/contexts/identity_access";
import { employeeIdentityApi } from "@/contexts/employee_master";
import { leaveAPI } from "@/contexts/leave/api/leaveApi";
import { EMPLOYEE, resolveScopeAccess } from "@/contexts/access_control";
import { Permissions } from "@/platform/permissions";
import { getApiErrorMessage, getLeaveTypeUnavailableMessage } from "@/shared/lib/utils";
import { toast } from "sonner";
import {
  buildLeaveApplicationPayload,
  createInitialLeaveApplyForm,
  getLeaveEligibilityValidationMessage,
  getLeaveSupportingDocumentValidationMessage,
} from "@/contexts/leave/model/leaveApplyForm";

export const LEAVE_TYPE_LABELS = {
  EL: "Earned Leave",
  HPL: "Half Pay Leave",
  CML: "Commuted Leave",
  LND: "Leave Not Due",
  CL: "Casual Leave",
};

const extractBalanceMap = (response) => response?.data?.balances || response?.balances || {};

export const useLeaveDashboardController = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const { can, canAccessModule } = usePermissions();
  const leaveModuleEnabled = canAccessModule("leave");
  const canApply = leaveModuleEnabled && can(Permissions.LEAVE_APPLY_OWN);
  const canReadOwn = leaveModuleEnabled && can(Permissions.LEAVE_READ_OWN);
  const canReadAll = leaveModuleEnabled && can(Permissions.LEAVE_READ_ALL);
  const canRecommend = leaveModuleEnabled && can(Permissions.LEAVE_RECOMMEND);
  const canSanction = leaveModuleEnabled && can(Permissions.LEAVE_SANCTION);
  const leaveApplyScope = resolveScopeAccess(user);
  const isEmployeeSelf = leaveApplyScope.scope === EMPLOYEE;
  const canApplySelf = canApply && isEmployeeSelf && leaveApplyScope.allowed;
  const selectedEmployeeId = (searchParams.get("employee_id") || "").trim();
  const canViewEmployeeHistory = leaveModuleEnabled && (canReadAll || canRecommend || canSanction);
  const isEmployeeHistoryMode = Boolean(selectedEmployeeId && canViewEmployeeHistory);
  const employeeHistoryReturnPath = location.state?.returnTo || "";

  const [profile, setProfile] = useState(null);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [balances, setBalances] = useState({});
  const [myLeaves, setMyLeaves] = useState([]);
  const [selectedEmployeeLeaves, setSelectedEmployeeLeaves] = useState([]);
  const [selectedEmployeeBalances, setSelectedEmployeeBalances] = useState({});
  const [selectedEmployeeInfo, setSelectedEmployeeInfo] = useState(null);
  const [selectedEmployeeLeaveType, setSelectedEmployeeLeaveType] = useState("");
  const [employeeHistorySearchQuery, setEmployeeHistorySearchQuery] = useState("");
  const [employeeHistorySearchResults, setEmployeeHistorySearchResults] = useState([]);
  const [employeeHistorySearchLoading, setEmployeeHistorySearchLoading] = useState(false);
  const [pendingRecommend, setPendingRecommend] = useState([]);
  const [pendingSanction, setPendingSanction] = useState([]);
  const [leaveTypeUnavailableMessage, setLeaveTypeUnavailableMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const [applyForm, setApplyForm] = useState(createInitialLeaveApplyForm);
  const [submitting, setSubmitting] = useState(false);

  const [actionDialog, setActionDialog] = useState({ open: false, action: null, record: null });

  const daysApplied = useMemo(() => {
    if (!applyForm.from_date || !applyForm.to_date) return 0;
    const start = new Date(applyForm.from_date);
    const end = new Date(applyForm.to_date);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;
    const diffMs = end - start;
    if (diffMs < 0) return 0;
    return Math.floor(diffMs / (1000 * 60 * 60 * 24)) + 1;
  }, [applyForm.from_date, applyForm.to_date]);

  const selectedBalance = balances?.[applyForm.leave_type_code];
  const leaveTypeOptions = useMemo(
    () =>
      leaveTypes.map((lt) => {
        const code = lt.leave_code || lt.code;
        return {
          value: code,
          label: lt.description ? `${lt.description} (${code})` : code,
          search: `${lt.description || ""} ${code || ""}`,
        };
      }),
    [leaveTypes]
  );
  const employeeHistoryLeaveTypeOptions = useMemo(() => {
    const seen = new Set();

    return selectedEmployeeLeaves
      .map((leave) => leave.leave_type_code)
      .filter((code) => {
        if (!code || seen.has(code)) return false;
        seen.add(code);
        return true;
      })
      .sort((left, right) => left.localeCompare(right))
      .map((code) => ({
        value: code,
        label: LEAVE_TYPE_LABELS[code] ? `${LEAVE_TYPE_LABELS[code]} (${code})` : code,
        search: `${LEAVE_TYPE_LABELS[code] || ""} ${code}`,
      }));
  }, [selectedEmployeeLeaves]);
  const filteredSelectedEmployeeLeaves = useMemo(() => {
    if (!selectedEmployeeLeaveType) return selectedEmployeeLeaves;
    return selectedEmployeeLeaves.filter((leave) => leave.leave_type_code === selectedEmployeeLeaveType);
  }, [selectedEmployeeLeaveType, selectedEmployeeLeaves]);
  const selectedEmployeeLeaveSummary = useMemo(() => {
    const summary = {
      totalApplications: selectedEmployeeLeaves.length,
      totalDays: 0,
      sanctionedCount: 0,
      pendingCount: 0,
      rejectedCount: 0,
      cancelledCount: 0,
      leaveTypeCounts: {},
    };

    selectedEmployeeLeaves.forEach((leave) => {
      const leaveTypeCode = leave.leave_type_code || "Unknown";
      summary.totalDays += Number(leave.days_applied) || 0;
      summary.leaveTypeCounts[leaveTypeCode] = (summary.leaveTypeCounts[leaveTypeCode] || 0) + 1;

      if (leave.status === "SANCTIONED") {
        summary.sanctionedCount += 1;
      } else if (leave.status === "SUBMITTED" || leave.status === "RECOMMENDED") {
        summary.pendingCount += 1;
      } else if (leave.status === "REJECTED") {
        summary.rejectedCount += 1;
      } else if (leave.status === "CANCELLED") {
        summary.cancelledCount += 1;
      }
    });

    summary.leaveTypeEntries = Object.entries(summary.leaveTypeCounts)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([leaveTypeCode, count]) => ({ leaveTypeCode, count }));

    return summary;
  }, [selectedEmployeeLeaves]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (isEmployeeSelf && (canApply || canReadOwn)) {
        const profileRes = await essAPI.getMyProfile().catch((error) => ({ data: null, error }));
        const profileData = profileRes.data || null;
        setProfile(profileData);

        let leaveTypeError = null;

        if (user?.employee_id) {
          const balanceRes = await leaveAPI.getBalances(user.employee_id).catch((error) => ({
            data: { balances: {} },
            error,
          }));
          const fetchedBalances = extractBalanceMap(balanceRes);
          setBalances(fetchedBalances);
          setLeaveTypes(Object.values(fetchedBalances));
          leaveTypeError = balanceRes.error || null;
          setLeaveTypeUnavailableMessage(
            Object.keys(fetchedBalances).length > 0
              ? ""
              : getLeaveTypeUnavailableMessage({
                  userEmployeeId: user.employee_id,
                  profile: profileData,
                  errorOrDetail: leaveTypeError || profileRes.error,
                })
          );
        } else {
          setBalances({});
          setLeaveTypes([]);
          setLeaveTypeUnavailableMessage(
            getLeaveTypeUnavailableMessage({ profile: profileData, errorOrDetail: profileRes.error })
          );
        }

        if (canReadOwn) {
          const myRes = await leaveAPI.listMy().catch(() => ({ data: [] }));
          setMyLeaves(myRes.data || []);
        }
      }

      if (canRecommend) {
        const pendingRes = await leaveAPI.list({ status: "SUBMITTED" }).catch(() => ({ data: [] }));
        setPendingRecommend(pendingRes.data || []);
      }
      if (canSanction) {
        const pendingRes = await leaveAPI.list({ status: "RECOMMENDED" }).catch(() => ({ data: [] }));
        setPendingSanction(pendingRes.data || []);
      }
      if (selectedEmployeeId && canViewEmployeeHistory) {
        const [employeeHistoryRes, empBalanceRes, empIdentity] = await Promise.all([
          leaveAPI.list({ employee_id: selectedEmployeeId }).catch(() => ({ data: [] })),
          leaveAPI.getBalances(selectedEmployeeId).catch(() => ({})),
          employeeIdentityApi.get(selectedEmployeeId).catch(() => ({ data: null })),
        ]);
        setSelectedEmployeeLeaves(Array.isArray(employeeHistoryRes.data) ? employeeHistoryRes.data : []);
        setSelectedEmployeeBalances(extractBalanceMap(empBalanceRes));
        setSelectedEmployeeInfo(empIdentity?.data || null);
      } else {
        setSelectedEmployeeLeaves([]);
        setSelectedEmployeeBalances({});
        setSelectedEmployeeInfo(null);
      }
    } finally {
      setLoading(false);
    }
  }, [
    canApply,
    canReadOwn,
    canRecommend,
    canSanction,
    canViewEmployeeHistory,
    isEmployeeSelf,
    selectedEmployeeId,
    user?.employee_id,
  ]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!selectedEmployeeId) {
      setSelectedEmployeeLeaveType("");
      return;
    }
    if (
      selectedEmployeeLeaveType
      && !selectedEmployeeLeaves.some((leave) => leave.leave_type_code === selectedEmployeeLeaveType)
    ) {
      setSelectedEmployeeLeaveType("");
    }
  }, [selectedEmployeeId, selectedEmployeeLeaveType, selectedEmployeeLeaves]);

  useEffect(() => {
    let cancelled = false;

    if (!canViewEmployeeHistory || isEmployeeHistoryMode) {
      setEmployeeHistorySearchResults([]);
      setEmployeeHistorySearchLoading(false);
      return () => {
        cancelled = true;
      };
    }

    const normalizedQuery = employeeHistorySearchQuery.trim();
    if (normalizedQuery.length < 2) {
      setEmployeeHistorySearchResults([]);
      setEmployeeHistorySearchLoading(false);
      return () => {
        cancelled = true;
      };
    }

    setEmployeeHistorySearchLoading(true);
    employeeIdentityApi
      .list({ search: normalizedQuery, page: 1, page_size: 8 })
      .then((response) => {
        if (cancelled) return;
        const identities = Array.isArray(response?.data?.identities) ? response.data.identities : [];
        setEmployeeHistorySearchResults(identities);
      })
      .catch(() => {
        if (cancelled) return;
        setEmployeeHistorySearchResults([]);
      })
      .finally(() => {
        if (!cancelled) {
          setEmployeeHistorySearchLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [canViewEmployeeHistory, employeeHistorySearchQuery, isEmployeeHistoryMode]);

  const openEmployeeHistory = (employeeId) => {
    if (!employeeId) return;
    const nextSearchParams = new URLSearchParams(searchParams);
    nextSearchParams.set("employee_id", employeeId);
    setSearchParams(nextSearchParams);
    setEmployeeHistorySearchQuery("");
    setEmployeeHistorySearchResults([]);
  };

  const handleEmployeeHistoryBack = () => {
    if (employeeHistoryReturnPath) {
      navigate(employeeHistoryReturnPath);
      return;
    }
    navigate(-1);
  };

  const handleApply = async () => {
    if (!applyForm.leave_type_code || !applyForm.from_date || !applyForm.to_date || !applyForm.reason || !applyForm.contact_during_leave) {
      toast.error("Please fill all required fields");
      return;
    }
    if (daysApplied <= 0) {
      toast.error("Invalid date range");
      return;
    }
    const eligibilityMessage = getLeaveEligibilityValidationMessage(applyForm);
    if (eligibilityMessage) {
      toast.error(eligibilityMessage);
      return;
    }
    const supportingDocumentMessage = getLeaveSupportingDocumentValidationMessage(applyForm);
    if (supportingDocumentMessage) {
      toast.error(supportingDocumentMessage);
      return;
    }
    try {
      setSubmitting(true);
      await leaveAPI.apply(buildLeaveApplicationPayload(applyForm));
      toast.success("Leave application submitted");
      setApplyForm(createInitialLeaveApplyForm());
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to submit leave"));
    } finally {
      setSubmitting(false);
    }
  };

  const setApplyFormAttachments = (updater) => {
    setApplyForm((prev) => ({
      ...prev,
      attachments: typeof updater === "function" ? updater(prev.attachments || []) : updater,
    }));
  };

  const openActionDialog = (action, record) => {
    setActionDialog({ open: true, action, record });
  };

  return {
    actionDialog,
    applyForm,
    balances,
    canApply,
    canApplySelf,
    canReadOwn,
    canRecommend,
    canSanction,
    canViewEmployeeHistory,
    daysApplied,
    employeeHistoryLeaveTypeOptions,
    employeeHistorySearchLoading,
    employeeHistorySearchQuery,
    employeeHistorySearchResults,
    fetchData,
    filteredSelectedEmployeeLeaves,
    handleApply,
    handleEmployeeHistoryBack,
    isEmployeeHistoryMode,
    isEmployeeSelf,
    leaveTypeOptions,
    leaveTypeUnavailableMessage,
    leaveTypes,
    loading,
    myLeaves,
    openActionDialog,
    openEmployeeHistory,
    pendingRecommend,
    pendingSanction,
    profile,
    selectedBalance,
    selectedEmployeeBalances,
    selectedEmployeeId,
    selectedEmployeeInfo,
    selectedEmployeeLeaveSummary,
    selectedEmployeeLeaveType,
    selectedEmployeeLeaves,
    setActionDialog,
    setApplyForm,
    setApplyFormAttachments,
    setEmployeeHistorySearchQuery,
    setSelectedEmployeeLeaveType,
    submitting,
  };
};
