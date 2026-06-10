import { useState, useMemo, useCallback, useRef } from "react";
import { toast } from "sonner";
import { versionedMastersAPI } from "@/contexts/masters";
import { getApiErrorMessage } from "@/shared/lib/utils";
import {
  SYSTEM_MANAGED_MASTERS,
  SERVICE_EVENT_PARTS,
} from "@/contexts/admin/pages/systemAdminConsole.constants";
import {
  buildMasterMetadata,
  createEmptyMasterMetadata,
  validateMasterMetadata,
} from "@/contexts/admin/model/policyMasterForms";

const EMPTY_MASTER_DATA = { code: "", name: "", description: "", metadata: "" };

const createDefaultServiceEventMeta = () => ({
  event_code: "",
  service_book_part: "II-A",
  requires_order_number: true,
  affects_pay: false,
  affects_posting: false,
});

const buildServiceEventMetadata = (meta) => ({
  event_code: meta.event_code?.trim() || "",
  service_book_part: meta.service_book_part || "",
  requires_order_number: !!meta.requires_order_number,
  affects_pay: !!meta.affects_pay,
  affects_posting: !!meta.affects_posting,
});

const usePolicyMasterAdmin = () => {
  const loadRequestSeqRef = useRef(0);
  const [selectedMasterType, setSelectedMasterType] = useState(null);
  const [masterRecords, setMasterRecords] = useState([]);
  const [masterLoading, setMasterLoading] = useState(false);
  const [showVersionHistory, setShowVersionHistory] = useState({ open: false, code: null, history: [] });
  const [editMasterDialog, setEditMasterDialog] = useState({ open: false, record: null });
  const [editMasterData, setEditMasterData] = useState({ name: "", description: "", reason: "" });
  const [createMasterDialog, setCreateMasterDialog] = useState(false);
  const [newMasterData, setNewMasterData] = useState(EMPTY_MASTER_DATA);
  const [newMasterMetadataForm, setNewMasterMetadataForm] = useState(createEmptyMasterMetadata(null));
  const [masterSearch, setMasterSearch] = useState("");
  const [showInactiveMasters, setShowInactiveMasters] = useState(false);
  const [deprecateDialog, setDeprecateDialog] = useState({ open: false, record: null });
  const [deprecateReason, setDeprecateReason] = useState("");
  const [masterRecordCounts, setMasterRecordCounts] = useState({});
  const [masterReferenceRecords, setMasterReferenceRecords] = useState({});

  const [newServiceEventMeta, setNewServiceEventMeta] = useState(createDefaultServiceEventMeta);
  const [editServiceEventMeta, setEditServiceEventMeta] = useState({
    event_code: "",
    service_book_part: "II-A",
    requires_order_number: true,
    affects_pay: false,
    affects_posting: false,
  });

  const isServiceEventMaster = selectedMasterType === "service_event_type";
  const selectedMasterConfig = useMemo(
    () => SYSTEM_MANAGED_MASTERS.find((master) => master.id === selectedMasterType) || null,
    [selectedMasterType],
  );
  const isSelectedMasterReadOnly = !!selectedMasterConfig?.readOnly;

  const filteredMasterRecords = useMemo(() => {
    let records = masterRecords;
    if (!showInactiveMasters) records = records.filter((r) => r.is_active);
    const q = masterSearch.trim().toLowerCase();
    if (q) records = records.filter((r) => [r.code, r.name, r.description].filter(Boolean).join(" ").toLowerCase().includes(q));
    return records;
  }, [masterRecords, masterSearch, showInactiveMasters]);

  const masterReferenceOptions = useMemo(() => {
    const toOptions = (masterType) =>
      (masterReferenceRecords[masterType] || []).map((record) => ({
        value: record.code,
        label: record.name ? `${record.code} - ${record.name}` : record.code,
      }));

    return {
      departmentOptions: toOptions("department"),
      employmentTypeOptions: toOptions("employment_type"),
      payLevelOptions: toOptions("pay_level"),
      serviceGroupOptions: toOptions("service_group"),
    };
  }, [masterReferenceRecords]);

  const resetCreateMasterState = useCallback((masterType = selectedMasterType) => {
    setNewMasterData(EMPTY_MASTER_DATA);
    setNewMasterMetadataForm(createEmptyMasterMetadata(masterType));
    setNewServiceEventMeta(createDefaultServiceEventMeta());
  }, [selectedMasterType]);

  const openCreateMasterDialog = useCallback(() => {
    if (selectedMasterConfig?.readOnly) {
      toast.error(selectedMasterConfig.readOnlyReason || "This master is read-only.");
      return;
    }
    resetCreateMasterState(selectedMasterType);
    setCreateMasterDialog(true);
  }, [resetCreateMasterState, selectedMasterConfig, selectedMasterType]);

  const preloadMasterCounts = useCallback(async () => {
    try {
      const results = await Promise.allSettled(
        SYSTEM_MANAGED_MASTERS.map(async (master) => {
          const res = await versionedMastersAPI.list(master.id, false);
          return { id: master.id, records: res.data?.records || [] };
        })
      );
      const counts = {};
      const references = {};
      results.forEach((result) => {
        if (result.status !== "fulfilled") return;
        const activeRecords = result.value.records.filter((record) => record.is_active);
        counts[result.value.id] = activeRecords.length;
        references[result.value.id] = activeRecords;
      });
      setMasterRecordCounts(counts);
      setMasterReferenceRecords((prev) => ({ ...prev, ...references }));
    } catch {
      // non-critical
    }
  }, []);

  const loadMasterRecords = useCallback(async (masterType) => {
    const requestSeq = loadRequestSeqRef.current + 1;
    loadRequestSeqRef.current = requestSeq;

    setMasterLoading(true);
    setSelectedMasterType(masterType);
    setMasterSearch("");
    try {
      const res = await versionedMastersAPI.list(masterType, true);
      if (requestSeq !== loadRequestSeqRef.current) return;
      const records = res.data?.records || [];
      setMasterRecords(records);
      setMasterRecordCounts((prev) => ({ ...prev, [masterType]: records.filter((record) => record.is_active).length }));
      setMasterReferenceRecords((prev) => ({ ...prev, [masterType]: records.filter((record) => record.is_active) }));
    } catch {
      if (requestSeq !== loadRequestSeqRef.current) return;
      toast.error("Failed to load master records");
    } finally {
      if (requestSeq === loadRequestSeqRef.current) {
        setMasterLoading(false);
      }
    }
  }, []);

  const loadVersionHistory = useCallback(async (masterType, code) => {
    try {
      const res = await versionedMastersAPI.getHistory(masterType, code);
      setShowVersionHistory({ open: true, code, history: res.data?.versions || [] });
    } catch {
      toast.error("Failed to load version history");
    }
  }, []);

  const submitMasterUpdate = useCallback(async () => {
    if (isSelectedMasterReadOnly) {
      toast.error(selectedMasterConfig?.readOnlyReason || "This master is read-only.");
      return;
    }
    if (editMasterData.reason.length < 10) {
      toast.error("Reason must be at least 10 characters");
      return;
    }

    try {
      const payload = {
        name: editMasterData.name,
        description: editMasterData.description,
        reason: editMasterData.reason,
      };

      if (selectedMasterType === "service_event_type") {
        if (!editServiceEventMeta.event_code?.trim() || !editServiceEventMeta.service_book_part) {
          toast.error("Event code and Service Book Part are required");
          return;
        }
        payload.metadata = buildServiceEventMetadata(editServiceEventMeta);
      }

      await versionedMastersAPI.update(selectedMasterType, editMasterDialog.record.code, payload);
      toast.success("Master updated (new version created)");
      setEditMasterDialog({ open: false, record: null });
      loadMasterRecords(selectedMasterType);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to update master"));
    }
  }, [editMasterData, selectedMasterType, editServiceEventMeta, editMasterDialog, loadMasterRecords, isSelectedMasterReadOnly, selectedMasterConfig]);

  const submitMasterCreate = useCallback(async () => {
    if (!selectedMasterType) {
      toast.error("Select a master type first");
      return;
    }
    if (isSelectedMasterReadOnly) {
      toast.error(selectedMasterConfig?.readOnlyReason || "This master is read-only.");
      return;
    }
    if (!newMasterData.code || !newMasterData.name) {
      toast.error("Code and Name are required");
      return;
    }

    let metadata = {};
    if (selectedMasterType === "service_event_type") {
      if (!newServiceEventMeta.event_code?.trim() || !newServiceEventMeta.service_book_part) {
        toast.error("Event code and Service Book Part are required");
        return;
      }
      metadata = buildServiceEventMetadata(newServiceEventMeta);
    } else {
      const metadataError = validateMasterMetadata(selectedMasterType, newMasterMetadataForm, newMasterData.code);
      if (metadataError) {
        toast.error(metadataError);
        return;
      }
      metadata = buildMasterMetadata(selectedMasterType, newMasterMetadataForm, newMasterData.code);
    }

    try {
      await versionedMastersAPI.create(selectedMasterType, {
        code: newMasterData.code.trim().toUpperCase(),
        name: newMasterData.name.trim(),
        description: newMasterData.description?.trim() || undefined,
        metadata,
      });
      toast.success("Master record created");
      setCreateMasterDialog(false);
      resetCreateMasterState(selectedMasterType);
      loadMasterRecords(selectedMasterType);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to create master"));
    }
  }, [selectedMasterType, newMasterData, newMasterMetadataForm, newServiceEventMeta, loadMasterRecords, resetCreateMasterState, isSelectedMasterReadOnly, selectedMasterConfig]);

  const getServiceEventMeta = useCallback((record) => {
    const meta = record?.metadata || {};
    return {
      event_code: meta.event_code || record?.event_code || "",
      service_book_part: meta.service_book_part || record?.service_book_part || "II-A",
      requires_order_number: meta.requires_order_number ?? record?.requires_order_number ?? true,
      affects_pay: meta.affects_pay ?? record?.affects_pay ?? false,
      affects_posting: meta.affects_posting ?? record?.affects_posting ?? false,
    };
  }, []);

  const handleDeprecateMaster = useCallback(async () => {
    if (isSelectedMasterReadOnly) {
      toast.error(selectedMasterConfig?.readOnlyReason || "This master is read-only.");
      return;
    }
    if (deprecateReason.length < 10) {
      toast.error("Reason must be at least 10 characters");
      return;
    }

    try {
      await versionedMastersAPI.deprecate(selectedMasterType, deprecateDialog.record.code, deprecateReason);
      toast.success(`Record '${deprecateDialog.record.code}' deprecated`);
      setDeprecateDialog({ open: false, record: null });
      setDeprecateReason("");
      loadMasterRecords(selectedMasterType);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to deprecate record"));
    }
  }, [deprecateReason, selectedMasterType, deprecateDialog, loadMasterRecords, isSelectedMasterReadOnly, selectedMasterConfig]);

  return {
    selectedMasterType,
    masterRecords,
    masterLoading,
    showVersionHistory,
    setShowVersionHistory,
    editMasterDialog,
    setEditMasterDialog,
    editMasterData,
    setEditMasterData,
    createMasterDialog,
    setCreateMasterDialog,
    openCreateMasterDialog,
    newMasterData,
    setNewMasterData,
    newMasterMetadataForm,
    setNewMasterMetadataForm,
    masterSearch,
    setMasterSearch,
    showInactiveMasters,
    setShowInactiveMasters,
    deprecateDialog,
    setDeprecateDialog,
    deprecateReason,
    setDeprecateReason,
    masterRecordCounts,
    masterReferenceOptions,
    newServiceEventMeta,
    setNewServiceEventMeta,
    editServiceEventMeta,
    setEditServiceEventMeta,
    isServiceEventMaster,
    isSelectedMasterReadOnly,
    selectedMasterConfig,
    filteredMasterRecords,
    preloadMasterCounts,
    loadMasterRecords,
    loadVersionHistory,
    submitMasterUpdate,
    submitMasterCreate,
    getServiceEventMeta,
    handleDeprecateMaster,
    SYSTEM_MANAGED_MASTERS,
    SERVICE_EVENT_PARTS,
  };
};

export default usePolicyMasterAdmin;
