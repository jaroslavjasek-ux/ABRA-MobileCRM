export function KvGrid({ rows }: { rows: { label: string; value: string }[] }) {
  if (rows.length === 0) {
    return null;
  }

  return (
    <dl className="kv-grid">
      {rows.map((row) => (
        <div key={row.label} className="kv-row">
          <dt>{row.label}</dt>
          <dd>{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}
