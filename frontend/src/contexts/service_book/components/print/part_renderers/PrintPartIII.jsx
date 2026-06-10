import React from "react";

import { AttestationBlock, PageHeader, PrintRow } from "@/contexts/service_book/components/print/PrintHeader";
import { PrintEmpty, PrintSection } from "@/contexts/service_book/components/print/PrintSectionRenderer";
import { fmt, fmtDate, money, yesNo } from "@/contexts/service_book/components/print/helpers/printHelpers";

export default function PrintPartIII({ data, employeeName, employeeId }) {
  if (!data) return null;
  const svc = data.total_previous_qualifying_service || {};

  return (
    <section className="sb-part-page">
      <PageHeader employeeName={employeeName} employeeId={employeeId} partLabel="Part III - Service History Outside Current Appointment" />

      {data.previous_services?.length > 0 && (
        <PrintSection title="Previous Qualifying Service">
          <table className="sb-table">
            <thead>
              <tr><th>From</th><th>To</th><th>Post Held</th><th>Organization</th><th>Pay Scale</th><th>Purpose</th><th>Qualifying Period</th><th>Certified By</th></tr>
            </thead>
            <tbody>
              {data.previous_services.map((s, i) => (
                <tr key={i}>
                  <td>{fmtDate(s.service_from)}</td>
                  <td>{fmtDate(s.service_to)}</td>
                  <td>{fmt(s.post_held)}</td>
                  <td>{fmt(s.organization)}</td>
                  <td>{fmt(s.pay_scale)}</td>
                  <td>{fmt(s.purpose_of_qualification)}</td>
                  <td>{s.qualifying_service_years}y {s.qualifying_service_months}m {s.qualifying_service_days}d</td>
                  <td>{fmt(s.certified_by)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="sb-summary-line">
            Total Qualifying Service: {svc.years || 0} years, {svc.months || 0} months, {svc.days || 0} days
          </div>
        </PrintSection>
      )}

      {data.foreign_services?.length > 0 && (
        <PrintSection title="Foreign Service / Deputation">
          <table className="sb-table">
            <thead>
              <tr><th>From</th><th>To</th><th>Post</th><th>Employer</th><th>Leave Salary Contr.</th><th>Pension Contr.</th><th>Remarks</th></tr>
            </thead>
            <tbody>
              {data.foreign_services.map((s, i) => (
                <tr key={i}>
                  <td>{fmtDate(s.service_from)}</td>
                  <td>{fmtDate(s.service_to)}</td>
                  <td>{fmt(s.post_held)}</td>
                  <td>{fmt(s.employer)}</td>
                  <td>{money(s.leave_salary_contribution)}</td>
                  <td>{money(s.pension_contribution)}</td>
                  <td>{fmt(s.remarks)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </PrintSection>
      )}

      {!data.previous_services?.length && !data.foreign_services?.length && (
        <PrintEmpty message="No previous / foreign service records." />
      )}

      <PrintSection>
        <PrintRow label="Verified" value={yesNo(data.verified)} />
        <PrintRow label="Verified By" value={data.verified_by} />
        <PrintRow label="Verification Date" value={fmtDate(data.verification_date)} />
      </PrintSection>

      <AttestationBlock />
    </section>
  );
}
