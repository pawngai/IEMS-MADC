import React from "react";

import { AttestationBlock, PageHeader } from "@/modules/service_book/components/print/PrintHeader";
import { fmt, fmtDate, yesNo } from "@/modules/service_book/components/print/helpers/printHelpers";

export default function PrintPartIIA({ data, employeeName, employeeId }) {
  if (!data) return null;
  return (
    <section className="sb-part-page">
      <PageHeader employeeName={employeeName} employeeId={employeeId} partLabel="Part II-A - Immutable Certificates" />
      <table className="sb-table">
        <thead>
          <tr><th>Certificate / Verification</th><th>Status</th><th>Date</th><th>Officer / Authority</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>Medical Fitness Certificate</td>
            <td>{yesNo(data.medical_fitness_certificate)}</td>
            <td>{fmtDate(data.medical_exam_date)}</td>
            <td>{fmt(data.medical_officer_name)} {data.medical_category ? `(${data.medical_category})` : ""}</td>
          </tr>
          <tr>
            <td>Character Verification</td>
            <td>{yesNo(data.character_verification_done)}</td>
            <td>{fmtDate(data.character_verification_date)}</td>
            <td>{fmt(data.character_verification_authority)}</td>
          </tr>
          <tr>
            <td>Police Verification</td>
            <td>{yesNo(data.police_verification_done)}</td>
            <td>{fmtDate(data.police_verification_date)}</td>
            <td>-</td>
          </tr>
          <tr>
            <td>Oath of Allegiance</td>
            <td>{yesNo(data.oath_of_allegiance_taken)}</td>
            <td>{fmtDate(data.oath_of_allegiance_date)}</td>
            <td>-</td>
          </tr>
          <tr>
            <td>Oath of Secrecy</td>
            <td>{yesNo(data.oath_of_secrecy_taken)}</td>
            <td>{fmtDate(data.oath_of_secrecy_date)}</td>
            <td>-</td>
          </tr>
          <tr>
            <td>Entries Confirmed</td>
            <td>{yesNo(data.entries_confirmed)}</td>
            <td>{fmtDate(data.confirmation_date)}</td>
            <td>{fmt(data.confirming_officer)}</td>
          </tr>
        </tbody>
      </table>
      <AttestationBlock />
    </section>
  );
}
