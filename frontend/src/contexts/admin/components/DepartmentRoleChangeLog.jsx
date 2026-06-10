import { Clock, FileText } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/shared/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";

function formatTimestamp(ts) {
  if (!ts) return "-";
  try {
    return new Date(ts).toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return ts;
  }
}

function renderChanges(changes) {
  if (!changes) return "-";
  return Object.entries(changes)
    .filter(([key]) => key !== "authority_sync")
    .map(([key, val]) => {
      const from = val?.from ?? "-";
      const to = val?.to ?? "-";
      return (
        <div key={key} className="text-[11px]">
          <span className="font-medium text-slate-600">{key}:</span>{" "}
          <span className="text-red-500 line-through">{String(from)}</span>{" "}
          <span className="text-emerald-600">{String(to)}</span>
        </div>
      );
    });
}

function renderSyncInfo(changes) {
  const sync = changes?.authority_sync;
  if (!sync || Object.keys(sync).length === 0) return null;
  return (
    <div className="mt-1 space-y-0.5">
      {sync.hod_sync && (
        <Badge variant="outline" className="text-[10px] font-normal">
          HOD granted to {sync.hod_sync.granted_to}
          {sync.hod_sync.revoked_from && `, revoked from ${sync.hod_sync.revoked_from}`}
        </Badge>
      )}
      {sync.de_sync && (
        <Badge variant="outline" className="text-[10px] font-normal">
          DE granted to {sync.de_sync.granted_to}
          {sync.de_sync.revoked_from && `, revoked from ${sync.de_sync.revoked_from}`}
        </Badge>
      )}
      {sync.hod_revoke && (
        <Badge variant="outline" className="text-[10px] font-normal text-amber-600">
          HOD revoked from {sync.hod_revoke.revoked_from}
        </Badge>
      )}
      {sync.de_revoke && (
        <Badge variant="outline" className="text-[10px] font-normal text-amber-600">
          DE revoked from {sync.de_revoke.revoked_from}
        </Badge>
      )}
      {Object.entries(sync)
        .filter(([k]) => k.endsWith("_error"))
        .map(([k, v]) => (
          <Badge key={k} variant="destructive" className="text-[10px] font-normal">
            {v}
          </Badge>
        ))}
    </div>
  );
}

export default function DepartmentRoleChangeLog({ logDialog, onClose }) {
  const dept = logDialog?.department;
  const logs = logDialog?.logs || [];

  return (
    <Dialog open={logDialog?.open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <FileText className="w-4 h-4" />
            Change Log {dept ? `\u2014 ${dept.name} (${dept.code})` : ""}
          </DialogTitle>
        </DialogHeader>

        {logDialog?.loading ? (
          <div className="py-8 text-center text-sm text-slate-400">Loading...</div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <Clock className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-medium text-slate-600">No changes recorded</p>
          </div>
        ) : (
          <div className="rounded-lg border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50/80">
                  <TableHead className="text-xs">Timestamp</TableHead>
                  <TableHead className="text-xs">Action</TableHead>
                  <TableHead className="text-xs">Changed By</TableHead>
                  <TableHead className="text-xs">Changes</TableHead>
                  <TableHead className="text-xs">Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id} className="align-top">
                    <TableCell className="text-xs text-slate-500 whitespace-nowrap">
                      {formatTimestamp(log.timestamp)}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`text-[10px] ${log.action === "CREATE" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-blue-50 text-blue-700 border-blue-200"}`}
                      >
                        {log.action}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-slate-600">{log.actor_email}</TableCell>
                    <TableCell>
                      {renderChanges(log.changes)}
                      {renderSyncInfo(log.changes)}
                    </TableCell>
                    <TableCell className="text-xs text-slate-500 max-w-[150px] truncate" title={log.reason}>
                      {log.reason || "-"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
