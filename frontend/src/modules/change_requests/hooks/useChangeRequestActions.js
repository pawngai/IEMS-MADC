import { useCallback, useState } from "react";
import { essAPI } from "@/modules/ess";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { toast } from "sonner";

export function useChangeRequestActions({ onAfterAction }) {
  const [submitting, setSubmitting] = useState(false);
  const [cancellingId, setCancellingId] = useState(null);

  const submitChangeRequest = useCallback(
    async (payload) => {
      setSubmitting(true);
      try {
        await essAPI.submitChangeRequest(payload);
        toast.success("Change request submitted successfully");
        onAfterAction?.();
        return true;
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Failed to submit change request"));
        return false;
      } finally {
        setSubmitting(false);
      }
    },
    [onAfterAction]
  );

  const cancelChangeRequest = useCallback(
    async (requestId) => {
      setCancellingId(requestId);
      try {
        await essAPI.cancelChangeRequest(requestId);
        toast.success("Change request cancelled");
        onAfterAction?.();
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Failed to cancel request"));
      } finally {
        setCancellingId(null);
      }
    },
    [onAfterAction]
  );

  return {
    submitting,
    cancellingId,
    submitChangeRequest,
    cancelChangeRequest,
  };
}

export default useChangeRequestActions;
