import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { TableSkeleton } from "@/shared/ui/skeletons";
import { cn } from "@/shared/lib/utils";

/**
 * Declarative data table following the app's directory/work-queue idiom:
 * shadcn table primitives, responsive column hiding via column className,
 * skeleton while loading, caller-supplied empty state.
 *
 * columns: [{ key, header, className?, headClassName?, render?(row) }]
 * - className applies to body cells and (unless headClassName is given)
 *   to the header cell, so responsive `hidden sm:table-cell` stays in sync.
 */
export function DataTable({
  columns,
  rows,
  rowKey,
  loading = false,
  skeletonRows = 5,
  emptyState = null,
  onRowClick,
  rowClassName,
  "data-testid": dataTestId,
}) {
  if (loading) {
    return <TableSkeleton rows={skeletonRows} columns={columns.length} />;
  }
  if (!rows || rows.length === 0) {
    return emptyState;
  }

  return (
    <div className="overflow-x-auto -mx-4 sm:mx-0" data-testid={dataTestId}>
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column) => (
              <TableHead key={column.key} className={column.headClassName ?? column.className}>
                {column.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow
              key={rowKey(row)}
              className={cn(
                onRowClick && "cursor-pointer",
                typeof rowClassName === "function" ? rowClassName(row) : rowClassName,
              )}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {columns.map((column) => (
                <TableCell key={column.key} className={column.className}>
                  {column.render ? column.render(row) : row[column.key]}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export default DataTable;
