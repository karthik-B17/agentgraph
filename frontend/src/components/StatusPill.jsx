export default function StatusPill({ status }) {
  const normalized = (status || "pending").toLowerCase();
  return (
    <span className={`status-pill ${normalized}`}>
      <span className="dot" />
      {normalized}
    </span>
  );
}
