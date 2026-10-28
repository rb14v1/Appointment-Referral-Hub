import { useEffect, useState } from "react";

import { extractErrorMessage } from "../../../api/client";
import { listClinics } from "../../../api/endpoints/clinics";
import { getMyPatientProfile, listPatients } from "../../../api/endpoints/patients";
import { listProviders } from "../../../api/endpoints/providers";
import { joinWaitlist, listWaitlist, listWaitlistOffers, respondToOffer } from "../../../api/endpoints/waitlist";
import { useAuth } from "../../../auth/AuthContext";
import type { Clinic, Patient, Provider, WaitlistEntry, WaitlistOffer } from "../../../types";

function addDaysISO(days: number) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export function WaitlistPage() {
  const { user } = useAuth();
  const isStaff = Boolean(user && ["front_desk", "clinician", "admin"].includes(user.role));

  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [myPatient, setMyPatient] = useState<Patient | null>(null);
  const [entries, setEntries] = useState<WaitlistEntry[]>([]);
  const [offers, setOffers] = useState<WaitlistOffer[]>([]);

  const [clinicId, setClinicId] = useState<number | "">("");
  const [providerId, setProviderId] = useState<number | "">("");
  const [patientId, setPatientId] = useState<number | "">("");
  const [rangeStart, setRangeStart] = useState(addDaysISO(0));
  const [rangeEnd, setRangeEnd] = useState(addDaysISO(30));
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  function reload() {
    listWaitlist().then((res) => setEntries(res.data.results));
    listWaitlistOffers({ response: "pending" }).then((res) => setOffers(res.data.results));
  }

  useEffect(() => {
    listClinics().then((res) => setClinics(res.data.results));
    if (isStaff) {
      listPatients().then((res) => setPatients(res.data.results));
    } else {
      getMyPatientProfile().then(setMyPatient);
    }
    reload();
  }, [isStaff]);

  useEffect(() => {
    if (!clinicId) {
      setProviders([]);
      return;
    }
    listProviders({ home_clinic: clinicId as number }).then((res) => setProviders(res.data.results));
  }, [clinicId]);

  async function handleJoin() {
    setError(null);
    setSuccess(null);
    const effectivePatientId = isStaff ? patientId : myPatient?.id;
    if (!effectivePatientId || !clinicId) {
      setError("Please choose a patient and a clinic.");
      return;
    }
    try {
      await joinWaitlist({
        patient: effectivePatientId as number,
        clinic: clinicId as number,
        provider: providerId ? (providerId as number) : undefined,
        desired_date_range_start: rangeStart,
        desired_date_range_end: rangeEnd,
      });
      setSuccess("Added to the waitlist.");
      reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleRespond(offerId: number, accept: boolean) {
    setError(null);
    try {
      await respondToOffer(offerId, accept);
      reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h1>Waitlist</h1>

      {offers.length > 0 && (
        <div className="card">
          <h2>Pending offers</h2>
          {offers.map((offer) => (
            <div key={offer.id} className="offer-row">
              <span>
                Slot: {new Date(offer.start_time).toLocaleString()} (expires {new Date(offer.expires_at).toLocaleString()})
              </span>
              <button onClick={() => handleRespond(offer.id, true)}>Accept</button>
              <button onClick={() => handleRespond(offer.id, false)}>Decline</button>
            </div>
          ))}
        </div>
      )}

      <h2>Join the waitlist</h2>
      <div className="form-grid">
        {isStaff && (
          <label>
            Patient
            <select value={patientId} onChange={(e) => setPatientId(e.target.value ? Number(e.target.value) : "")}>
              <option value="">Select a patient</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.user_detail?.first_name} {p.user_detail?.last_name}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          Clinic
          <select value={clinicId} onChange={(e) => setClinicId(e.target.value ? Number(e.target.value) : "")}>
            <option value="">Select a clinic</option>
            {clinics.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Provider (optional)
          <select value={providerId} onChange={(e) => setProviderId(e.target.value ? Number(e.target.value) : "")}>
            <option value="">Any provider</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.user_detail?.first_name} {p.user_detail?.last_name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Earliest date
          <input type="date" value={rangeStart} onChange={(e) => setRangeStart(e.target.value)} />
        </label>
        <label>
          Latest date
          <input type="date" value={rangeEnd} onChange={(e) => setRangeEnd(e.target.value)} />
        </label>
      </div>
      <button onClick={handleJoin}>Join Waitlist</button>
      {error && <p className="error-text">{error}</p>}
      {success && <p className="success-text">{success}</p>}

      <h2>Waitlist entries</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Clinic</th>
            <th>Provider</th>
            <th>Desired range</th>
            <th>Status</th>
            <th>Priority</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.id}>
              <td>{clinics.find((c) => c.id === entry.clinic)?.name ?? entry.clinic}</td>
              <td>{entry.provider ?? "Any"}</td>
              <td>
                {entry.desired_date_range_start} to {entry.desired_date_range_end}
              </td>
              <td>
                <span className={`status-badge status-${entry.status}`}>{entry.status}</span>
              </td>
              <td>{entry.priority}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
