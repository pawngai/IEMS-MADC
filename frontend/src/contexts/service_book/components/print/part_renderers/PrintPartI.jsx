import React from "react";

import { AuthImage } from "@/platform/auth/AuthImage";
import { AttestationBlock, PageHeader, PrintRow } from "@/contexts/service_book/components/print/PrintHeader";
import { PrintSection } from "@/contexts/service_book/components/print/PrintSectionRenderer";
import {
  addressStr,
  fmtDate,
  listToString,
} from "@/contexts/service_book/components/print/helpers/printHelpers";

export default function PrintPartI({ data, employeeName, employeeId }) {
  const addr = (data?.permanent_address) || {};
  const photoPath = data?.photograph_url;
  const sigPath = data?.signature_url;

  return (
    <>
      {/* Page 2 — Intentionally blank (back of cover) */}
      <section className="sb-part-page sb-blank-page">
        <div className="sb-blank-page-notice">This page intentionally left blank</div>
      </section>

      {/* Page 3 — Personal bio-data + photo */}
      <section className="sb-part-page">
        <PageHeader employeeName={employeeName} employeeId={employeeId} partLabel="Part I - Bio-Data" />
        <PrintSection>
          <div className="sb-part-i-bio">
            <div className="sb-part-i-fields">
              <div className="sb-grid-2">
                <PrintRow label="Name (Block Letters)" value={data?.name_in_block_letters} />
                <PrintRow label="Father/Parent's Name" value={data?.parent_name || data?.father_name} />
                <PrintRow label="Mother's Name" value={data?.mother_name} />
                <PrintRow label="Spouse's Name" value={data?.spouse_name} />
                <PrintRow label="Nationality" value={data?.nationality} />
                <PrintRow label="Caste Category" value={data?.caste_category} />
                <PrintRow label="Religion" value={data?.religion} />
                <PrintRow label="Blood Group" value={data?.blood_group} />
                <PrintRow label="DOB (Christian)" value={fmtDate(data?.date_of_birth_christian)} />
                <PrintRow label="DOB (Saka)" value={data?.date_of_birth_saka} />
                <PrintRow label="Place of Birth" value={data?.place_of_birth} />
                <PrintRow label="Height (cm)" value={data?.height_cm} />
              </div>
              <PrintRow
                label="Identification Marks"
                value={Array.isArray(data?.identification_marks) ? data.identification_marks.join("; ") : data?.identification_marks}
                wide
              />
            </div>
            <div className="sb-part-i-photo">
              {photoPath ? (
                <AuthImage path={photoPath} alt="Photograph" className="sb-photograph"
                  fallback={<div className="sb-photo-placeholder">No Photo</div>}
                />
              ) : (
                <div className="sb-photo-placeholder">No Photo</div>
              )}
              <div className="sb-photo-label">Photograph</div>
            </div>
          </div>
        </PrintSection>
      </section>

      {/* Page 3 — Address, qualifications, signatures */}
      <section className="sb-part-page">
        <PageHeader employeeName={employeeName} employeeId={employeeId} partLabel="Part I - Bio-Data (Continued)" />
        <PrintSection>
          <PrintRow label="Permanent Address" value={addressStr(addr)} wide />
          <PrintRow label="Phone" value={data?.phone_number} wide />
          <PrintRow label="Email" value={data?.email} wide />
        </PrintSection>

        <PrintSection title="Educational Qualifications">
          <PrintRow label="At First Appointment" value={listToString(data?.educational_qualifications_initial)} wide />
          <PrintRow label="Acquired During Service" value={listToString(data?.educational_qualifications_acquired)} wide />
          <PrintRow label="Professional / Technical" value={listToString(data?.professional_qualifications)} wide />
        </PrintSection>

        <PrintSection title="Signatures">
          <div className="sb-signatures-row">
            {sigPath ? (
              <div>
                <div className="sb-sig-label">Signature</div>
                <AuthImage path={sigPath} alt="Signature" className="sb-signature-img" />
              </div>
            ) : (
              <PrintRow label="Signature" value="(not uploaded)" />
            )}
          </div>
        </PrintSection>

        <AttestationBlock />
      </section>
    </>
  );
}
