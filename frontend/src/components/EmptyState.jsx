export default function EmptyState({ label = "Nothing here yet", detail }) {
  return (
    <div className="state-screen">
      <div className="state-label">{label}</div>
      {detail && <div className="text-muted">{detail}</div>}
    </div>
  );
}
