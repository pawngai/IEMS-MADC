import { Ban, Database, History, Plus, Search, Settings } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { TableSkeleton } from "@/shared/ui/skeletons";
import { Switch } from "@/shared/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

const PolicyMastersTab = ({
  SYSTEM_MANAGED_MASTERS,
  selectedMasterType,
  masterRecordCounts,
  loadMasterRecords,
  filteredMasterRecords,
  masterRecords,
  openCreateMasterDialog,
  masterSearch,
  setMasterSearch,
  showInactiveMasters,
  setShowInactiveMasters,
  masterLoading,
  isServiceEventMaster,
  isSelectedMasterReadOnly,
  selectedMasterConfig,
  getServiceEventMeta,
  getRuleBadge,
  loadVersionHistory,
  setEditMasterData,
  setEditServiceEventMeta,
  setEditMasterDialog,
  setDeprecateDialog,
}) => {
  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base"><Database className="w-4 h-4" />System-Managed Masters</CardTitle>
        <CardDescription>Versioned master data with full audit trail. Deletions are not permitted.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
          {SYSTEM_MANAGED_MASTERS.map((master) => (
            <div
              key={master.id}
              className={`group p-4 border rounded-xl cursor-pointer transition-all hover:shadow-sm ${
                selectedMasterType === master.id
                  ? "border-blue-400 bg-blue-50/50 shadow-sm ring-1 ring-blue-200"
                  : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/50"
              }`}
              onClick={() => loadMasterRecords(master.id)}
            >
              <div className="flex items-center justify-between mb-1.5">
                <p className={`font-medium text-sm ${selectedMasterType === master.id ? "text-blue-700" : "text-slate-700"}`}>{master.name}</p>
                <div className="flex items-center gap-1.5">
                  {masterRecordCounts[master.id] !== undefined && (
                    <Badge variant="outline" className="text-[10px] px-1.5 py-0">{masterRecordCounts[master.id]}</Badge>
                  )}
                  <Database className={`w-3.5 h-3.5 ${selectedMasterType === master.id ? "text-blue-500" : "text-slate-300 group-hover:text-slate-400"}`} />
                </div>
              </div>
              <p className="text-xs text-slate-500">{master.description}</p>
            </div>
          ))}
        </div>

        {selectedMasterType && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <h4 className="font-medium">{SYSTEM_MANAGED_MASTERS.find((m) => m.id === selectedMasterType)?.name} Records</h4>
                {isSelectedMasterReadOnly && (
                  <Badge variant="outline" className="bg-slate-50 text-slate-700">Read-only derived view</Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">{filteredMasterRecords.length} shown</Badge>
                <Badge variant="outline" className="bg-green-50 text-green-700">{masterRecords.filter((r) => r.is_active).length} active</Badge>
                {masterRecords.filter((r) => !r.is_active).length > 0 && (
                  <Badge variant="outline" className="bg-amber-50 text-amber-700">{masterRecords.filter((r) => !r.is_active).length} inactive</Badge>
                )}
                {!isSelectedMasterReadOnly && (
                  <Button size="sm" className="gap-2" onClick={openCreateMasterDialog}>
                    <Plus className="w-4 h-4" />Create Record
                  </Button>
                )}
              </div>
            </div>
            {isSelectedMasterReadOnly && (
              <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
                {selectedMasterConfig?.readOnlyReason || "This master is shown for reference only."}
              </div>
            )}
            <div className="flex items-center gap-3 mb-4">
              <div className="relative flex-1 max-w-xs">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search by code or name..."
                  value={masterSearch}
                  onChange={(e) => setMasterSearch(e.target.value)}
                  className="pl-9 h-9"
                />
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={showInactiveMasters}
                  onCheckedChange={setShowInactiveMasters}
                  id="show-inactive-masters"
                />
                <Label htmlFor="show-inactive-masters" className="text-sm text-slate-600 cursor-pointer">Show inactive</Label>
              </div>
            </div>
            {masterLoading ? (
              <TableSkeleton rows={6} columns={isServiceEventMaster ? 10 : 5} />
            ) : filteredMasterRecords.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm">
                {masterRecords.length === 0 ? "No records found." : "No records match your search."}
              </div>
            ) : (
              isServiceEventMaster ? (
                <div className="overflow-x-auto rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Code</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Event Code</TableHead>
                        <TableHead>Part</TableHead>
                        <TableHead>Order Required</TableHead>
                        <TableHead>Affects Pay</TableHead>
                        <TableHead>Affects Posting</TableHead>
                        <TableHead>Version</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredMasterRecords.map((record) => {
                        const meta = getServiceEventMeta(record);
                        return (
                          <TableRow key={record.id} className={!record.is_active ? "opacity-60" : ""}>
                            <TableCell className="font-mono text-sm">{record.code}</TableCell>
                            <TableCell className={!record.is_active ? "line-through" : ""}>{record.name || record.description || "N/A"}</TableCell>
                            <TableCell className="font-mono text-xs">{meta.event_code || "N/A"}</TableCell>
                            <TableCell><Badge variant="outline">{meta.service_book_part || "N/A"}</Badge></TableCell>
                            <TableCell>{getRuleBadge(meta.requires_order_number)}</TableCell>
                            <TableCell>{getRuleBadge(meta.affects_pay)}</TableCell>
                            <TableCell>{getRuleBadge(meta.affects_posting)}</TableCell>
                            <TableCell><Badge variant="outline">v{record.version}</Badge></TableCell>
                            <TableCell>
                              {!record.is_active ? (
                                <Badge className="bg-slate-100 text-slate-500">Inactive</Badge>
                              ) : record.metadata?.is_deprecated ? (
                                <Badge className="bg-amber-100 text-amber-700">Deprecated</Badge>
                              ) : (
                                <Badge className="bg-green-100 text-green-700">Active</Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-1.5">
                                <Button variant="outline" size="sm" title="Version history" onClick={() => loadVersionHistory(selectedMasterType, record.code)}><History className="w-4 h-4" /></Button>
                                {!isSelectedMasterReadOnly && (
                                  <>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      title="Edit"
                                      disabled={!record.is_active}
                                      onClick={() => {
                                        setEditMasterData({ name: record.name || record.description || "", description: record.description || "", reason: "" });
                                        setEditServiceEventMeta(getServiceEventMeta(record));
                                        setEditMasterDialog({ open: true, record });
                                      }}
                                    >
                                      <Settings className="w-4 h-4" />
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      title="Deprecate"
                                      disabled={!record.is_active || record.metadata?.is_deprecated}
                                      className={record.is_active && !record.metadata?.is_deprecated ? "text-amber-600 hover:text-amber-700 hover:border-amber-300" : ""}
                                      onClick={() => setDeprecateDialog({ open: true, record })}
                                    >
                                      <Ban className="w-4 h-4" />
                                    </Button>
                                  </>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="overflow-x-auto rounded-lg border">
                  <Table>
                    <TableHeader><TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow></TableHeader>
                    <TableBody>
                      {filteredMasterRecords.map((record) => (
                        <TableRow key={record.id} className={!record.is_active ? "opacity-60" : ""}>
                          <TableCell className="font-mono text-sm">{record.code}</TableCell>
                          <TableCell className={!record.is_active ? "line-through" : ""}>{record.name}</TableCell>
                          <TableCell className="text-sm text-slate-500 max-w-[200px] truncate">{record.description || "—"}</TableCell>
                          <TableCell><Badge variant="outline">v{record.version}</Badge></TableCell>
                          <TableCell>
                            {!record.is_active ? (
                              <Badge className="bg-slate-100 text-slate-500">Inactive</Badge>
                            ) : record.metadata?.is_deprecated ? (
                              <Badge className="bg-amber-100 text-amber-700">Deprecated</Badge>
                            ) : (
                              <Badge className="bg-green-100 text-green-700">Active</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1.5">
                              <Button variant="outline" size="sm" title="Version history" onClick={() => loadVersionHistory(selectedMasterType, record.code)}><History className="w-4 h-4" /></Button>
                              {!isSelectedMasterReadOnly && (
                                <>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    title="Edit"
                                    disabled={!record.is_active}
                                    onClick={() => { setEditMasterData({ name: record.name, description: record.description || "", reason: "" }); setEditMasterDialog({ open: true, record }); }}
                                  >
                                    <Settings className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    title="Deprecate"
                                    disabled={!record.is_active || record.metadata?.is_deprecated}
                                    className={record.is_active && !record.metadata?.is_deprecated ? "text-amber-600 hover:text-amber-700 hover:border-amber-300" : ""}
                                    onClick={() => setDeprecateDialog({ open: true, record })}
                                  >
                                    <Ban className="w-4 h-4" />
                                  </Button>
                                </>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PolicyMastersTab;