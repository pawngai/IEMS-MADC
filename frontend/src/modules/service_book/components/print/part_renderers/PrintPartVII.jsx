import React from "react";

import { AttestationBlock, PageHeader, PrintRow } from "@/modules/service_book/components/print/PrintHeader";
import { PrintEmpty, PrintSection } from "@/modules/service_book/components/print/PrintSectionRenderer";
import { fmt, fmtDate, money } from "@/modules/service_book/components/print/helpers/printHelpers";

export default function PrintPartVII({ data, employeeName, employeeId }) {
  if (!data) return null;

  return (
    <section className="sb-part-page">
      <PageHeader employeeName={employeeName} employeeId={employeeId} partLabel="Part VII - Other Records" />

      {data.ltc_records?.length > 0 && (
        <PrintSection title="Leave Travel Concession (LTC)">
          <table className="sb-table">
            <thead><tr><th>Block Year</th><th>Type</th><th>Date</th><th>From</th><th>To</th><th>Family</th><th>Claimed</th><th>Sanctioned</th><th>Order No</th></tr></thead>
            <tbody>
              {data.ltc_records.map((r, i) => (
                <tr key={r.id || i}>
                  <td>{r.block_year}</td><td>{r.ltc_type}</td><td>{fmtDate(r.availed_date)}</td><td>{r.journey_from}</td><td>{r.journey_to}</td><td>{r.family_members_availed}</td><td>{money(r.amount_claimed)}</td><td>{money(r.amount_sanctioned)}</td><td>{fmt(r.sanction_order_number)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </PrintSection>
      )}

      {data.hba_records?.length > 0 && (
        <PrintSection title="House Building Advance (HBA)">
          <table className="sb-table">
            <thead><tr><th>Sanction Date</th><th>Order No</th><th>Amount</th><th>Purpose</th><th>Property Address</th><th>Monthly EMI</th><th>Repaid</th><th>Balance</th></tr></thead>
            <tbody>
              {data.hba_records.map((r, i) => (
                <tr key={r.id || i}>
                  <td>{fmtDate(r.sanction_date)}</td><td>{r.sanction_order_number}</td><td>{money(r.amount_sanctioned)}</td><td>{r.purpose}</td><td>{r.property_address}</td><td>{money(r.monthly_installment)}</td><td>{money(r.total_repaid)}</td><td>{money(r.balance_outstanding)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </PrintSection>
      )}

      {data.vehicle_advance_records?.length > 0 && (
        <PrintSection title="Vehicle Advance">
          {data.vehicle_advance_records.map((r, i) => (
            <div key={i} className="sb-grid-2">
              {Object.entries(r)
                .filter(([k]) => k !== "id")
                .map(([k, v]) => (
                  <PrintRow key={k} label={k.replace(/_/g, " ")} value={v} />
                ))}
            </div>
          ))}
        </PrintSection>
      )}

      {data.festival_advance_records?.length > 0 && (
        <PrintSection title="Festival Advance">
          <table className="sb-table">
            <thead><tr><th>Date</th><th>Festival</th><th>Amount</th><th>Recovery Months</th><th>Monthly Deduction</th><th>Order No</th><th>Status</th></tr></thead>
            <tbody>
              {data.festival_advance_records.map((r, i) => (
                <tr key={i}>
                  <td>{fmtDate(r.advance_date)}</td><td>{fmt(r.festival)}</td><td>{money(r.amount)}</td><td>{fmt(r.recovery_months)}</td><td>{money(r.monthly_deduction)}</td><td>{fmt(r.order_number)}</td><td>{fmt(r.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </PrintSection>
      )}

      {!data.ltc_records?.length && !data.hba_records?.length && !data.vehicle_advance_records?.length && !data.festival_advance_records?.length && (
        <PrintEmpty message="No records in Part VII." />
      )}

      <AttestationBlock />
    </section>
  );
}
