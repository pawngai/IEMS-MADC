import { useState, useCallback } from "react";
import { toast } from "sonner";
import { seniorityAPI } from "@/modules/seniority/api/seniorityApi";

const useSeniorityAdmin = () => {
  const [lists, setLists] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [availableServices, setAvailableServices] = useState([]);
  const [availableDesignations, setAvailableDesignations] = useState([]);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [transitioning, setTransitioning] = useState(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState("");
  const [serviceFilter, setServiceFilter] = useState("");
  const [listTypeFilter, setListTypeFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("");
  const [pagination, setPagination] = useState({ offset: 0, limit: 50 });

  const fetchOptions = useCallback(async () => {
    try {
      const [svcRes, dsgRes] = await Promise.all([
        seniorityAPI.getServices(),
        seniorityAPI.getDesignations(),
      ]);
      setAvailableServices(svcRes.data || []);
      setAvailableDesignations(dsgRes.data || []);
    } catch { /* silent */ }
  }, []);

  const fetchLists = useCallback(async () => {
    setLoading(true);
    try {
      const res = await seniorityAPI.getLists({
        status: statusFilter || undefined,
        service: serviceFilter || undefined,
        list_type: listTypeFilter || undefined,
        year: yearFilter || undefined,
        limit: pagination.limit,
        offset: pagination.offset,
      });
      setLists(res.data?.items || []);
      setTotal(res.data?.total || 0);
    } catch {
      toast.error("Failed to load seniority lists");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, serviceFilter, listTypeFilter, yearFilter, pagination]);

  const fetchDetail = useCallback(async (listId) => {
    setDetailLoading(true);
    try {
      const res = await seniorityAPI.getListDetail(listId);
      setDetail(res.data || null);
    } catch {
      toast.error("Failed to load seniority list detail");
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const generateList = useCallback(async (service, designationCode, title, listType) => {
    setGenerating(true);
    try {
      const res = await seniorityAPI.generateList({
        service,
        designation_code: designationCode,
        title: title || undefined,
        list_type: listType || "DRAFT",
      });
      toast.success(`Seniority list generated with ${res.data?.total || 0} employees`);
      return res.data;
    } catch (err) {
      const msg = err?.response?.data?.detail || "Failed to generate seniority list";
      toast.error(msg);
      return null;
    } finally {
      setGenerating(false);
    }
  }, []);

  const overrideRanks = useCallback(async (listId, overrides, reason) => {
    try {
      await seniorityAPI.overrideRanks(listId, { overrides, reason });
      toast.success("Ranks updated");
      await fetchDetail(listId);
      return true;
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to update ranks");
      return false;
    }
  }, [fetchDetail]);

  const transition = useCallback(async (action, listId, remarks) => {
    setTransitioning(true);
    try {
      const actions = {
        submit: seniorityAPI.submitList,
        verify: seniorityAPI.verifyList,
        approve: seniorityAPI.approveList,
        reject: seniorityAPI.rejectList,
      };
      const fn = actions[action];
      if (!fn) throw new Error("Unknown action");
      const res = await fn(listId, remarks || undefined);
      toast.success(`List ${res.data?.status || action}`);
      await fetchDetail(listId);
      return true;
    } catch (err) {
      toast.error(err?.response?.data?.detail || `Failed to ${action}`);
      return false;
    } finally {
      setTransitioning(false);
    }
  }, [fetchDetail]);

  const promote = useCallback(async (listId, remarks) => {
    setTransitioning(true);
    try {
      const res = await seniorityAPI.promoteList(listId, remarks || undefined);
      toast.success(`List promoted to ${res.data?.list_type || "next version"}`);
      setDetail(null);
      return res.data;
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to promote list");
      return null;
    } finally {
      setTransitioning(false);
    }
  }, []);

  const exportCSV = useCallback(async (listId) => {
    try {
      const res = await seniorityAPI.exportListCSV(listId);
      if (res?.data) {
        const blob = new Blob([res.data], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `seniority_${listId}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success("CSV downloaded");
      }
    } catch {
      toast.error("Failed to export CSV");
    }
  }, []);

  return {
    lists,
    total,
    loading,
    detail,
    detailLoading,
    generating,
    transitioning,
    availableServices,
    availableDesignations,
    statusFilter,
    setStatusFilter,
    serviceFilter,
    setServiceFilter,
    listTypeFilter,
    setListTypeFilter,
    yearFilter,
    setYearFilter,
    pagination,
    setPagination,
    fetchOptions,
    fetchLists,
    fetchDetail,
    generateList,
    overrideRanks,
    transition,
    promote,
    exportCSV,
    setDetail,
  };
};

export default useSeniorityAdmin;
