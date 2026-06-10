import { useMemo } from "react";
import { buildOpeningEligibility } from "@/contexts/service_book/opening/services/openingDomainService";

export const useOpeningEligibility = (employee) =>
  useMemo(() => buildOpeningEligibility(employee), [employee]);

export default useOpeningEligibility;
