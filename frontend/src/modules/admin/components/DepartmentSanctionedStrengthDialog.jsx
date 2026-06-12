import { Plus, Trash2, Building2, Users, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { Textarea } from "@/shared/ui/textarea";

const makeKey = () => Math.random().toString(36).slice(2);
const toCode = (value) => String(value || "").trim().toUpperCase();

const emptyRow = () => ({
  _key: makeKey(),
  designation_code: "",
  employment_type: null,
  sanctioned_count: 0,
  order_number: "",
  order_date: "",
  remarks: "",
});

const rowKey = (row) => row._key || `${row.designation_code}-${row.employment_type || "ALL"}`;

const recordLabel = (record) => {
  const code = toCode(record?.code);
  const name = String(record?.name || record?.description || "").trim();
  return name ? `${code} - ${name}` : code;
};

const Metric = ({ icon: Icon, label, value }) => (
  <div className="flex items-center justify-between rounded-md border bg-slate-50 px-3 py-2">
    <div>
      <p className="text-[11px] font-semibold uppercase text-slate-500">{label}</p>
      <p className="text-lg font-bold text-slate-900">{value}</p>
    </div>
    <Icon className="h-4 w-4 text-slate-500" />
  </div>
);

export default function DepartmentSanctionedStrengthDialog({
  dialog,
  setDialog,
  designations,
  onClose,
  onSave,
  saving,
}) {
  const rows = (dialog.rows || []).map((row) => ({ ...row, _key: rowKey(row) }));
  const totals = dialog.summary?.totals || {};

  const patchRows = (nextRows) => {
    setDialog((prev) => ({ ...prev, rows: nextRows }));
  };

  const updateRow = (key, field, value) => {
    patchRows(rows.map((row) => (row._key === key ? { ...row, [field]: value } : row)));
  };

  const setReason = (reason) => {
    setDialog((prev) => ({ ...prev, reason }));
  };

  return (
    <Dialog open={dialog.open} onOpenChange={(open) => (!open ? onClose() : null)}>
      <DialogContent className="max-w-6xl">
        <DialogHeader>
          <DialogTitle>Sanctioned Strength</DialogTitle>
          <DialogDescription>
            {dialog.department?.name} ({dialog.department?.code})
          </DialogDescription>
        </DialogHeader>

        {dialog.loading ? (
          <div className="py-12 text-center text-sm text-slate-500">Loading sanctioned strength...</div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
              <Metric icon={Building2} label="Sanctioned" value={totals.sanctioned_strength_total || 0} />
              <Metric icon={Users} label="Filled" value={totals.filled_strength_total || 0} />
              <Metric icon={AlertTriangle} label="Vacant" value={totals.vacancy_count || 0} />
              <Metric icon={CheckCircle2} label="Over" value={totals.over_strength_count || 0} />
            </div>

            <div className="overflow-x-auto rounded-md border">
              <Table>
                <TableHeader>
                    <TableRow className="bg-slate-50">
                    <TableHead className="min-w-[220px]">Post</TableHead>
                    <TableHead className="min-w-[110px]">Sanctioned</TableHead>
                    <TableHead className="min-w-[140px]">Order No.</TableHead>
                    <TableHead className="min-w-[140px]">Order Date</TableHead>
                    <TableHead className="min-w-[180px]">Remarks</TableHead>
                    <TableHead className="w-10" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="py-8 text-center text-sm text-slate-500">
                        No sanctioned posts configured yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    rows.map((row) => (
                      <TableRow key={row._key}>
                        <TableCell className="p-1">
                          <Select value={row.designation_code || ""} onValueChange={(value) => updateRow(row._key, "designation_code", value)}>
                            <SelectTrigger className="h-8 text-xs">
                              <SelectValue placeholder="Select post" />
                            </SelectTrigger>
                            <SelectContent>
                              {(designations || []).map((designation) => (
                                <SelectItem key={designation.code} value={designation.code}>
                                  {recordLabel(designation)}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell className="p-1">
                          <Input
                            type="number"
                            min={0}
                            value={row.sanctioned_count ?? 0}
                            onChange={(event) => updateRow(row._key, "sanctioned_count", event.target.value)}
                            className="h-8 text-xs"
                          />
                        </TableCell>
                        <TableCell className="p-1">
                          <Input
                            value={row.order_number || ""}
                            onChange={(event) => updateRow(row._key, "order_number", event.target.value)}
                            className="h-8 text-xs"
                          />
                        </TableCell>
                        <TableCell className="p-1">
                          <Input
                            type="date"
                            value={row.order_date || ""}
                            onChange={(event) => updateRow(row._key, "order_date", event.target.value)}
                            className="h-8 text-xs"
                          />
                        </TableCell>
                        <TableCell className="p-1">
                          <Input
                            value={row.remarks || ""}
                            onChange={(event) => updateRow(row._key, "remarks", event.target.value)}
                            className="h-8 text-xs"
                          />
                        </TableCell>
                        <TableCell className="p-1">
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-red-500 hover:bg-red-50 hover:text-red-700"
                            onClick={() => patchRows(rows.filter((item) => item._key !== row._key))}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            <Button type="button" variant="outline" size="sm" className="gap-2" onClick={() => patchRows([...rows, emptyRow()])}>
              <Plus className="h-4 w-4" />
              Add Row
            </Button>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-slate-600">
                Reason for change <span className="text-red-500">*</span>
              </Label>
              <Textarea
                value={dialog.reason || ""}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Explain the change for audit trail..."
                rows={3}
              />
            </div>
          </div>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
          <Button type="button" onClick={onSave} disabled={saving || dialog.loading || (dialog.reason || "").trim().length < 3}>
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
