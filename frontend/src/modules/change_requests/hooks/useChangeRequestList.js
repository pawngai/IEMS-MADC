import { useCallback, useEffect, useMemo, useState } from "react";
import { essAPI } from "@/modules/ess";
import { serviceBookAPI } from "@/modules/service_book";
import { isServiceBookEligible } from "@/modules/service_book";
import { toast } from "sonner";

const ESS_VISIBLE_SERVICE_BOOK_STATUSES = ["APPROVED", "LOCKED"];

export function useChangeRequestList({ partKeyToCompleteKey }) {
  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState([]);
  const [profile, setProfile] = useState(null);
  const [serviceBook, setServiceBook] = useState(null);

  const serviceBookEligible = useMemo(() => {
    return isServiceBookEligible(profile);
  }, [profile]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [requestsResponse, profileResponse] = await Promise.all([
        essAPI.listMyChangeRequests(),
        essAPI.getMyProfile(),
      ]);

      const profileData = profileResponse?.data || null;
      const completeServiceBookResponse =
        isServiceBookEligible(profileData) && profileData?.employee_id
          ? await serviceBookAPI
              .getComplete(profileData.employee_id, { statuses: ESS_VISIBLE_SERVICE_BOOK_STATUSES })
              .catch(() => null)
          : null;

      const completeServiceBook = completeServiceBookResponse?.data || null;
      const byPart = completeServiceBook
        ? Object.entries(partKeyToCompleteKey || {}).reduce((acc, [partKey, completeKey]) => {
            const value = completeServiceBook?.[completeKey];
            if (value != null) acc[partKey] = value;
            return acc;
          }, {})
        : null;

      setRequests(requestsResponse?.data?.items || []);
      setProfile(profileData);
      setServiceBook(byPart);
    } catch {
      toast.error("Failed to load change requests");
    } finally {
      setLoading(false);
    }
  }, [partKeyToCompleteKey]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return {
    loading,
    requests,
    profile,
    serviceBook,
    serviceBookEligible,
    loadData,
    setRequests,
  };
}

export default useChangeRequestList;
