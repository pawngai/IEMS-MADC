import { useState, useCallback } from "react";
import { departmentManagementAPI, mastersAPI } from "@/contexts/organization_master";
import { userManagementAPI } from "@/contexts/identity_access";
import { toast } from "sonner";

const useDepartmentRoles = () => {
  const [departments, setDepartments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [designations, setDesignations] = useState([]);
  const [deptEmployees, setDeptEmployees] = useState([]);
  const [loadingDeptEmployees, setLoadingDeptEmployees] = useState(false);
  const [loading, setLoading] = useState(false);
  const [editDialog, setEditDialog] = useState({ open: false, department: null });
  const [logDialog, setLogDialog] = useState({ open: false, department: null, logs: [] });
  const [strengthDialog, setStrengthDialog] = useState({
    open: false,
    department: null,
    rows: [],
    summary: null,
    reason: "",
    loading: false,
  });
  const [saving, setSaving] = useState(false);

  const fetchDepartments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await departmentManagementAPI.list(true);
      setDepartments(res.data?.records || []);
    } catch {
      toast.error("Failed to load departments");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchEmployees = useCallback(async () => {
    try {
      const res = await userManagementAPI.getEmployees({ limit: 500 });
      setEmployees(res.data?.employees || res.data || []);
    } catch {
      /* employees are optional for display enrichment */
    }
  }, []);

  const fetchDesignations = useCallback(async () => {
    try {
      const res = await mastersAPI.getDesignations();
      setDesignations(res.data || []);
    } catch {
      setDesignations([]);
    }
  }, []);

  const fetchDeptEmployees = useCallback(async (departmentCode) => {
    setLoadingDeptEmployees(true);
    try {
      const res = await userManagementAPI.getEmployees({ department: departmentCode, limit: 500 });
      setDeptEmployees(res.data?.employees || res.data || []);
    } catch {
      setDeptEmployees([]);
    } finally {
      setLoadingDeptEmployees(false);
    }
  }, []);

  const openEditDialog = useCallback((dept) => {
    setEditDialog({
      open: true,
      department: dept,
      hod_employee_id: dept.hod_employee_id || "",
      data_entry_employee_id: dept.data_entry_employee_id || "",
      reason: "",
    });
    fetchDeptEmployees(dept.code);
  }, [fetchDeptEmployees]);

  const closeEditDialog = useCallback(() => {
    setEditDialog({ open: false, department: null });
  }, []);

  const saveDepartmentRoles = useCallback(async (code, payload) => {
    setSaving(true);
    try {
      const res = await departmentManagementAPI.update(code, payload);
      const syncInfo = res.data?.authority_sync || {};
      const syncErrors = Object.keys(syncInfo).filter((k) => k.endsWith("_error"));
      if (syncErrors.length > 0) {
        toast.warning("Roles saved with sync warnings", {
          description: syncErrors.map((k) => syncInfo[k]).join("; "),
        });
      } else {
        toast.success("Department roles updated");
      }
      closeEditDialog();
      await fetchDepartments();
    } catch (err) {
      const detail = err.response?.data?.detail || "Failed to update department roles";
      toast.error(detail);
    } finally {
      setSaving(false);
    }
  }, [closeEditDialog, fetchDepartments]);

  const openLogDialog = useCallback(async (dept) => {
    setLogDialog({ open: true, department: dept, logs: [], loading: true });
    try {
      const res = await departmentManagementAPI.getLogs(dept.code, 50);
      setLogDialog((prev) => ({ ...prev, logs: res.data?.logs || [], loading: false }));
    } catch {
      toast.error("Failed to load change log");
      setLogDialog((prev) => ({ ...prev, loading: false }));
    }
  }, []);

  const closeLogDialog = useCallback(() => {
    setLogDialog({ open: false, department: null, logs: [] });
  }, []);

  const openStrengthDialog = useCallback(async (dept) => {
    setStrengthDialog({
      open: true,
      department: dept,
      rows: [],
      summary: null,
      reason: "",
      loading: true,
    });
    try {
      const [strengthRes] = await Promise.all([
        departmentManagementAPI.getSanctionedStrength(dept.code),
        fetchDesignations(),
      ]);
      setStrengthDialog((prev) => ({
        ...prev,
        rows: strengthRes.data?.items || [],
        summary: strengthRes.data || null,
        loading: false,
      }));
    } catch {
      toast.error("Failed to load sanctioned strength");
      setStrengthDialog((prev) => ({ ...prev, loading: false }));
    }
  }, [fetchDesignations]);

  const closeStrengthDialog = useCallback(() => {
    setStrengthDialog({
      open: false,
      department: null,
      rows: [],
      summary: null,
      reason: "",
      loading: false,
    });
  }, []);

  const saveDepartmentStrength = useCallback(async () => {
    const dept = strengthDialog.department;
    if (!dept?.code) return;
    if ((strengthDialog.reason || "").trim().length < 3) {
      toast.error("Reason is required");
      return;
    }

    const payloadRows = (strengthDialog.rows || []).map((row) => {
      const count = Number.parseInt(row.sanctioned_count, 10);
      return {
        designation_code: row.designation_code,
        employment_type: row.employment_type || null,
        sanctioned_count: Number.isNaN(count) ? -1 : count,
        order_number: (row.order_number || "").trim() || null,
        order_date: (row.order_date || "").trim() || null,
        remarks: (row.remarks || "").trim() || null,
      };
    });

    if (payloadRows.some((row) => !row.designation_code)) {
      toast.error("Post is required for every row");
      return;
    }
    if (payloadRows.some((row) => row.sanctioned_count < 0)) {
      toast.error("Sanctioned count must be non-negative");
      return;
    }

    setSaving(true);
    try {
      const res = await departmentManagementAPI.updateSanctionedStrength(dept.code, {
        sanctioned_strength: payloadRows,
        reason: strengthDialog.reason.trim(),
      });
      setStrengthDialog((prev) => ({
        ...prev,
        rows: res.data?.items || [],
        summary: res.data || null,
        reason: "",
      }));
      toast.success("Sanctioned strength updated");
    } catch (err) {
      const detail = err.response?.data?.detail || "Failed to update sanctioned strength";
      toast.error(typeof detail === "string" ? detail : detail.message || "Failed to update sanctioned strength");
    } finally {
      setSaving(false);
    }
  }, [strengthDialog]);

  const resolveEmployeeName = useCallback(
    (employeeId) => {
      if (!employeeId) return null;
      const emp = employees.find(
        (e) => e.employee_id === employeeId || e.id === employeeId
      );
      return emp?.name || emp?.full_name || null;
    },
    [employees]
  );

  return {
    departments,
    employees,
    designations,
    deptEmployees,
    loadingDeptEmployees,
    loading,
    editDialog,
    setEditDialog,
    logDialog,
    strengthDialog,
    setStrengthDialog,
    saving,
    fetchDepartments,
    fetchEmployees,
    openEditDialog,
    closeEditDialog,
    saveDepartmentRoles,
    openLogDialog,
    closeLogDialog,
    openStrengthDialog,
    closeStrengthDialog,
    saveDepartmentStrength,
    resolveEmployeeName,
  };
};

export default useDepartmentRoles;
