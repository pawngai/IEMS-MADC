import {
  BookOpen,
  CheckCircle2,
  ClipboardEdit,
  FileText,
  Send,
  ShieldCheck,
  Users,
  XCircle,
} from "lucide-react";

export const TYPE_META = {
  identity: { label: "Identity", icon: Users, color: "bg-emerald-500", badge: "bg-emerald-100 text-emerald-700" },
  profile: { label: "Profile", icon: FileText, color: "bg-blue-500", badge: "bg-blue-100 text-blue-700" },
  service: { label: "Service Book", icon: BookOpen, color: "bg-amber-500", badge: "bg-amber-100 text-amber-700" },
  service_opening: { label: "Service Book Opening", icon: BookOpen, color: "bg-amber-500", badge: "bg-amber-100 text-amber-700" },
  ess: { label: "Self Service", icon: Users, color: "bg-slate-500", badge: "bg-slate-100 text-slate-700" },
  change_request: { label: "Change Request", icon: ClipboardEdit, color: "bg-violet-500", badge: "bg-violet-100 text-violet-700" },
};

export const STATUS_STYLE = {
  DRAFT: "bg-slate-100 text-slate-700 border-slate-200",
  SUBMITTED: "bg-blue-50 text-blue-700 border-blue-200",
  VERIFIED: "bg-amber-50 text-amber-700 border-amber-200",
  APPROVED: "bg-purple-50 text-purple-700 border-purple-200",
  ACTIVE: "bg-green-50 text-green-700 border-green-200",
  LOCKED: "bg-green-50 text-green-700 border-green-200",
  REJECTED: "bg-red-50 text-red-700 border-red-200",
  RECOMMENDED: "bg-indigo-50 text-indigo-700 border-indigo-200",
  SANCTIONED: "bg-green-50 text-green-700 border-green-200",
  PENDING: "bg-violet-50 text-violet-700 border-violet-200",
  NOW: "bg-orange-50 text-orange-700 border-orange-200",
};

export const WORKFLOW_STAGE_META = {
  NOW: { label: "Action needed", description: "Needs your attention before submission" },
  DRAFT: { label: "Draft", description: "Being prepared" },
  SUBMITTED: { label: "Submitted", description: "Awaiting verification" },
  VERIFIED: { label: "Verified", description: "Ready for approval" },
  APPROVED: { label: "Approved", description: "Approved and ready to finalize" },
  ACTIVE: { label: "Active", description: "Identity is activated and live" },
  LOCKED: { label: "Locked", description: "Finalized and immutable" },
  REJECTED: { label: "Rejected", description: "Returned for correction" },
  RECOMMENDED: { label: "Recommended", description: "Ready for sanction" },
  SANCTIONED: { label: "Sanctioned", description: "Sanction recorded" },
  PENDING: { label: "Pending", description: "Waiting on follow-up" },
};

export const SLA_STYLE = {
  GREEN: { bg: "bg-green-500", label: "< 24h", border: "border-green-300" },
  YELLOW: { bg: "bg-yellow-500", label: "24-72h", border: "border-yellow-400" },
  RED: { bg: "bg-red-500", label: "> 72h", border: "border-red-400" },
  NONE: { bg: "bg-slate-300", label: "N/A", border: "border-slate-200" },
};

export const ACTION_ICONS = {
  "identity-submit": Send,
  "identity-verify": CheckCircle2,
  "identity-activate": ShieldCheck,
  "identity-reject": XCircle,
  "profile-submit": Send,
  "profile-verify": CheckCircle2,
  "profile-approve": ShieldCheck,
  "profile-lock": ShieldCheck,
  "profile-reject": XCircle,
  "service-submit": Send,
  "service-verify": CheckCircle2,
  "service-approve": ShieldCheck,
  "service-attest": ShieldCheck,
  "service-reject": XCircle,
  "service-opening-submit": Send,
  "service-opening-verify": CheckCircle2,
  "service-opening-approve": ShieldCheck,
  "cr-approve": CheckCircle2,
  "cr-reject": XCircle,
};

export const KANBAN_STAGES = ["NOW", "DRAFT", "SUBMITTED", "VERIFIED", "APPROVED"];

const toTitleCase = (value) => value.charAt(0).toUpperCase() + value.slice(1);

export const formatWorkflowStatusLabel = (status) => {
  if (!status) return "Unknown";

  const normalized = String(status).trim();
  if (!normalized) return "Unknown";

  const knownLabel = WORKFLOW_STAGE_META[normalized]?.label;
  if (knownLabel) return knownLabel;

  return normalized
    .toLowerCase()
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map(toTitleCase)
    .join(" ");
};

export const getWorkflowStageMeta = (stage) => ({
  label: formatWorkflowStatusLabel(stage),
  description: WORKFLOW_STAGE_META[stage]?.description || "",
});

export const formatAge = (hours) => {
  if (hours == null) return "";
  if (hours < 1) return "just now";
  if (hours < 24) return `${Math.floor(hours)}h ago`;
  const days = Math.floor(hours / 24);
  return days === 1 ? "1 day ago" : `${days} days ago`;
};
