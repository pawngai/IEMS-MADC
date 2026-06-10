import React from "react";

export function PrintCoverPage({ serviceBook, employeeName, employeeId }) {
  return (
    <section className="sb-part-page sb-cover-page">
      <div className="sb-cover">
        <div className="sb-cover-govt">Mara Autonomous District Council</div>
        <div className="sb-cover-title">DIGITAL SERVICE BOOK</div>
        <div className="sb-cover-divider" />
        <div className="sb-cover-name">{employeeName || "—"}</div>
        <div className="sb-cover-id">{serviceBook?.employee_code || employeeId}</div>
        <div className="sb-cover-meta">
          <div>Completion: {serviceBook.completion_percentage ?? 0}%</div>
          <div>Parts Completed: {serviceBook.parts_completed?.join(", ") || "None"}</div>
        </div>
      </div>
    </section>
  );
}

export function PrintFooterPage({ printDate }) {
  return (
    <section className="sb-part-page sb-footer-page">
      <div className="sb-print-footer-block">
        <p>This is a computer-generated Digital Service Book.</p>
        <p>Printed on: {printDate}</p>
        <p className="sb-disclaimer">
          This document is generated from MADC Human Resource Management System (MADC-HRMS).
          All entries are subject to verification as per applicable government rules.
        </p>
      </div>
    </section>
  );
}
