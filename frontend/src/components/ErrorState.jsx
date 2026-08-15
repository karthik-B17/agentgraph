export default function ErrorState({ error }) {
  const message =
    error?.response?.status === 503
      ? "The database is unreachable right now. Check that CognoDB is running, then retry."
      : error?.response?.status === 404
      ? "That item couldn't be found. It may have been removed."
      : "Something went wrong loading this data.";

  return (
    <div className="state-screen error">
      <div className="state-label">Error</div>
      <div>{message}</div>
    </div>
  );
}
