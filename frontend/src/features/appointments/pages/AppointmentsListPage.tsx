import { useState } from "react";

import { extractErrorMessage } from "../../../api/client";
import {
  cancelAppointment,
  checkInAppointment,
  completeAppointment,
  markNoShow,
} from "../../../api/endpoints/appointments";
import { useAuth } from "../../../auth/AuthContext";
import { formatInTimezone } from "../../../utils/timezone";
import { useAppointments } from "../hooks/useAppointments";

export function AppointmentsListPage() {
  const { user } = useAuth();
  const { appointments, loading, error, reload } = useAppointments();
  const [actionError, setActionError] = useState<string | null>(null);
  const isStaff = Boolean(user && ["front_desk", "clinician", "admin"].includes(user.role));

  async function runAction(fn: () => Promise<unknown>) {
    setActionError(null);
    try {
      await fn();
      await reload();
    } catch (err) {
      setActionError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h1>Appointments</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="error-text">{error}</p>}
      {actionError && <p className="error-text">{actionError}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Patient</th>
            <th>Provider</th>
            <th>Clinic</th>
            <th>When (clinic local)</th>
            <th>Status</th>
            <th>Reason</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {appointments.map((appt) => (
            <tr key={appt.id}>
              <td>{appt.patient_name}</td>
              <td>{appt.provider_name}</td>
              <td>{appt.clinic_name}</td>
              <td>{formatInTimezone(appt.start_time, Intl.DateTimeFormat().resolvedOptions().timeZone)}</td>
              <td>
                <span className={`status-badge status-${appt.status}`}>{appt.status}</span>
              </td>
              <td>{appt.reason}</td>
              <td className="action-cell">
                {isStaff && appt.status === "confirmed" && (
                  <>
                    <button onClick={() => runAction(() => checkInAppointment(appt.id))}>Check in</button>
                    <button onClick={() => runAction(() => cancelAppointment(appt.id))}>Cancel</button>
                    <button onClick={() => runAction(() => markNoShow(appt.id))}>No-show</button>
                  </>
                )}
                {isStaff && appt.status === "checked_in" && (
                  <button onClick={() => runAction(() => completeAppointment(appt.id))}>Complete</button>
                )}
                {(appt.status === "requested" || (!isStaff && appt.status === "confirmed")) && (
                  <button onClick={() => runAction(() => cancelAppointment(appt.id))}>Cancel</button>
                )}
              </td>
            </tr>
          ))}
          {appointments.length === 0 && !loading && (
            <tr>
              <td colSpan={7}>No appointments yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
