import type { ReactNode } from "react";

export type DenseColumn<T> = {
  key: string;
  header: string;
  width?: string;
  cell: (row: T, index: number) => ReactNode;
};

export function DenseTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  selectedKey,
  empty,
}: {
  columns: DenseColumn<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  onRowClick?: (row: T, index: number) => void;
  selectedKey?: string | null;
  empty?: ReactNode;
}) {
  if (rows.length === 0) {
    return <div className="term-dense-empty">{empty ?? "—"}</div>;
  }
  return (
    <div className="term-dense-table-wrap">
      <table className="term-dense-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} style={c.width ? { width: c.width } : undefined}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const k = rowKey(row, i);
            return (
              <tr
                key={k}
                className={selectedKey === k ? "term-dense-table__row--selected" : undefined}
                onClick={onRowClick ? () => onRowClick(row, i) : undefined}
                onKeyDown={
                  onRowClick
                    ? (e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          onRowClick(row, i);
                        }
                      }
                    : undefined
                }
                tabIndex={onRowClick ? 0 : undefined}
                role={onRowClick ? "button" : undefined}
              >
                {columns.map((c) => (
                  <td key={c.key}>{c.cell(row, i)}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
