import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "@/contexts/identity";
import { MAIN } from "@/shared/lib/routes";
import { toast } from "sonner";
import { serviceBookOpeningApi } from "@/contexts/service_book/opening/api/serviceBookOpeningApi";
import { resolveOpeningPermissions } from "@/contexts/service_book/opening/model/openingPermissions";
import { OPENING_STATUS, normalizeOpeningStatus } from "@/contexts/service_book/opening/model/openingStatus";
import {
  buildOpeningEligibility,
  getOpeningCompletion,
} from "@/contexts/service_book/opening/services/openingDomainService";
import {
  mapDraftToOpeningPayload,
  mapIdentityProfileToPartIDefaults,
  normalizeOpeningDraft,
} from "@/contexts/service_book/opening/services/openingPayloadMapper";

const safeData = (response) => response?.data || response || null;

const readOpeningError = (error) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  if (detail?.error) return detail.error;
  return error?.message || "Failed to load Service Book Opening";
};

const safeCall = async (operation) => {
  try {
    return safeData(await operation());
  } catch {
    return null;
  }
};

export const useServiceBookOpeningPageState = () => {
  const { employeeId } = useParams();
  const navigate = useNavigate();
  const { user, can } = useAuth();
  const targetEmployeeId = employeeId || user?.employee_id;

  const [identity, setIdentity] = useState(null);
  const [profile, setProfile] = useState(null);
  const [draft, setDraft] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingDocument, setUploadingDocument] = useState(false);
  const [acting, setActing] = useState("");
  const [error, setError] = useState(null);
  const [remarks, setRemarks] = useState("");

  const eligibilitySource = identity || profile || draft;
  const resolvedEmployeeId =
    identity?.employee_id ||
    profile?.employee_id ||
    draft?.employee_id ||
    draft?.parts?.part_i?.employee_id ||
    targetEmployeeId;
  const eligibility = useMemo(() => buildOpeningEligibility(eligibilitySource), [eligibilitySource]);
  const status = normalizeOpeningStatus(draft?.status);
  const completion = useMemo(() => getOpeningCompletion(draft), [draft]);
  const permissions = useMemo(
    () => resolveOpeningPermissions({ can, status, eligible: eligibility.eligible }),
    [can, eligibility.eligible, status]
  );

  const load = useCallback(async () => {
    if (!targetEmployeeId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [identityData, profileData, defaultsData, openingData] = await Promise.all([
        safeCall(() => serviceBookOpeningApi.getEmployeeIdentity(targetEmployeeId)),
        safeCall(() => serviceBookOpeningApi.getEmployeeProfile(targetEmployeeId)),
        safeCall(() => serviceBookOpeningApi.getPartIDefaults(targetEmployeeId)),
        safeCall(() => serviceBookOpeningApi.getForEmployee(targetEmployeeId)),
      ]);

      const partIDefaults =
        defaultsData?.part_i ||
        defaultsData ||
        mapIdentityProfileToPartIDefaults({ identity: identityData, profile: profileData });

      setIdentity(identityData);
      setProfile(profileData);
      setDraft(
        normalizeOpeningDraft({
          employeeId: targetEmployeeId,
          opening: openingData || { status: OPENING_STATUS.NOT_STARTED },
          partIDefaults,
        })
      );
    } catch (loadError) {
      setError(readOpeningError(loadError));
    } finally {
      setLoading(false);
    }
  }, [targetEmployeeId]);

  useEffect(() => {
    load();
  }, [load]);

  const updatePart = (partId, values) => {
    setDraft((current) => ({
      ...(current || {}),
      status: current?.status === OPENING_STATUS.NOT_STARTED ? OPENING_STATUS.DRAFT : current?.status,
      parts: {
        ...(current?.parts || {}),
        [partId]: {
          ...(current?.parts?.[partId] || {}),
          ...(values || {}),
        },
      },
    }));
  };

  const saveDraft = async () => {
    if (!resolvedEmployeeId || !draft) return;
    setSaving(true);
    try {
      const payload = mapDraftToOpeningPayload({ employeeId: resolvedEmployeeId, draft });
      const response =
        status === OPENING_STATUS.NOT_STARTED
          ? await serviceBookOpeningApi.createDraft(payload)
          : await serviceBookOpeningApi.updateDraft(resolvedEmployeeId, payload);
      const saved = safeData(response);
      setDraft((current) =>
        normalizeOpeningDraft({
          employeeId: resolvedEmployeeId,
          opening: saved || { ...current, status: OPENING_STATUS.DRAFT },
          partIDefaults: current?.parts?.part_i,
        })
      );
      toast.success("Service Book Opening draft saved");
    } catch (saveError) {
      toast.error(readOpeningError(saveError));
    } finally {
      setSaving(false);
    }
  };

  const runWorkflowAction = async (action) => {
    if (!resolvedEmployeeId) return;
    setActing(action);
    try {
      const response = await serviceBookOpeningApi[action](resolvedEmployeeId, remarks);
      const next = safeData(response);
      setDraft((current) => ({
        ...(current || {}),
        ...(next || {}),
        status: next?.status || next?.workflow_status || current?.status,
      }));
      setRemarks("");
      toast.success("Service Book Opening workflow updated");
    } catch (actionError) {
      toast.error(readOpeningError(actionError));
    } finally {
      setActing("");
    }
  };

  const uploadDocument = async (file, metadata = {}) => {
    if (!resolvedEmployeeId || !file) return;
    setUploadingDocument(true);
    try {
      const uploadResponse = await serviceBookOpeningApi.uploadLinkedDocument(file, {
        employee_id: resolvedEmployeeId,
        source_context: "service_book.opening",
        document_type: metadata.documentType || "opening",
      });
      const uploaded = safeData(uploadResponse);
      const documentId = uploaded?.document_id || uploaded?.id || uploaded?.file_id;
      if (!documentId) {
        throw new Error("Document uploaded, but no document ID was returned");
      }
      const attachResponse = await serviceBookOpeningApi.attachDocument(resolvedEmployeeId, {
        document_id: documentId,
        document_type: metadata.documentType || "opening",
        name: uploaded?.filename || uploaded?.name || file.name,
        field_key: metadata.fieldKey,
        field_label: metadata.fieldLabel,
        part_id: metadata.partId,
      });
      const next = safeData(attachResponse);
      setDraft((current) =>
        normalizeOpeningDraft({
          employeeId: resolvedEmployeeId,
          opening: next || current,
          partIDefaults: current?.parts?.part_i,
        })
      );
      toast.success("Opening document attached");
    } catch (uploadError) {
      toast.error(readOpeningError(uploadError));
    } finally {
      setUploadingDocument(false);
    }
  };

  const viewServiceBook = () => {
    if (resolvedEmployeeId) navigate(MAIN.SERVICE_BOOK_EMP(resolvedEmployeeId));
  };

  return {
    targetEmployeeId,
    employeeFileId:
      identity?.employee_id ||
      profile?.employee_id ||
      draft?.employee_id ||
      draft?.parts?.part_i?.employee_id ||
      null,
    employeeName:
      draft?.parts?.part_i?.name_in_block_letters ||
      draft?.parts?.part_i?.full_name ||
      identity?.name_in_block_letters ||
      identity?.full_name ||
      profile?.full_name ||
      targetEmployeeId,
    employeeCode: draft?.parts?.part_i?.employee_code || identity?.employee_code || profile?.employee_code,
    identity,
    profile,
    draft,
    loading,
    saving,
    uploadingDocument,
    acting,
    error,
    remarks,
    setRemarks,
    eligibility,
    status,
    completion,
    permissions,
    updatePart,
    saveDraft,
    runWorkflowAction,
    uploadDocument,
    reload: load,
    viewServiceBook,
  };
};

export default useServiceBookOpeningPageState;
