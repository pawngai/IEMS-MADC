import React from "react";

import { fmt } from "@/contexts/service_book/components/print/helpers/printHelpers";

export function PageHeader({ employeeName, employeeId, partLabel }) {
  return (
    <div className="sb-page-header">
      <div className="sb-page-header-top">
        <div className="sb-govt-label">Mara Autonomous District Council</div>
        <div className="sb-title">DIGITAL SERVICE BOOK</div>
        <div className="sb-employee-line">
          {employeeName && <span className="sb-emp-name">{employeeName}</span>}
          {employeeId && <span className="sb-emp-id">({employeeName ? employeeId : ""})</span>}
        </div>
      </div>
      <div className="sb-part-label">{partLabel}</div>
    </div>
  );
}

export function PrintRow({ label, value, wide }) {
  return (
    <div className={`sb-row ${wide ? "sb-row-wide" : ""}`}>
      <span className="sb-label">{label}</span>
      <span className="sb-value">{fmt(value)}</span>
    </div>
  );
}

export function AttestationBlock() {
  return (
    <div className="sb-attestation">
      <div className="sb-attest-row">
        <div className="sb-sign-block">
          <div className="sb-sign-line" />
          <div className="sb-sign-caption">Employee Signature</div>
        </div>
        <div className="sb-sign-block">
          <div className="sb-sign-line" />
          <div className="sb-sign-caption">Certifying Officer</div>
          <div className="sb-sign-caption">(Name, Designation &amp; Date)</div>
        </div>
      </div>
    </div>
  );
}
