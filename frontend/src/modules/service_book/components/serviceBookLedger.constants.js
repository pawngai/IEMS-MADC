import {
  FileText,
  User,
  Award,
  Briefcase,
  CheckCircle,
  Calendar,
  DollarSign,
  Shield,
  Building,
} from "lucide-react";
import { WorkflowState } from "@/modules/service_book/model/serviceBookModel";

export const WORKFLOW_STATUS_STYLES = {
  [WorkflowState.DRAFT]: "bg-gray-100 text-gray-700 border-gray-300",
  [WorkflowState.SUBMITTED]: "bg-blue-100 text-blue-700 border-blue-300",
  [WorkflowState.VERIFIED]: "bg-indigo-100 text-indigo-700 border-indigo-300",
  [WorkflowState.APPROVED]: "bg-green-100 text-green-700 border-green-300",
  [WorkflowState.LOCKED]: "bg-emerald-100 text-emerald-800 border-emerald-300",
  [WorkflowState.REJECTED]: "bg-red-100 text-red-700 border-red-300",
  [WorkflowState.SUPERSEDED]: "bg-amber-100 text-amber-700 border-amber-300",
};

export const PART_ICONS = {
  I: User,
  "II-A": Award,
  "II-B": FileText,
  III: Building,
  IV: Briefcase,
  V: CheckCircle,
  VI: Calendar,
  VII: DollarSign,
  VIII: Shield,
};

export const PART_COLORS = {
  I: "bg-blue-100 text-blue-700 border-blue-200",
  "II-A": "bg-purple-100 text-purple-700 border-purple-200",
  "II-B": "bg-indigo-100 text-indigo-700 border-indigo-200",
  III: "bg-teal-100 text-teal-700 border-teal-200",
  IV: "bg-amber-100 text-amber-700 border-amber-200",
  V: "bg-green-100 text-green-700 border-green-200",
  VI: "bg-cyan-100 text-cyan-700 border-cyan-200",
  VII: "bg-orange-100 text-orange-700 border-orange-200",
  VIII: "bg-red-100 text-red-700 border-red-200",
};

export const PART_NAMES = {
  I: "Bio-Data",
  "II-A": "Immutable Certificates",
  "II-B": "Mutable Certificates",
  III: "Previous Service",
  IV: "Service History",
  V: "Verification",
  VI: "Leave Account",
  VII: "Other Records",
  VIII: "Audit Comments",
};

export const APPEND_ONLY_PARTS = new Set(["IV", "VI", "VIII"]);
