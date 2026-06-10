import React from "react";

import { AttestationBlock, PageHeader } from "@/contexts/service_book/components/print/PrintHeader";
import { PrintEmpty } from "@/contexts/service_book/components/print/PrintSectionRenderer";
import { fmt, fmtDate, money } from "@/contexts/service_book/components/print/helpers/printHelpers";

const formatClassification = (entry) => {
  const parts = [entry?.service, entry?.service_group, entry?.grade].filter(Boolean);
  return parts.length > 0 ? parts.join(" / ") : "-";
};

export default function PrintPartIV({ data, employeeName, employeeId }) {
  if (!data) return null;
  const total = data.total_service || {};

  return (
    <section className="sb-part-page">
      <PageHeader employeeName={employeeName} employeeId={employeeId} partLabel="Part IV - History of Service" />
      {data.entries?.length > 0 ? (
        <>
          <table className="sb-table sb-table-compact">
            <thead>
              <tr>
                <th>S.No.</th><th>Period From</th><th>Period To</th><th>Office / Station</th><th>Post Held</th><th>Service / Group / Grade</th><th>Pay Level</th><th>Basic Pay</th><th>Event</th><th>Order No / Date</th><th>Remarks</th>
              </tr>
            </thead>
            <tbody>
              {data.entries.map((e, i) => (
                <tr key={e.id || i}>
                  <td>{i + 1}</td>
                  <td>{fmtDate(e.period_from)}</td>
                  <td>{e.period_to ? fmtDate(e.period_to) : "Present"}</td>
                  <td>{fmt(e.office_station)}</td>
                  <td>{fmt(e.post_held)}</td>
                  <td>{formatClassification(e)}</td>
                  <td>{fmt(e.pay_level)}</td>
                  <td>{money(e.basic_pay)}</td>
                  <td>{fmt(e.event_type)}</td>
                  <td>{e.event_order_number ? `${e.event_order_number} / ${fmtDate(e.event_order_date)}` : "-"}</td>
                  <td>{fmt(e.remarks)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="sb-summary-line">
            Total Service: {total.years || 0} years, {total.months || 0} months, {total.days || 0} days
          </div>
        </>
      ) : (
        <PrintEmpty message="No service history entries recorded." />
      )}
      <AttestationBlock />
    </section>
  );
}
