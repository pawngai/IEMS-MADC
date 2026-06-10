import React from "react";

import { AttestationBlock, PageHeader, PrintRow } from "@/contexts/service_book/components/print/PrintHeader";
import { fmt, fmtDate } from "@/contexts/service_book/components/print/helpers/printHelpers";
import { PrintSection } from "@/contexts/service_book/components/print/PrintSectionRenderer";

export default function PrintPartIIB({ data, employeeName, employeeId }) {
  if (!data) return null;
  const nominations = [
    { label: "PCF Nomination", items: data.pcf_nomination, date: data.pcf_nomination_date, acct: data.pcf_account_number },
    { label: "DCR Gratuity", items: data.dcr_gratuity_nomination, date: data.dcr_gratuity_nomination_date },
    { label: "Family Pension", items: data.family_pension_nomination, date: data.family_pension_nomination_date },
    { label: "Leave Encashment", items: data.leave_encashment_nomination, date: data.leave_encashment_nomination_date },
    { label: "NPS", items: data.nps_nomination, date: data.nps_nomination_date, acct: data.nps_pran_number },
  ];

  return (
    <section className="sb-part-page">
      <PageHeader employeeName={employeeName} employeeId={employeeId} partLabel="Part II-B - Mutable Certificates (Nominations & Bank)" />

      {data.family_members?.length > 0 && (
        <PrintSection title="Family Particulars">
          <table className="sb-table">
            <thead><tr><th>Name</th><th>Relationship</th><th>DOB</th><th>Dependent</th></tr></thead>
            <tbody>
              {data.family_members.map((m, i) => (
                <tr key={i}><td>{m.name}</td><td>{m.relationship}</td><td>{fmtDate(m.date_of_birth)}</td><td>{m.is_dependent ? "Yes" : "No"}</td></tr>
              ))}
            </tbody>
          </table>
        </PrintSection>
      )}

      <PrintSection title="Nominations">
        <table className="sb-table">
          <thead><tr><th>Type</th><th>Account/Policy</th><th>Nominees</th><th>Nom. Date</th></tr></thead>
          <tbody>
            {nominations.map((n, i) => (
              <tr key={i}>
                <td>{n.label}</td>
                <td>{fmt(n.acct)}</td>
                <td>
                  {n.items?.length
                    ? n.items.map((nom, j) => (
                        <div key={j}>{nom.name || nom.nominee_name} ({nom.relationship || nom.relation}) - {nom.share_percent || nom.share_percentage || "-"}%</div>
                      ))
                    : "-"}
                </td>
                <td>{fmtDate(n.date)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </PrintSection>

      <PrintSection title="Bank Details">
        <div className="sb-grid-2">
          <PrintRow label="Bank Account No" value={data.bank_account_number} />
          <PrintRow label="Bank Name" value={data.bank_name} />
          <PrintRow label="IFSC Code" value={data.bank_ifsc} />
        </div>
      </PrintSection>

      <AttestationBlock />
    </section>
  );
}
