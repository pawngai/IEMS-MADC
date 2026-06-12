import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "@/modules/identity_access";
import { usePermissions } from "@/modules/identity_access";
import { Permissions } from "@/platform/permissions";
import { serviceBookRecordsAPI } from "@/modules/service_book/records/api/serviceBookRecordsApi";
import { serviceRecordsApi } from "@/modules/service_book/records/api/serviceRecordsApi";
import { toast } from "sonner";

const isRegularServiceBookRecordsEmployee = (identityInfo) => {
  if (identityInfo && "eligible_for_service_book" in identityInfo) {
    return Boolean(identityInfo.eligible_for_service_book);
  }
  const employmentType = String(
    identityInfo?.current_employment_type_code || identityInfo?.employment_type || identityInfo?.employment_type_code || ""
  )
    .trim()
    .toUpperCase();
  return employmentType === "REGULAR" || employmentType === "REG";
};

const formatServiceBookRecordsError = (error) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  if (detail?.error) return detail.error;
  return error?.message || "Failed to load Service Book records";
};

const safeCall = (operation) => {
  try {
    return Promise.resolve(operation()).catch(() => ({ data: null }));
  } catch {
    return Promise.resolve({ data: null });
  }
};

export function useServiceBookRecordsPageState() {
  const { employeeId } = useParams();
  const { user } = useAuth();
  const { can } = usePermissions();

  const targetEmployeeId = employeeId || user?.employee_id;

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [identityInfo, setIdentityInfo] = useState(null);

  // Dialog state
  const [showRecordDialog, setShowRecordDialog] = useState(false);
  const [correctTarget, setCorrectTarget] = useState(null);
  const [voidTarget, setVoidTarget] = useState(null);
  const [attachTarget, setAttachTarget] = useState(null);

  const serviceBookRecordsEligible =
    identityInfo == null ? null : isRegularServiceBookRecordsEmployee(identityInfo);

  const canCreate =
    serviceBookRecordsEligible === false
      ? false
      : can(Permissions.SERVICE_BOOK_ENTRY_CREATE);
  const canCorrectOrVoid =
    serviceBookRecordsEligible === false
      ? false
      : can(Permissions.SERVICE_BOOK_SUPERSEDE) ||
        can(Permissions.SERVICE_BOOK_ENTRY_APPROVE);
  const canAttachDoc =
    serviceBookRecordsEligible === false
      ? false
      : can(Permissions.SERVICE_BOOK_ENTRY_CREATE) ||
        can(Permissions.SERVICE_BOOK_ENTRY_VERIFY) ||
        can(Permissions.SERVICE_BOOK_ENTRY_APPROVE);

  const loadEvents = useCallback(async () => {
    if (!targetEmployeeId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await serviceBookRecordsAPI.getEventStream(targetEmployeeId);
      const data = res.data || res;
      setEvents(Array.isArray(data) ? data : data.events || []);
    } catch (err) {
      const message = formatServiceBookRecordsError(err);
      if (message.toLowerCase().includes("regular employees")) {
        setIdentityInfo((current) => current || { eligible_for_service_book: false });
        setError(null);
        setEvents([]);
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }, [targetEmployeeId]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  useEffect(() => {
    let active = true;
    if (!targetEmployeeId) {
      setIdentityInfo(null);
      return undefined;
    }

    const loadIdentityInfo = async () => {
      const identityResponse = await safeCall(() => serviceBookRecordsAPI.getEmployeeIdentity(targetEmployeeId));
      if (!active) return;

      const identityData = identityResponse?.data || null;
      setIdentityInfo(identityData);

      const summaryResponse = await safeCall(() => serviceRecordsApi.getServiceSummary(targetEmployeeId));
      if (!active) return;

      const summaryData = summaryResponse?.data || null;
      if (summaryData && Object.keys(summaryData).length > 0) {
        setIdentityInfo({ ...(identityData || {}), ...summaryData });
      }
    };

    loadIdentityInfo()
      .catch(() => {
        if (active) setIdentityInfo(null);
      });

    return () => {
      active = false;
    };
  }, [targetEmployeeId]);

  const employeeName =
    identityInfo?.name_in_block_letters ||
    identityInfo?.full_name ||
    user?.name ||
    null;
  const employeeCode = identityInfo?.employee_code || null;

  const handleRecordSuccess = () => {
    setShowRecordDialog(false);
    toast.success("Service Book record created successfully");
    loadEvents();
  };

  const handleCorrectSuccess = () => {
    setCorrectTarget(null);
    toast.success("Service Book record corrected");
    loadEvents();
  };

  const handleVoidSuccess = () => {
    setVoidTarget(null);
    toast.success("Service Book record voided");
    loadEvents();
  };

  const handleAttachSuccess = () => {
    setAttachTarget(null);
    toast.success("Document attached");
    loadEvents();
  };

  return {
    targetEmployeeId,
    events,
    loading,
    error,
    loadEvents,
    // Dialog state
    showRecordDialog,
    setShowRecordDialog,
    correctTarget,
    setCorrectTarget,
    voidTarget,
    setVoidTarget,
    attachTarget,
    setAttachTarget,
    employeeName,
    employeeCode,
    serviceBookRecordsEligible,
    // Permissions
    canCreate,
    canCorrectOrVoid,
    canAttachDoc,
    // Callbacks
    handleRecordSuccess,
    handleCorrectSuccess,
    handleVoidSuccess,
    handleAttachSuccess,
  };
}
