import { Navigate, createBrowserRouter } from "react-router-dom";

import { RequireAuth, RequireRole } from "../auth/RequireRole";
import { useAuth } from "../auth/AuthContext";
import { AppointmentsListPage } from "../features/appointments/pages/AppointmentsListPage";
import { BookAppointmentPage } from "../features/appointments/pages/BookAppointmentPage";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { AvailabilityPage } from "../features/availability/pages/AvailabilityPage";
import { ClinicsPage } from "../features/clinics/pages/ClinicsPage";
import { CreateReferralPage } from "../features/referrals/pages/CreateReferralPage";
import { ReferralsListPage } from "../features/referrals/pages/ReferralsListPage";
import { WaitlistPage } from "../features/waitlist/pages/WaitlistPage";
import { AdminLayout } from "../layouts/AdminLayout";
import { PatientLayout } from "../layouts/PatientLayout";
import { StaffLayout } from "../layouts/StaffLayout";

function RoleHome() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to="/appointments" replace />;
}

function RoleLayout() {
  const { user } = useAuth();
  if (user?.role === "admin") return <AdminLayout />;
  if (user?.role === "front_desk" || user?.role === "clinician") return <StaffLayout />;
  return <PatientLayout />;
}

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: (
      <RequireAuth>
        <RoleLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <RoleHome /> },
      { path: "appointments", element: <AppointmentsListPage /> },
      { path: "book", element: <BookAppointmentPage /> },
      { path: "referrals", element: <ReferralsListPage /> },
      { path: "referrals/new", element: <CreateReferralPage /> },
      { path: "waitlist", element: <WaitlistPage /> },
      {
        path: "availability",
        element: (
          <RequireRole roles={["clinician"]}>
            <AvailabilityPage />
          </RequireRole>
        ),
      },
      {
        path: "clinics",
        element: (
          <RequireRole roles={["admin"]}>
            <ClinicsPage />
          </RequireRole>
        ),
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
