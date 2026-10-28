import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { bookAppointment } from "../../../api/endpoints/appointments";
import { extractErrorMessage } from "../../../api/client";
import { listClinics } from "../../../api/endpoints/clinics";
import { listPatients, getMyPatientProfile } from "../../../api/endpoints/patients";
import { getSlots, listProviders } from "../../../api/endpoints/providers";
import { useAuth } from "../../../auth/AuthContext";
import type { Clinic, Patient, Provider, Slot } from "../../../types";
import { formatTimeInTimezone } from "../../../utils/timezone";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function addDaysISO(days: number) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export function BookAppointmentPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isStaff = user && ["front_desk", "clinician", "admin"].includes(user.role);

  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [myPatient, setMyPatient] = useState<Patient | null>(null);

  const [clinicId, setClinicId] = useState<number | "">("");
  const [providerId, setProviderId] = useState<number | "">("");
  const [patientId, setPatientId] = useState<number | "">("");
  const [reason, setReason] = useState("");
  const [slots, setSlots] = useState<Slot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const selectedClinic = useMemo(() => clinics.find((c) => c.id === clinicId) ?? null, [clinics, clinicId]);

  useEffect(() => {
    listClinics().then((res) => setClinics(res.data.results));
    if (isStaff) {
      listPatients().then((res) => setPatients(res.data.results));
    } else {
      getMyPatientProfile().then(setMyPatient);
    }
  }, [isStaff]);

  useEffect(() => {
    if (!clinicId) {
      setProviders([]);
      return;
    }
    listProviders({ home_clinic: clinicId as number }).then((res) => setProviders(res.data.results));
  }, [clinicId]);

  useEffect(() => {
    setSlots([]);
    setSelectedSlot(null);
    if (!providerId) return;
    getSlots(providerId as number, todayISO(), addDaysISO(14), clinicId ? (clinicId as number) : undefined).then((res) =>
      setSlots(res.data)
    );
  }, [providerId, clinicId]);

  async function handleBook() {
    setError(null);
    setSuccess(null);
    const effectivePatientId = isStaff ? patientId : myPatient?.id;
    if (!effectivePatientId || !providerId || !clinicId || !selectedSlot) {
      setError("Please select a clinic, provider, patient, and time slot.");
      return;
    }
    setSubmitting(true);
    try {
      await bookAppointment({
        patient: effectivePatientId as number,
        provider: providerId as number,
        clinic: clinicId as number,
        start_time: selectedSlot.start_time,
        reason,
      });
      setSuccess("Appointment booked.");
      setTimeout(() => navigate("/appointments"), 800);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>Book an Appointment</h1>

      <div className="form-grid">
        <label>
          Clinic
          <select value={clinicId} onChange={(e) => setClinicId(e.target.value ? Number(e.target.value) : "")}>
            <option value="">Select a clinic</option>
            {clinics.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.timezone})
              </option>
            ))}
          </select>
        </label>

        <label>
          Provider
          <select
            value={providerId}
            onChange={(e) => setProviderId(e.target.value ? Number(e.target.value) : "")}
            disabled={!clinicId}
          >
            <option value="">Select a provider</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.user_detail?.first_name} {p.user_detail?.last_name} - {p.specialty}
              </option>
            ))}
          </select>
        </label>

        {isStaff && (
          <label>
            Patient
            <select value={patientId} onChange={(e) => setPatientId(e.target.value ? Number(e.target.value) : "")}>
              <option value="">Select a patient</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.user_detail?.first_name} {p.user_detail?.last_name} ({p.user_detail?.email})
                </option>
              ))}
            </select>
          </label>
        )}

        <label>
          Reason
          <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason for visit" />
        </label>
      </div>

      {providerId && (
        <div className="slots-section">
          <h2>Available slots (next 14 days){selectedClinic ? ` - ${selectedClinic.timezone}` : ""}</h2>
          {slots.length === 0 && <p>No open slots in this window.</p>}
          <div className="slot-grid">
            {slots.map((slot) => (
              <button
                key={slot.start_time}
                className={`slot-chip ${selectedSlot?.start_time === slot.start_time ? "slot-chip-selected" : ""}`}
                onClick={() => setSelectedSlot(slot)}
              >
                {new Date(slot.start_time).toLocaleDateString()}{" "}
                {formatTimeInTimezone(slot.start_time, selectedClinic?.timezone ?? "UTC")}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && <p className="error-text">{error}</p>}
      {success && <p className="success-text">{success}</p>}

      <button disabled={!selectedSlot || submitting} onClick={handleBook}>
        {submitting ? "Booking..." : "Book Appointment"}
      </button>
    </div>
  );
}
