export default function LoadingState({ label = "Loading" }) {
  return (
    <div className="state-screen">
      <div className="spinner" />
      <div className="state-label">{label}</div>
    </div>
  );
}
