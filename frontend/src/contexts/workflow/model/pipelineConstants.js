import {
  FileText,
  Clock,
  UserCheck,
  ShieldCheck,
  Lock,
  XCircle,
  User,
  Users,
  CreditCard,
  MapPin,
  Briefcase,
} from "lucide-react";

export const PIPELINE_STAGES = [
  { key: "DRAFT", label: "Draft", icon: FileText, color: "slate", description: "Profile being prepared" },
  { key: "SUBMITTED", label: "Submitted", icon: Clock, color: "blue", description: "Awaiting verification" },
  { key: "VERIFIED", label: "Verified", icon: UserCheck, color: "amber", description: "Verified by officer" },
  { key: "APPROVED", label: "Approved", icon: ShieldCheck, color: "purple", description: "Approved by authority" },
  { key: "LOCKED", label: "Locked", icon: Lock, color: "green", description: "Finalized & immutable" },
];

export const REJECTED_STAGE = { key: "REJECTED", label: "Rejected", icon: XCircle, color: "red", description: "Returned for corrections" };

export const SECTION_META = {
  core: { label: "Core Details", icon: Briefcase, color: "blue" },
  personal: { label: "Personal Info", icon: User, color: "indigo" },
  nominees: { label: "Nominees", icon: Users, color: "purple" },
  id_documents: { label: "ID Documents", icon: CreditCard, color: "amber" },
  address: { label: "Address & Contact", icon: MapPin, color: "green" },
};

export const STAGE_COLORS = {
  slate: {
    bg: "bg-slate-100", text: "text-slate-600", ring: "ring-slate-300",
    bgSolid: "bg-slate-500", connector: "bg-slate-300", activeBg: "bg-slate-50",
    progressBg: "bg-slate-200", progressFill: "bg-slate-500",
  },
  blue: {
    bg: "bg-blue-100", text: "text-blue-600", ring: "ring-blue-300",
    bgSolid: "bg-blue-500", connector: "bg-blue-300", activeBg: "bg-blue-50",
    progressBg: "bg-blue-100", progressFill: "bg-blue-500",
  },
  amber: {
    bg: "bg-amber-100", text: "text-amber-600", ring: "ring-amber-300",
    bgSolid: "bg-amber-500", connector: "bg-amber-300", activeBg: "bg-amber-50",
    progressBg: "bg-amber-100", progressFill: "bg-amber-500",
  },
  purple: {
    bg: "bg-purple-100", text: "text-purple-600", ring: "ring-purple-300",
    bgSolid: "bg-purple-500", connector: "bg-purple-300", activeBg: "bg-purple-50",
    progressBg: "bg-purple-100", progressFill: "bg-purple-500",
  },
  green: {
    bg: "bg-green-100", text: "text-green-600", ring: "ring-green-300",
    bgSolid: "bg-green-500", connector: "bg-green-300", activeBg: "bg-green-50",
    progressBg: "bg-green-100", progressFill: "bg-green-500",
  },
  red: {
    bg: "bg-red-100", text: "text-red-600", ring: "ring-red-300",
    bgSolid: "bg-red-500", connector: "bg-red-300", activeBg: "bg-red-50",
    progressBg: "bg-red-100", progressFill: "bg-red-500",
  },
};
