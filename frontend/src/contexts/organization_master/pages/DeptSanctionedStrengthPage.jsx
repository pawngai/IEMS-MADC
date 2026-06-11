import { useEffect, useMemo, useState } from "react";
import Layout from "@/app/layout/Layout";
import { departmentPortalAPI } from "@/contexts/organization_master/api/departmentApi";
import { useDepartmentScope } from "@/contexts/organization_master/hooks/useDepartmentScope";
import { mastersAPI } from "@/contexts/organization_master";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { CardSkeleton, PageHeaderSkeleton, StatGridSkeleton, TableSkeleton } from "@/shared/ui/skeletons";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { Textarea } from "@/shared/ui/textarea";
import { AlertTriangle, Building2, CheckCircle2, Plus, RefreshCw, Trash2, Users } from "lucide-react";
import { toast } from "sonner";

const makeKey = () => Math.random().toString(36).slice(2);

const toCode = (value) => String(value || "").trim().toUpperCase();

const toLabel = (record) => {
  const code = toCode(record?.code);
  const name = String(record?.name || record?.description || "").trim();
  if (!code) return "";
  return name ? `${code} - ${name}` : code;
};

const mergeReferencedRecords = (records, referencedCodes) => {
  const activeByCode = new Map();
  const allByCode = new Map();

  (records || []).forEach((record) => {
    const code = toCode(record?.code);
    if (!code) return;
    allByCode.set(code, record);
    if (record?.is_active !== false) activeByCode.set(code, record);
  });

  referencedCodes.forEach((code) => {
    const normalizedCode = toCode(code);
    if (!normalizedCode || activeByCode.has(normalizedCode)) return;
    const referencedRecord = allByCode.get(normalizedCode) || {
      code: normalizedCode,
      name: `${normalizedCode} (inactive)`,
      is_active: false,
      metadata: {},
    };
    activeByCode.set(normalizedCode, referencedRecord);
  });

  return Array.from(activeByCode.values()).sort((left, right) =>
    toLabel(left).localeCompare(toLabel(right))
  );
};

const mergeRecordsByCode = (records, extraRecords = []) => {
  const merged = new Map();

  [...records, ...extraRecords].forEach((record) => {
    const code = toCode(record?.code);
    if (!code) return;
    merged.set(code, record);
  });

  return Array.from(merged.values()).sort((left, right) =>
    toLabel(left).localeCompare(toLabel(right))
  );
};

const EMPTY_ROW = () => ({
  _key: makeKey(),
  designation_code: "",
  service_group_code: "",
  pay_level_code: "",
  sanctioned_count: "0",
  order_number: "",
  order_date: "",
  remarks: "",
});

const getDesignationDerivedCodes = (designationLookup, designationCode) => {
  const designation = designationLookup.get(toCode(designationCode));
  const metadata = designation?.metadata || {};
  return {
    service_group_code: toCode(metadata.service_group_code),
    pay_level_code: toCode(metadata.pay_level_code),
  };
};

const toRowModel = (row, designationLookup = new Map()) => ({
  _key: makeKey(),
  designation_code: row.designation_code || "",
  ...getDesignationDerivedCodes(designationLookup, row.designation_code),
  sanctioned_count: row.sanctioned_count !== undefined ? String(row.sanctioned_count) : "0",
  order_number: row.order_number || "",
  order_date: row.order_date || "",
  remarks: row.remarks || "",
});

const MetricCard = ({ icon: Icon, label, value, hint }) => (
  <Card>
    <CardContent className="flex items-start justify-between p-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
        <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
        <p className="mt-1 text-xs text-slate-500">{hint}</p>
      </div>
      <div className="rounded-lg bg-slate-100 p-2 text-slate-600">
        <Icon className="h-4 w-4" />
      </div>
    </CardContent>
  </Card>
);

const DeptSanctionedStrengthPage = () => {
  const {
    canUseDepartmentPortal,
    canManageSanctionedStrength,
    loading: scopeLoading,
    selectedDepartment,
    selectedDepartmentLabel,
    scopeError,
  } = useDepartmentScope();
  const [rows, setRows] = useState([]);
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [designations, setDesignations] = useState([]);
  const [payLevels, setPayLevels] = useState([]);
  const [serviceGroups, setServiceGroups] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    if (!canUseDepartmentPortal || !selectedDepartment) return;
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setReason("");
      setRows([]);
      setDesignations([]);
      setPayLevels([]);
      setServiceGroups([]);
      setSummary(null);

      try {
        const [strengthRes, desigRes, payLevelRes, serviceGroupRes] = await Promise.all([
          departmentPortalAPI.getSanctionedStrength(),
          mastersAPI.getDesignations(),
          mastersAPI.getPayLevels(),
          mastersAPI.getServiceGroups(),
        ]);
        if (cancelled) return;

        const rawRows = strengthRes.data?.items || [];
        const referencedDesignationCodes = rawRows.map((row) => row.designation_code);
        const mergedDesignations = mergeReferencedRecords(
          desigRes.data || [],
          referencedDesignationCodes
        );
        const designationLookup = new Map(
          mergedDesignations.map((designation) => [toCode(designation.code), designation])
        );
        const currentRows = rawRows.map((row) => toRowModel(row, designationLookup));
        const referencedPayLevelCodes = currentRows.map((row) => row.pay_level_code);
        const referencedServiceGroupCodes = currentRows.map((row) => row.service_group_code);

        setRows(currentRows);
        setDesignations(mergedDesignations);
        setPayLevels(
          mergeReferencedRecords(payLevelRes.data || [], referencedPayLevelCodes)
        );
        setServiceGroups(
          mergeReferencedRecords(serviceGroupRes.data || [], referencedServiceGroupCodes)
        );
        setSummary(strengthRes.data || null);
      } catch (error) {
        if (cancelled) return;
        toast.error(getApiErrorMessage(error, "Failed to load sanctioned strength"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [canUseDepartmentPortal, selectedDepartment]);

  const rowMatchesFilters = (row, designation) => {
    const metadata = designation?.metadata || {};
    const rowServiceGroupCode = toCode(row.service_group_code);
    const rowPayLevelCode = toCode(row.pay_level_code);
    const designationServiceGroupCode = toCode(metadata.service_group_code);
    const designationPayLevelCode = toCode(metadata.pay_level_code);

    return (
      (!rowServiceGroupCode || rowServiceGroupCode === designationServiceGroupCode) &&
      (!rowPayLevelCode || rowPayLevelCode === designationPayLevelCode)
    );
  };

  const getDesignationRecord = (designationCode) =>
    designations.find((designation) => toCode(designation.code) === toCode(designationCode));

  const getFilteredDesignations = (row) => {
    const matchingDesignations = designations.filter((designation) => rowMatchesFilters(row, designation));
    const selectedDesignation = getDesignationRecord(row.designation_code);
    return mergeRecordsByCode(matchingDesignations, selectedDesignation ? [selectedDesignation] : []);
  };

  const updateRow = (key, field, value) => {
    setRows((prev) =>
      prev.map((row) => {
        if (row._key !== key) return row;

        if (field === "designation_code") {
          return {
            ...row,
            designation_code: value,
            ...getDesignationDerivedCodes(
              new Map(designations.map((designation) => [toCode(designation.code), designation])),
              value
            ),
          };
        }

        return { ...row, [field]: value };
      })
    );
  };

  const totals = useMemo(
    () => ({
      sanctioned: Number(summary?.totals?.sanctioned_strength_total || 0),
      filled: Number(summary?.totals?.filled_strength_total || 0),
      vacant: Number(summary?.totals?.vacancy_count || 0),
      over: Number(summary?.totals?.over_strength_count || 0),
    }),
    [summary]
  );

  const reload = async () => {
    setLoading(true);
    try {
      const response = await departmentPortalAPI.getSanctionedStrength();
      const rawRows = response.data?.items || [];
      const designationLookup = new Map(
        designations.map((designation) => [toCode(designation.code), designation])
      );
      setRows(rawRows.map((row) => toRowModel(row, designationLookup)));
      setSummary(response.data || null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to reload sanctioned strength"));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!canManageSanctionedStrength) return;
    if (reason.trim().length < 3) {
      toast.error("Reason is required (min 3 characters)");
      return;
    }

    for (const row of rows) {
      if (!row.designation_code) {
        toast.error("Designation code is required for all rows");
        return;
      }
      const count = parseInt(row.sanctioned_count, 10);
      if (Number.isNaN(count) || count < 0) {
        toast.error("Sanctioned count must be a non-negative integer");
        return;
      }
    }

    const payload = rows.map((row) => ({
      designation_code: row.designation_code,
      employment_type: null,
      sanctioned_count: parseInt(row.sanctioned_count, 10) || 0,
      order_number: row.order_number.trim() || null,
      order_date: row.order_date.trim() || null,
      remarks: row.remarks.trim() || null,
    }));

    setSubmitting(true);
    try {
      const response = await departmentPortalAPI.updateSanctionedStrength({
        sanctioned_strength: payload,
        reason: reason.trim(),
      });
      const designationLookup = new Map(
        designations.map((designation) => [toCode(designation.code), designation])
      );
      setRows((response.data?.items || []).map((row) => toRowModel(row, designationLookup)));
      setSummary(response.data || null);
      setReason("");
      toast.success("Sanctioned strength updated");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to update sanctioned strength"));
    } finally {
      setSubmitting(false);
    }
  };

  if (!canUseDepartmentPortal) {
    return (
      <Layout>
        <div className="flex h-[60vh] flex-col items-center justify-center px-4 text-center">
          <AlertTriangle className="mb-3 h-8 w-8 text-slate-400" />
          <h2 className="text-lg font-semibold text-slate-800">Access Restricted</h2>
          <p className="text-sm text-slate-500">Department Operations Portal is available only for HOD and Data Entry roles.</p>
        </div>
      </Layout>
    );
  }

  if (scopeLoading || loading) {
    return (
      <Layout>
        <div className="mx-auto max-w-7xl space-y-6" data-testid="dept-sanctioned-strength-loading">
          <PageHeaderSkeleton />
          <StatGridSkeleton count={4} />
          <CardSkeleton lines={2} />
          <TableSkeleton rows={6} columns={6} />
        </div>
      </Layout>
    );
  }

  if (scopeError) {
    return (
      <Layout>
        <div className="flex h-[60vh] flex-col items-center justify-center px-4 text-center">
          <AlertTriangle className="mb-3 h-8 w-8 text-amber-500" />
          <h2 className="text-lg font-semibold text-slate-800">Department Not Mapped</h2>
          <p className="text-sm text-slate-500">{scopeError}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mx-auto max-w-7xl space-y-6 animate-fade-in" data-testid="dept-sanctioned-strength-page">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Department Operations Portal</p>
            <h2 className="text-2xl font-bold text-slate-900 sm:text-3xl">Sanctioned Strength</h2>
            <p className="mt-1 text-sm text-slate-500">{selectedDepartmentLabel}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" className="gap-2" onClick={reload} disabled={loading || submitting}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            <Button onClick={handleSubmit} disabled={!canManageSanctionedStrength || submitting || reason.trim().length < 3}>
              {submitting ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <MetricCard icon={Building2} label="Sanctioned Posts" value={totals.sanctioned} hint="Configured establishment" />
          <MetricCard icon={Users} label="Filled Posts" value={totals.filled} hint="Active employee count" />
          <MetricCard icon={AlertTriangle} label="Vacancies" value={totals.vacant} hint="Sanctioned minus filled" />
          <MetricCard icon={CheckCircle2} label="Over Strength" value={totals.over} hint="Filled above sanctioned" />
        </div>

        <Card>
          <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-base">Establishment Plan</CardTitle>
              <p className="text-sm text-slate-500">Department-owned sanctioned-strength configuration by designation.</p>
            </div>
            {!canManageSanctionedStrength && (
              <Badge variant="outline" className="w-fit bg-slate-50 text-slate-600">Read only</Badge>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-[180px]">Post <span className="text-red-500">*</span></TableHead>
                    <TableHead className="min-w-[150px]">Group</TableHead>
                    <TableHead className="min-w-[150px]">Pay Level</TableHead>
                    <TableHead className="min-w-[100px]">Sanctioned <span className="text-red-500">*</span></TableHead>
                    <TableHead className="min-w-[120px]">Order No.</TableHead>
                    <TableHead className="min-w-[120px]">Order Date</TableHead>
                    <TableHead className="min-w-[140px]">Remarks</TableHead>
                    <TableHead className="w-10" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="py-8 text-center text-sm text-slate-500">
                        No rows configured yet. Use Add Row to create the department establishment plan.
                      </TableCell>
                    </TableRow>
                  ) : (
                    rows.map((row) => {
                      const filteredDesignations = getFilteredDesignations(row);
                      return (
                        <TableRow key={row._key}>
                          <TableCell className="p-1">
                            <Select
                              value={row.designation_code}
                              onValueChange={(value) => updateRow(row._key, "designation_code", value)}
                              disabled={!canManageSanctionedStrength}
                            >
                              <SelectTrigger className="h-8 text-xs">
                                <SelectValue placeholder="Select..." />
                              </SelectTrigger>
                              <SelectContent>
                                {filteredDesignations.map((designation) => (
                                  <SelectItem key={designation.code} value={designation.code}>
                                    {toLabel(designation)}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell className="p-1 text-xs text-slate-600">
                            {row.service_group_code || "-"}
                          </TableCell>
                          <TableCell className="p-1 text-xs text-slate-600">
                            {row.pay_level_code || "-"}
                          </TableCell>
                          <TableCell className="p-1">
                            <Input
                              type="number"
                              min={0}
                              value={row.sanctioned_count}
                              onChange={(event) => updateRow(row._key, "sanctioned_count", event.target.value)}
                              className="h-8 w-24 text-xs"
                              disabled={!canManageSanctionedStrength}
                            />
                          </TableCell>
                          <TableCell className="p-1">
                            <Input
                              value={row.order_number}
                              onChange={(event) => updateRow(row._key, "order_number", event.target.value)}
                              className="h-8 text-xs"
                              disabled={!canManageSanctionedStrength}
                            />
                          </TableCell>
                          <TableCell className="p-1">
                            <Input
                              type="date"
                              value={row.order_date}
                              onChange={(event) => updateRow(row._key, "order_date", event.target.value)}
                              className="h-8 text-xs"
                              disabled={!canManageSanctionedStrength}
                            />
                          </TableCell>
                          <TableCell className="p-1">
                            <Input
                              value={row.remarks}
                              onChange={(event) => updateRow(row._key, "remarks", event.target.value)}
                              className="h-8 text-xs"
                              disabled={!canManageSanctionedStrength}
                            />
                          </TableCell>
                          <TableCell className="p-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-red-500 hover:bg-red-50 hover:text-red-700"
                              onClick={() => setRows((prev) => prev.filter((item) => item._key !== row._key))}
                              disabled={!canManageSanctionedStrength}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setRows((prev) => [...prev, EMPTY_ROW()])}
                className="gap-2"
                disabled={!canManageSanctionedStrength}
              >
                <Plus className="h-4 w-4" />
                Add Row
              </Button>
              <p className="text-xs text-slate-500">Designation metadata derives service group and pay level automatically.</p>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-slate-600">
                Reason for change <span className="text-red-500">*</span>
              </Label>
              <Textarea
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Explain the change (for audit trail)..."
                rows={3}
                className="rounded-lg"
                disabled={!canManageSanctionedStrength}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default DeptSanctionedStrengthPage;