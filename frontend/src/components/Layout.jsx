import { NavLink, Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="dot" />
          AgentGraph
        </div>
        <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
          Dashboard
        </NavLink>
        <NavLink to="/failures" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
          Failure Patterns
        </NavLink>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
