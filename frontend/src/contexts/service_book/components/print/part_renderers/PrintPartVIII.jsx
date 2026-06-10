import React from "react";

import { AttestationBlock, PageHeader, PrintRow } from "@/contexts/service_book/components/print/PrintHeader";
import { PrintEmpty, PrintSection } from "@/contexts/service_book/components/print/PrintSectionRenderer";
import { fmtDate } from "@/contexts/service_book/components/print/helpers/printHelpers";

const severityMap = { OBSERVATION: "Obs", MINOR: "Minor", MAJOR: "Major", CRITICAL: "Critical" };

export default function PrintPartVIII({ data, employeeName, employeeId }) {
  if (!data) return null;

  return (
    <section className="sb-part-page">
      <PageHeader employeeName={employeeName} employeeId={employeeId} partLabel="Part VIII - Internal Audit Comments" />

      <PrintSection>
        <div className="sb-grid-3">
          <PrintRow label="Total Comments" value={data.total_comments ?? 0} />
          <PrintRow label="Open" value={data.open_comments ?? 0} />
          <PrintRow label="Resolved" value={data.resolved_comments ?? 0} />
        </div>
      </PrintSection>

      {data.comments?.length > 0 ? (
        <table className="sb-table">
          <thead><tr><th>Date</th><th>Type</th><th>Auditor</th><th>Severity</th><th>Comment</th><th>Status</th><th>Response</th></tr></thead>
          <tbody>
            {data.comments.map((c, i) => (
              <tr key={c.id || i}>
                <td>{fmtDate(c.comment_date)}</td>
                <td>{c.audit_type}</td>
                <td>{c.auditor_name}{c.auditor_designation ? `, ${c.auditor_designation}` : ""}</td>
                <td>{severityMap[c.severity] || c.severity}</td>
                <td className="sb-wrap-cell">{c.comment_text}</td>
                <td>{c.status}</td>
                <td className="sb-wrap-cell">{c.response || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <PrintEmpty message="No audit comments recorded." />
      )}

      <AttestationBlock />
    </section>
  );
}
