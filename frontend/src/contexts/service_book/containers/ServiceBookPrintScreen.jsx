import ServiceBookPrintShell from "@/contexts/service_book/components/print/ServiceBookPrintShell";

export default function ServiceBookPrintScreen({ serviceBook, employeeName, employeeId }) {
  return <ServiceBookPrintShell serviceBook={serviceBook} employeeName={employeeName} employeeId={employeeId} />;
}
