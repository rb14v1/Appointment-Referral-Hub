import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function PatientLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">Appointment & Referral Hub</div>
        <nav>
          <NavLink to="/appointments">My Appointments</NavLink>
          <NavLink to="/book">Book Appointment</NavLink>
          <NavLink to="/referrals">My Referrals</NavLink>
          <NavLink to="/waitlist">Waitlist</NavLink>
        </nav>
        <div className="header-user">
          <span>{user?.email}</span>
          <button onClick={logout}>Log out</button>
        </div>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
