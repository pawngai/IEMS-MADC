import { AlertCircle, Inbox, Loader2, ShieldAlert } from "lucide-react";

export function LoadingState({ title = "Loading", message = "Please wait while the latest data is loaded." }) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white p-6 text-center">
      <Loader2 className="h-6 w-6 animate-spin text-slate-500" aria-hidden="true" />
      <div>
        <div className="text-sm font-medium text-slate-900">{title}</div>
        <div className="mt-1 text-sm text-slate-500">{message}</div>
      </div>
    </div>
  );
}

export function EmptyState({ title = "No records", message = "There is nothing to show yet." }) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
      <Inbox className="h-6 w-6 text-slate-500" aria-hidden="true" />
      <div>
        <div className="text-sm font-medium text-slate-900">{title}</div>
        <div className="mt-1 text-sm text-slate-500">{message}</div>
      </div>
    </div>
  );
}

export function ErrorState({ title = "Something went wrong", message = "Please try again." }) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center gap-3 rounded-lg border border-red-200 bg-red-50 p-6 text-center">
      <AlertCircle className="h-6 w-6 text-red-600" aria-hidden="true" />
      <div>
        <div className="text-sm font-medium text-red-900">{title}</div>
        <div className="mt-1 text-sm text-red-700">{message}</div>
      </div>
    </div>
  );
}

export function PermissionDeniedState({ title = "Access denied", message = "You do not have permission to view this area." }) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center gap-3 rounded-lg border border-amber-200 bg-amber-50 p-6 text-center">
      <ShieldAlert className="h-6 w-6 text-amber-600" aria-hidden="true" />
      <div>
        <div className="text-sm font-medium text-amber-900">{title}</div>
        <div className="mt-1 text-sm text-amber-700">{message}</div>
      </div>
    </div>
  );
}
