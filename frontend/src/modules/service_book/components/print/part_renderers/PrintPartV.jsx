import React from "react";

import { AttestationBlock, PageHeader } from "@/modules/service_book/components/print/PrintHeader";
import { PrintEmpty } from "@/modules/service_book/components/print/PrintSectionRenderer";
import { fmt, fmtDate, yesNo } from "@/modules/service_book/components/print/helpers/printHelpers";

export default function PrintPartV({ data, employeeName, employeeId }) {
  if (!data) return null;
  const total = data.total_verified_service || {};

  return (
    <section className="sb-part-page">
      <PageHeader employeeName={employeeName} employeeId={employeeId} partLabel="Part V - Verification of Service" />
      {data.verification_entries?.length > 0 ? (
        <>
          <table className="sb-table">
            <thead>
              <tr><th>S.No.</th><th>Period From</th><th>Period To</th><th>Post Held</th><th>Purpose</th><th>Verified</th><th>Certifying Officer</th><th>Cert. Date</th><th>Remarks</th></tr>
            </thead>
            <tbody>
              {data.verification_entries.map((v, i) => (
                <tr key={i}>
                  <td>{i + 1}</td>
                  <td>{fmtDate(v.period_from)}</td>
                  <td>{fmtDate(v.period_to)}</td>
                  <td>{fmt(v.post_held)}</td>
                  <td>{fmt(v.purpose_of_qualification)}</td>
                  <td>{yesNo(v.verified)}</td>
                  <td>{fmt(v.certifying_officer)}</td>
                  <td>{fmtDate(v.certification_date)}</td>
                  <td>{fmt(v.remarks)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="sb-summary-line">
            Total Verified Service: {total.years || 0} years, {total.months || 0} months, {total.days || 0} days
          </div>
        </>
      ) : (
        <PrintEmpty message="No verification entries recorded." />
      )}
      <AttestationBlock />
    </section>
  );
}
