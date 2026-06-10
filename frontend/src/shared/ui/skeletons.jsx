import { cn } from "@/shared/lib/utils";
import { Skeleton } from "@/shared/ui/skeleton";

/**
 * Reusable skeleton layouts for consistent loading states.
 * Replace full-page spinners with content-shaped placeholders.
 */

/** A single text line skeleton */
const SkeletonLine = ({ className, width = "w-full" }) => (
  <Skeleton className={cn("h-4 rounded", width, className)} />
);

/** Page header skeleton (title + subtitle + action buttons) */
const PageHeaderSkeleton = ({ className }) => (
  <div className={cn("flex flex-col lg:flex-row lg:items-end justify-between gap-4", className)}>
    <div className="space-y-2">
      <Skeleton className="h-3 w-16 rounded" />
      <Skeleton className="h-8 w-64 rounded" />
      <Skeleton className="h-4 w-40 rounded" />
    </div>
    <div className="flex gap-2">
      <Skeleton className="h-9 w-28 rounded-md" />
      <Skeleton className="h-9 w-24 rounded-md" />
    </div>
  </div>
);

/** Stat card skeleton (icon + value + label) */
const StatCardSkeleton = ({ className }) => (
  <div className={cn("rounded-xl border bg-white p-6", className)}>
    <div className="flex items-center justify-between">
      <div className="space-y-2">
        <Skeleton className="h-3 w-24 rounded" />
        <Skeleton className="h-7 w-12 rounded" />
        <Skeleton className="h-3 w-20 rounded" />
      </div>
      <Skeleton className="h-11 w-11 rounded-full" />
    </div>
  </div>
);

/** Grid of stat cards */
const StatGridSkeleton = ({ count = 4, className }) => (
  <div className={cn("grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4", className)}>
    {Array.from({ length: count }).map((_, i) => (
      <StatCardSkeleton key={i} />
    ))}
  </div>
);

/** Table skeleton with configurable rows and columns */
const TableSkeleton = ({ rows = 8, columns = 5, className }) => (
  <div className={cn("rounded-xl border bg-white overflow-hidden shadow-sm", className)}>
    {/* Header */}
    <div className="flex items-center gap-4 px-4 py-3 bg-slate-50/80 border-b">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} className={cn("h-4 rounded", i === 0 ? "w-[30%]" : "w-[15%]")} />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, row) => (
      <div key={row} className="flex items-center gap-4 px-4 py-3 border-b last:border-b-0">
        {row === 0 || Math.random() > 0.5 ? null : null}
        {Array.from({ length: columns }).map((_, col) => (
          <Skeleton
            key={col}
            className={cn(
              "h-4 rounded",
              col === 0 ? "w-[30%]" : col === columns - 1 ? "w-[10%]" : "w-[15%]"
            )}
          />
        ))}
      </div>
    ))}
  </div>
);

/** Employee table row skeleton (avatar + name + columns) */
const EmployeeTableSkeleton = ({ rows = 10, className }) => (
  <div className={cn("rounded-xl border bg-white overflow-hidden shadow-sm", className)}>
    {/* Header */}
    <div className="flex items-center gap-4 px-4 py-3 bg-slate-50/80 border-b">
      <Skeleton className="h-4 w-[35%] rounded" />
      <Skeleton className="h-4 w-[12%] rounded hidden sm:block" />
      <Skeleton className="h-4 w-[10%] rounded hidden md:block" />
      <Skeleton className="h-4 w-[18%] rounded hidden lg:block" />
      <Skeleton className="h-4 w-[10%] rounded" />
      <Skeleton className="h-4 w-[10%] rounded" />
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex items-center gap-4 px-4 py-3 border-b last:border-b-0">
        <div className="flex items-center gap-3 w-[35%]">
          <Skeleton className="w-9 h-9 rounded-full flex-shrink-0" />
          <div className="space-y-1.5 flex-1 min-w-0">
            <Skeleton className="h-4 w-3/4 rounded" />
            <Skeleton className="h-3 w-1/2 rounded" />
          </div>
        </div>
        <Skeleton className="h-4 w-[12%] rounded hidden sm:block" />
        <Skeleton className="h-5 w-[10%] rounded-full hidden md:block" />
        <Skeleton className="h-4 w-[18%] rounded hidden lg:block" />
        <Skeleton className="h-5 w-[10%] rounded-full" />
        <Skeleton className="h-8 w-[10%] rounded" />
      </div>
    ))}
  </div>
);

/** Profile page skeleton (header + tabs + content) */
const ProfileSkeleton = ({ className }) => (
  <div className={cn("space-y-6", className)}>
    {/* Profile header */}
    <div className="flex flex-col sm:flex-row gap-4">
      <Skeleton className="w-20 h-20 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-7 w-48 rounded" />
        <div className="flex gap-2">
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-5 w-24 rounded-full" />
        </div>
        <Skeleton className="h-4 w-64 rounded" />
      </div>
    </div>
    {/* Tabs */}
    <div className="flex gap-2 border-b pb-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-8 w-24 rounded" />
      ))}
    </div>
    {/* Content */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="space-y-1.5">
          <Skeleton className="h-3 w-20 rounded" />
          <Skeleton className="h-5 w-full rounded" />
        </div>
      ))}
    </div>
  </div>
);

/** Card content skeleton */
const CardSkeleton = ({ lines = 3, className }) => (
  <div className={cn("rounded-xl border bg-white p-6 space-y-3", className)}>
    <Skeleton className="h-5 w-36 rounded" />
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        className={cn("h-4 rounded", i === lines - 1 ? "w-2/3" : "w-full")}
      />
    ))}
  </div>
);

/** Dashboard skeleton (header + stats + cards) */
const DashboardSkeleton = ({ className }) => (
  <div className={cn("space-y-6", className)}>
    <PageHeaderSkeleton />
    <StatGridSkeleton />
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <CardSkeleton lines={4} />
      <CardSkeleton lines={4} />
    </div>
  </div>
);

/** Search bar skeleton */
const SearchBarSkeleton = ({ className }) => (
  <div className={cn("flex flex-col sm:flex-row gap-3 items-start sm:items-center", className)}>
    <Skeleton className="h-9 w-full max-w-md rounded-md" />
    <div className="flex gap-1.5">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-7 w-16 rounded-full" />
      ))}
    </div>
  </div>
);

/** Form field skeleton */
const FormFieldSkeleton = ({ className }) => (
  <div className={cn("space-y-1.5", className)}>
    <Skeleton className="h-3.5 w-24 rounded" />
    <Skeleton className="h-9 w-full rounded-md" />
  </div>
);

/** Form skeleton with multiple fields */
const FormSkeleton = ({ fields = 4, columns = 1, className }) => (
  <div className={cn(
    "space-y-4",
    columns === 2 && "grid grid-cols-1 sm:grid-cols-2 gap-4 space-y-0",
    className
  )}>
    {Array.from({ length: fields }).map((_, i) => (
      <FormFieldSkeleton key={i} />
    ))}
  </div>
);

/** Work queue item skeleton */
const WorkQueueSkeleton = ({ items = 6, className }) => (
  <div className={cn("space-y-3", className)}>
    {Array.from({ length: items }).map((_, i) => (
      <div key={i} className="flex items-center gap-3 p-3 rounded-lg border bg-white">
        <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
        <div className="flex-1 space-y-1.5 min-w-0">
          <Skeleton className="h-4 w-3/4 rounded" />
          <Skeleton className="h-3 w-1/2 rounded" />
        </div>
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="h-8 w-20 rounded-md" />
      </div>
    ))}
  </div>
);

export {
  SkeletonLine,
  PageHeaderSkeleton,
  StatCardSkeleton,
  StatGridSkeleton,
  TableSkeleton,
  EmployeeTableSkeleton,
  ProfileSkeleton,
  CardSkeleton,
  DashboardSkeleton,
  SearchBarSkeleton,
  FormFieldSkeleton,
  FormSkeleton,
  WorkQueueSkeleton,
};
