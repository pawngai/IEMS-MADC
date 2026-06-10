import {
  Building2,
  Database,
  Shield,
  Users,
} from "lucide-react";

export const ALLOWED_TABS = [
  { id: "policy-masters", label: "Policy Masters", icon: Database },
  { id: "user-mgmt", label: "User Management", icon: Users },
  { id: "role-mgmt", label: "Role Management", icon: Shield },
  { id: "dept-roles", label: "Department Roles", icon: Building2 },
];

export const SYSTEM_MANAGED_MASTERS = [
  { id: "employment_type", name: "Employment Types", description: "REGULAR, CONTRACTUAL, etc." },
  { id: "pay_level", name: "Pay Levels", description: "7th CPC Pay Matrix levels" },
  { id: "service_event_type", name: "Service Event Types", description: "APPOINTMENT, TRANSFER, etc." },
  { id: "leave_type", name: "Leave Types", description: "CL, EL, HPL, CCL, etc." },
  { id: "department", name: "Departments", description: "Departments with optional parent department linkage" },
  { id: "designation", name: "Designations", description: "Job titles and post designations" },
  { id: "caste_category", name: "Caste Categories", description: "Reservation categories (GEN, SC, ST, OBC, etc.)" },
  { id: "service_group", name: "Service Groups", description: "GRP-A, GRP-B, GRP-C, GRP-D" },
  { id: "service", name: "Services", description: "MINISTERIAL, ENGINEERING, GENERAL" },
  { id: "document_type", name: "Document Types", description: "Order types, certificates" },
  { id: "qualification", name: "Qualifications", description: "Educational qualifications" },
  { id: "role", name: "Roles", description: "System roles and authorities" },
  {
    id: "workflow_stage",
    name: "Workflow Stages",
    description: "Derived from the runtime workflow model",
    readOnly: true,
    readOnlyReason: "Derived from RBAC workflow enums and transitions; not editable here.",
  },
];

export const SERVICE_EVENT_PARTS = [
  { value: "I", label: "I - Bio-Data" },
  { value: "II-A", label: "II-A - Service Book Records" },
  { value: "II-B", label: "II-B - Pay & Allowances" },
  { value: "III", label: "III - Leave Account" },
  { value: "IV", label: "IV - Disciplinary" },
  { value: "V", label: "V - Retirement & Pension" },
];
