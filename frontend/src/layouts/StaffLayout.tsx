import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function StaffLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">Appointment & Referral Hub - Staff</div>
        <nav>
          <NavLink to="/appointments">Appointments</NavLink>
          <NavLink to="/book">Book</NavLink>
          <NavLink to="/referrals">Referrals</NavLink>
          <NavLink to="/waitlist">Waitlist</NavLink>
          {user?.role === "clinician" && <NavLink to="/availability">My Availability</NavLink>}
        </nav>
        <div className="header-user">
          <span>
            {user?.email} ({user?.role})
          </span>
          <button onClick={logout}>Log out</button>
        </div>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
