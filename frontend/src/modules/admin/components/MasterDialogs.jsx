import { Ban, History } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/shared/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "@/shared/ui/sheet";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { Switch } from "@/shared/ui/switch";
import { Checkbox } from "@/shared/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import { Textarea } from "@/shared/ui/textarea";
import {
  createEmptyMasterMetadata,
  getPolicyMasterCreateFields,
  getPolicyMasterIdentityFields,
} from "@/modules/admin/model/policyMasterForms";

const DEFAULT_SERVICE_EVENT_META = {
  event_code: "",
  service_book_part: "II-A",
  requires_order_number: true,
  affects_pay: false,
  affects_posting: false,
};

const MasterDialogs = ({
  showVersionHistory,
  setShowVersionHistory,
  deprecateDialog,
  setDeprecateDialog,
  deprecateReason,
  setDeprecateReason,
  handleDeprecateMaster,
  editMasterDialog,
  setEditMasterDialog,
  editMasterData,
  setEditMasterData,
  isServiceEventMaster,
  editServiceEventMeta,
  setEditServiceEventMeta,
  SERVICE_EVENT_PARTS,
  submitMasterUpdate,
  createMasterDialog,
  setCreateMasterDialog,
  newMasterData,
  setNewMasterData,
  newMasterMetadataForm,
  setNewMasterMetadataForm,
  masterReferenceOptions,
  newServiceEventMeta,
  setNewServiceEventMeta,
  SYSTEM_MANAGED_MASTERS,
  selectedMasterType,
  submitMasterCreate,
}) => {
  const createFields = getPolicyMasterCreateFields(selectedMasterType, masterReferenceOptions);
  const identityFields = getPolicyMasterIdentityFields(selectedMasterType);

  const updateNewMetadataField = (key, value) => {
    setNewMasterMetadataForm((prev) => ({ ...prev, [key]: value }));
  };

  const toggleNewMetadataMultiSelect = (key, optionValue, checked) => {
    setNewMasterMetadataForm((prev) => {
      const current = Array.isArray(prev[key]) ? prev[key] : [];
      const next = checked
        ? [...new Set([...current, optionValue])]
        : current.filter((value) => value !== optionValue);
      return { ...prev, [key]: next };
    });
  };

  return (
    <>
      <Dialog open={showVersionHistory.open} onOpenChange={(open) => !open && setShowVersionHistory({ open: false, code: null, history: [] })}>
        <DialogContent className="max-w-3xl">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><History className="w-5 h-5" />Version History: {showVersionHistory.code}</DialogTitle></DialogHeader>
          <div className="max-h-96 overflow-auto">
            <Table>
              <TableHeader><TableRow><TableHead>Version</TableHead><TableHead>Name</TableHead><TableHead>Reason</TableHead><TableHead>Status</TableHead><TableHead>Created</TableHead><TableHead>By</TableHead></TableRow></TableHeader>
              <TableBody>
                {showVersionHistory.history.map((v) => (
                  <TableRow key={v.id} className={v.is_active ? "bg-green-50" : ""}>
                    <TableCell><Badge variant={v.is_active ? "default" : "outline"}>v{v.version}</Badge></TableCell>
                    <TableCell>{v.name}</TableCell>
                    <TableCell className="text-xs text-slate-600 max-w-[180px] truncate">{v.metadata?.reason || v.reason || (v.version === 1 ? "Initial creation" : "—")}</TableCell>
                    <TableCell>{v.is_active ? <Badge className="bg-green-100 text-green-700">Active</Badge> : <Badge variant="outline">Superseded</Badge>}</TableCell>
                    <TableCell className="text-xs">{new Date(v.created_at).toLocaleDateString()}</TableCell>
                    <TableCell className="text-xs">{v.created_by}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setShowVersionHistory({ open: false, code: null, history: [] })}>Close</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={deprecateDialog.open} onOpenChange={(open) => { if (!open) { setDeprecateDialog({ open: false, record: null }); setDeprecateReason(""); } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base"><Ban className="w-4 h-4 text-amber-600" />Deprecate Record</DialogTitle>
            <DialogDescription>
              This will soft-deprecate the record. It will remain in the system for historical reference but will no longer be available for new transactions.
            </DialogDescription>
          </DialogHeader>
          {deprecateDialog.record && (
            <div className="space-y-4 py-1">
              <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl text-sm">
                <span className="text-amber-700 font-medium">{deprecateDialog.record.code}</span>
                <span className="mx-2 text-amber-300">|</span>
                <span className="text-amber-600">{deprecateDialog.record.name}</span>
                <span className="mx-2 text-amber-300">|</span>
                <span className="text-amber-500 text-xs">v{deprecateDialog.record.version}</span>
              </div>
              <div>
                <Label htmlFor="deprecate-reason">Reason for deprecation <span className="text-red-500">*</span></Label>
                <Textarea
                  id="deprecate-reason"
                  value={deprecateReason}
                  onChange={(e) => setDeprecateReason(e.target.value)}
                  placeholder="Explain why this record is being deprecated..."
                  className="mt-1.5"
                  rows={3}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => { setDeprecateDialog({ open: false, record: null }); setDeprecateReason(""); }}>Cancel</Button>
            <Button
              variant="destructive"
              disabled={!deprecateReason.trim()}
              onClick={handleDeprecateMaster}
            >
              Deprecate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Sheet open={editMasterDialog.open} onOpenChange={(open) => {
        if (!open) {
          setEditMasterDialog({ open: false, record: null });
          setEditServiceEventMeta(DEFAULT_SERVICE_EVENT_META);
        }
      }}>
        <SheetContent side="right" size="lg" className="flex flex-col">
          <SheetHeader className="flex-shrink-0"><SheetTitle>Update Master Record</SheetTitle><SheetDescription>This creates a NEW VERSION. Current version will be superseded.</SheetDescription></SheetHeader>
          <div className="flex-1 overflow-y-auto space-y-4 mt-4 pr-1">
            <div className="p-3 bg-blue-50/60 border border-blue-200/60 rounded-xl text-sm"><strong>Code:</strong> {editMasterDialog.record?.code} &middot; <strong>Current:</strong> v{editMasterDialog.record?.version}</div>
            <div className="space-y-1.5"><Label className="text-xs font-medium text-slate-600">Name</Label><Input value={editMasterData.name} onChange={(e) => setEditMasterData({ ...editMasterData, name: e.target.value })} className="rounded-lg" /></div>
            <div className="space-y-1.5"><Label className="text-xs font-medium text-slate-600">Description</Label><Textarea value={editMasterData.description} onChange={(e) => setEditMasterData({ ...editMasterData, description: e.target.value })} rows={2} className="rounded-lg" /></div>
            {isServiceEventMaster && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Event Code *</Label>
                  <Input value={editServiceEventMeta.event_code} onChange={(e) => setEditServiceEventMeta({ ...editServiceEventMeta, event_code: e.target.value })} placeholder="e.g., APPOINTMENT" />
                </div>
                <div className="space-y-2">
                  <Label>Service Book Part *</Label>
                  <Select value={editServiceEventMeta.service_book_part} onValueChange={(value) => setEditServiceEventMeta({ ...editServiceEventMeta, service_book_part: value })}>
                    <SelectTrigger><SelectValue placeholder="Select part" /></SelectTrigger>
                    <SelectContent>
                      {SERVICE_EVENT_PARTS.map((part) => (
                        <SelectItem key={part.value} value={part.value}>{part.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Requires Order Number</Label>
                  <div className="flex items-center gap-2">
                    <Switch checked={editServiceEventMeta.requires_order_number} onCheckedChange={(value) => setEditServiceEventMeta({ ...editServiceEventMeta, requires_order_number: value })} />
                    <span>{editServiceEventMeta.requires_order_number ? "Required" : "Optional"}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Affects Pay</Label>
                  <div className="flex items-center gap-2">
                    <Switch checked={editServiceEventMeta.affects_pay} onCheckedChange={(value) => setEditServiceEventMeta({ ...editServiceEventMeta, affects_pay: value })} />
                    <span>{editServiceEventMeta.affects_pay ? "Yes" : "No"}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Affects Posting</Label>
                  <div className="flex items-center gap-2">
                    <Switch checked={editServiceEventMeta.affects_posting} onCheckedChange={(value) => setEditServiceEventMeta({ ...editServiceEventMeta, affects_posting: value })} />
                    <span>{editServiceEventMeta.affects_posting ? "Yes" : "No"}</span>
                  </div>
                </div>
              </div>
            )}
            <div className="space-y-1.5"><Label className="text-xs font-medium text-slate-600">Reason * (min 10 chars)</Label><Textarea value={editMasterData.reason} onChange={(e) => setEditMasterData({ ...editMasterData, reason: e.target.value })} placeholder="Explain why..." rows={3} className="rounded-lg" /></div>
          </div>
          <SheetFooter className="flex-shrink-0 mt-4 border-t pt-4"><Button variant="outline" onClick={() => setEditMasterDialog({ open: false, record: null })}>Cancel</Button><Button onClick={submitMasterUpdate} disabled={editMasterData.reason.length < 10}>Create New Version</Button></SheetFooter>
        </SheetContent>
      </Sheet>

      <Sheet open={createMasterDialog} onOpenChange={(open) => {
        setCreateMasterDialog(open);
        if (!open) {
          setNewMasterData({ code: "", name: "", description: "", metadata: "" });
          setNewMasterMetadataForm(createEmptyMasterMetadata(selectedMasterType));
          setNewServiceEventMeta(DEFAULT_SERVICE_EVENT_META);
        }
      }}>
        <SheetContent side="right" size="lg" className="flex flex-col">
          <SheetHeader className="flex-shrink-0">
            <SheetTitle>Create Master Record</SheetTitle>
            <SheetDescription>
              Create a new record in {SYSTEM_MANAGED_MASTERS.find((m) => m.id === selectedMasterType)?.name || "selected master"}.
            </SheetDescription>
          </SheetHeader>
          <div className="flex-1 overflow-y-auto space-y-4 pr-1">
            <div className="space-y-2"><Label>Code *</Label><Input value={newMasterData.code} onChange={(e) => setNewMasterData({ ...newMasterData, code: e.target.value })} placeholder={identityFields.codePlaceholder} /></div>
            <div className="space-y-2"><Label>Name *</Label><Input value={newMasterData.name} onChange={(e) => setNewMasterData({ ...newMasterData, name: e.target.value })} placeholder={identityFields.namePlaceholder} /></div>
            <div className="space-y-2"><Label>Description</Label><Textarea value={newMasterData.description} onChange={(e) => setNewMasterData({ ...newMasterData, description: e.target.value })} rows={2} placeholder={identityFields.descriptionPlaceholder} /></div>
            {selectedMasterType === "service_event_type" ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Event Code *</Label>
                  <Input value={newServiceEventMeta.event_code} onChange={(e) => setNewServiceEventMeta({ ...newServiceEventMeta, event_code: e.target.value })} placeholder="e.g., APPOINTMENT" />
                </div>
                <div className="space-y-2">
                  <Label>Service Book Part *</Label>
                  <Select value={newServiceEventMeta.service_book_part} onValueChange={(value) => setNewServiceEventMeta({ ...newServiceEventMeta, service_book_part: value })}>
                    <SelectTrigger><SelectValue placeholder="Select part" /></SelectTrigger>
                    <SelectContent>
                      {SERVICE_EVENT_PARTS.map((part) => (
                        <SelectItem key={part.value} value={part.value}>{part.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Requires Order Number</Label>
                  <div className="flex items-center gap-2">
                    <Switch checked={newServiceEventMeta.requires_order_number} onCheckedChange={(value) => setNewServiceEventMeta({ ...newServiceEventMeta, requires_order_number: value })} />
                    <span>{newServiceEventMeta.requires_order_number ? "Required" : "Optional"}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Affects Pay</Label>
                  <div className="flex items-center gap-2">
                    <Switch checked={newServiceEventMeta.affects_pay} onCheckedChange={(value) => setNewServiceEventMeta({ ...newServiceEventMeta, affects_pay: value })} />
                    <span>{newServiceEventMeta.affects_pay ? "Yes" : "No"}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Affects Posting</Label>
                  <div className="flex items-center gap-2">
                    <Switch checked={newServiceEventMeta.affects_posting} onCheckedChange={(value) => setNewServiceEventMeta({ ...newServiceEventMeta, affects_posting: value })} />
                    <span>{newServiceEventMeta.affects_posting ? "Yes" : "No"}</span>
                  </div>
                </div>
              </div>
            ) : (
              createFields.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {createFields.map((field) => {
                    const value = newMasterMetadataForm[field.key];
                    return (
                      <div key={field.key} className={field.fullWidth ? "space-y-2 sm:col-span-2" : "space-y-2"}>
                        <Label>{field.label}</Label>
                        {field.type === "text" && (
                          <Input
                            value={value || ""}
                            onChange={(e) => updateNewMetadataField(field.key, e.target.value)}
                            placeholder={field.placeholder}
                          />
                        )}
                        {field.type === "number" && (
                          <Input
                            type="number"
                            value={value ?? ""}
                            onChange={(e) => updateNewMetadataField(field.key, e.target.value)}
                            placeholder={field.placeholder}
                          />
                        )}
                        {field.type === "select" && (
                          field.options?.length > 0 ? (
                            <Select value={value || ""} onValueChange={(nextValue) => updateNewMetadataField(field.key, nextValue)}>
                              <SelectTrigger><SelectValue placeholder={field.placeholder || "Select option"} /></SelectTrigger>
                              <SelectContent>
                                {field.options.map((option) => (
                                  <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          ) : (
                            <div className="rounded-md border border-dashed px-3 py-2 text-sm text-slate-500">No options available yet.</div>
                          )
                        )}
                        {field.type === "switch" && (
                          <div className="flex items-center gap-2 rounded-md border px-3 py-2">
                            <Switch checked={!!value} onCheckedChange={(checked) => updateNewMetadataField(field.key, checked)} />
                            <span className="text-sm text-slate-600">{value ? "Yes" : "No"}</span>
                          </div>
                        )}
                        {field.type === "multiselect" && (
                          field.options?.length > 0 ? (
                            <div className="max-h-44 space-y-2 overflow-auto rounded-md border p-3">
                              {field.options.map((option) => {
                                const checked = Array.isArray(value) && value.includes(option.value);
                                return (
                                  <label key={option.value} className="flex items-start gap-2 text-sm text-slate-700">
                                    <Checkbox
                                      checked={checked}
                                      onCheckedChange={(nextChecked) => toggleNewMetadataMultiSelect(field.key, option.value, !!nextChecked)}
                                    />
                                    <span>{option.label}</span>
                                  </label>
                                );
                              })}
                            </div>
                          ) : (
                            <div className="rounded-md border border-dashed px-3 py-2 text-sm text-slate-500">No options available yet.</div>
                          )
                        )}
                        {field.helperText && (
                          <p className="text-xs text-slate-500">{field.helperText}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="rounded-lg border border-dashed bg-slate-50 px-4 py-3 text-sm text-slate-600">
                  No additional metadata fields are required for this master type.
                </div>
              )
            )}
          </div>
          <SheetFooter className="flex-shrink-0 mt-4 border-t pt-4">
            <Button variant="outline" onClick={() => setCreateMasterDialog(false)}>Cancel</Button>
            <Button onClick={submitMasterCreate} disabled={!newMasterData.code.trim() || !newMasterData.name.trim()}>Create</Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </>
  );
};

export default MasterDialogs;