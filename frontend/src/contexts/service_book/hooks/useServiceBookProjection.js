import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  rebuildServiceBookProjection,
} from "@/contexts/service_book/services/serviceBookDomainService";
import { projectionAPI } from "@/contexts/service_book/api/projectionApi";

const extractErrorMessage = (err) => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (detail && typeof detail === "object") {
    if (typeof detail.message === "string" && detail.message.trim()) return detail.message;
    if (typeof detail.error === "string" && detail.error.trim()) return detail.error;
  }
  if (typeof err?.response?.data?.message === "string" && err.response.data.message.trim()) {
    return err.response.data.message;
  }
  return "Failed to load Service Book";
};

export function useServiceBookProjection({ employeeId, canRead, statuses }) {
  const [serviceBook, setServiceBook] = useState(null);
  const [partsInfo, setPartsInfo] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [notApplicable, setNotApplicable] = useState(null);

  const loadServiceBook = useCallback(async () => {
    if (!employeeId || !canRead) {
      setIsLoading(false);
      return;
    }
    try {
      setIsLoading(true);
      setNotApplicable(null);
      const res = await rebuildServiceBookProjection({
        employeeId,
        employeeOrType: "REGULAR",
        statuses,
      });
      setServiceBook(res.data);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const detailError = detail?.error;
      const detailMessage = detail?.message;
      const isNotApplicable =
        err?.response?.status === 403 &&
        (detailError === "Service Book not applicable" ||
          (typeof detailMessage === "string" &&
            detailMessage.toLowerCase().includes("service book is only maintained for regular employees")) ||
          (typeof detail === "string" && detail.toLowerCase().includes("service book not applicable")));

      if (isNotApplicable) {
        setNotApplicable(
          typeof detail === "object"
            ? detail
            : {
                error: "Service Book not applicable",
                message: typeof detail === "string" ? detail : "Service Book is not applicable for this employee.",
                employment_type: "N/A",
              }
        );
      } else {
        toast.error(extractErrorMessage(err));
      }
    } finally {
      setIsLoading(false);
    }
  }, [employeeId, canRead, statuses]);

  const loadPartsInfo = useCallback(async () => {
    if (!employeeId || !canRead) return;
    try {
      const res = await projectionAPI.getPartsInfo();
      setPartsInfo(res.data.parts || {});
    } catch {
      // non-fatal; constants can still render labels
    }
  }, [employeeId, canRead]);

  useEffect(() => {
    loadServiceBook();
    loadPartsInfo();
  }, [loadServiceBook, loadPartsInfo]);

  return {
    serviceBook,
    partsInfo,
    isLoading,
    notApplicable,
    reloadServiceBook: loadServiceBook,
  };
}
