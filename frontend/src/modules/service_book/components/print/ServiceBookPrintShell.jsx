import React from "react";

import {
  PrintPartI,
  PrintPartIIA,
  PrintPartIIB,
  PrintPartIII,
  PrintPartIV,
  PrintPartV,
  PrintPartVI,
  PrintPartVII,
  PrintPartVIII,
} from "@/modules/service_book/components/print/part_renderers";
import {
  PrintCoverPage,
  PrintFooterPage,
} from "@/modules/service_book/components/print/PrintEmployeeSummary";

export default function ServiceBookPrintShell({ serviceBook, employeeName, employeeId }) {
  if (!serviceBook) return null;

  const printDate = new Date().toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="sb-print-only" id="sb-print-view">
      <PrintCoverPage serviceBook={serviceBook} employeeName={employeeName} employeeId={employeeId} />

      <PrintPartI data={serviceBook.part_i} employeeName={employeeName} employeeId={employeeId} />
      <PrintPartIIA data={serviceBook.part_ii_a} employeeName={employeeName} employeeId={employeeId} />
      <PrintPartIIB data={serviceBook.part_ii_b} employeeName={employeeName} employeeId={employeeId} />
      <PrintPartIII data={serviceBook.part_iii} employeeName={employeeName} employeeId={employeeId} />
      <PrintPartIV data={serviceBook.part_iv} employeeName={employeeName} employeeId={employeeId} />
      <PrintPartV data={serviceBook.part_v} employeeName={employeeName} employeeId={employeeId} />
      <PrintPartVI data={serviceBook.part_vi} employeeName={employeeName} employeeId={employeeId} />
      <PrintPartVII data={serviceBook.part_vii} employeeName={employeeName} employeeId={employeeId} />
      <PrintPartVIII data={serviceBook.part_viii} employeeName={employeeName} employeeId={employeeId} />

      <PrintFooterPage printDate={printDate} />
    </div>
  );
}
