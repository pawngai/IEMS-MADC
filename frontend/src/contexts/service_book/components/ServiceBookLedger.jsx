import React from "react";
import ServiceBookLedgerScreen from "@/contexts/service_book/containers/ServiceBookLedgerScreen";

export default function ServiceBookLedger({ employeeId, employeeName, onClose, forceReadOnly = false }) {
  return (
    <ServiceBookLedgerScreen
      employeeId={employeeId}
      employeeName={employeeName}
      onClose={onClose}
      forceReadOnly={forceReadOnly}
    />
  );
}
