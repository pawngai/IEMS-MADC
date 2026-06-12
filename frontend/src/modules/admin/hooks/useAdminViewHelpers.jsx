import { useCallback } from "react";
import { Badge } from "@/shared/ui/badge";
import { dedupeAuthorityCodes, normalizeAuthorityCode } from "@/modules/admin/hooks/authorityNormalization";

const ROLE_COLORS = {
  SYSTEM_ADMIN: "bg-red-100 text-red-700",
  DEPT_DATA_ENTRY: "bg-blue-100 text-blue-700",
  GLOBAL_DATA_ENTRY: "bg-cyan-100 text-cyan-700",
  VERIFIER: "bg-amber-100 text-amber-700",
  APPROVER: "bg-purple-100 text-purple-700",
  HOD: "bg-green-100 text-green-700",
  AUDITOR: "bg-green-100 text-green-700",
};

const useAdminViewHelpers = ({ availableAuthorities }) => {
  const getAuthorityLabel = useCallback((authorityCode) => {
    if (!authorityCode) return "No Role";

    const normalizedCode = normalizeAuthorityCode(authorityCode);

    const authority = (availableAuthorities || []).find((auth) => {
      const code = normalizeAuthorityCode(typeof auth === "string" ? auth : auth.code);
      return code === normalizedCode;
    });

    if (authority && typeof authority !== "string") {
      return authority.name || authority.code || normalizedCode;
    }

    return String(normalizedCode)
      .toLowerCase()
      .split("_")
      .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : ""))
      .join(" ");
  }, [availableAuthorities]);

  const getRoleBadge = useCallback((authorities) => {
    if (!authorities?.length) return <Badge variant="outline">No Role</Badge>;

    const normalizedAuthorities = dedupeAuthorityCodes(authorities);

    return (
      <div className="flex flex-wrap gap-1">
        {normalizedAuthorities.map((authority) => (
          <Badge key={authority} className={ROLE_COLORS[authority] || "bg-slate-100 text-slate-700"}>
            {getAuthorityLabel(authority)}
          </Badge>
        ))}
      </div>
    );
  }, [getAuthorityLabel]);

  const getBooleanBadge = useCallback((value, yesLabel = "Yes", noLabel = "No") => (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${value ? "text-emerald-700" : "text-slate-400"}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${value ? "bg-emerald-500" : "bg-slate-300"}`} />
      {value ? yesLabel : noLabel}
    </span>
  ), []);

  const getRuleBadge = useCallback((value) => {
    if (value === undefined || value === null) {
      return <Badge variant="outline">N/A</Badge>;
    }
    return getBooleanBadge(!!value);
  }, [getBooleanBadge]);

  return {
    getAuthorityLabel,
    getRoleBadge,
    getRuleBadge,
  };
};

export default useAdminViewHelpers;
