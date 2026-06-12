import React from "react";

import { AttestationBlock, PageHeader } from "@/modules/service_book/components/print/PrintHeader";
import { PrintSection } from "@/modules/service_book/components/print/PrintSectionRenderer";
import { fmt, fmtDate } from "@/modules/service_book/components/print/helpers/printHelpers";

export default function PrintPartVI({ data, employeeName, employeeId }) {
  if (!data) return null;

  return (
    <section className="sb-part-page">
      <PageHeader employeeName={employeeName} employeeId={employeeId} partLabel="Part VI - Leave Account" />

      <PrintSection title="Leave Balances (as on date)">
        <table className="sb-table sb-table-narrow">
          <thead><tr><th>Leave Type</th><th>Balance (days)</th></tr></thead>
          <tbody>
            <tr><td>Earned Leave (EL)</td><td>{data.earned_leave_balance ?? 0}</td></tr>
            <tr><td>Half Pay Leave (HPL)</td><td>{data.half_pay_leave_balance ?? 0}</td></tr>
            <tr><td>Commuted Leave</td><td>{data.commuted_leave_balance ?? 0}</td></tr>
            <tr><td>Leave Not Due</td><td>{data.leave_not_due_balance ?? 0}</td></tr>
          </tbody>
        </table>
      </PrintSection>

      {data.transactions?.length > 0 && (
        <PrintSection title="Leave Ledger">
          <table className="sb-table sb-table-compact">
            <thead>
              <tr><th>Date</th><th>Type</th><th>Leave</th><th>Credit</th><th>From</th><th>To</th><th>Availed</th><th>Opening</th><th>Closing</th><th>Remarks</th></tr>
            </thead>
            <tbody>
              {data.transactions.map((t, i) => (
                <tr key={t.id || i}>
                  <td>{fmtDate(t.transaction_date)}</td>
                  <td>{t.transaction_type}</td>
                  <td>{t.leave_type}</td>
                  <td>{t.credit_days ?? "-"}</td>
                  <td>{t.leave_from ? fmtDate(t.leave_from) : "-"}</td>
                  <td>{t.leave_to ? fmtDate(t.leave_to) : "-"}</td>
                  <td>{t.days_availed ?? "-"}</td>
                  <td>{t.opening_balance}</td>
                  <td>{t.closing_balance}</td>
                  <td>{fmt(t.remarks)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </PrintSection>
      )}
      <AttestationBlock />
    </section>
  );
}
