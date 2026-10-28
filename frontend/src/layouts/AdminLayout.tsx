import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function AdminLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">Appointment & Referral Hub - Admin</div>
        <nav>
          <NavLink to="/clinics">Clinics</NavLink>
          <NavLink to="/appointments">Appointments</NavLink>
          <NavLink to="/referrals">Referrals</NavLink>
          <NavLink to="/waitlist">Waitlist</NavLink>
        </nav>
        <div className="header-user">
          <span>{user?.email} (admin)</span>
          <button onClick={logout}>Log out</button>
        </div>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
