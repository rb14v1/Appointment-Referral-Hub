import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { extractErrorMessage } from "../../../api/client";
import { listClinics } from "../../../api/endpoints/clinics";
import { getMyPatientProfile, listPatients } from "../../../api/endpoints/patients";
import { listProviders } from "../../../api/endpoints/providers";
import { createReferral } from "../../../api/endpoints/referrals";
import { useAuth } from "../../../auth/AuthContext";
import type { Clinic, Patient, Provider } from "../../../types";

export function CreateReferralPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isStaff = Boolean(user && ["front_desk", "clinician", "admin"].includes(user.role));

  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [myPatient, setMyPatient] = useState<Patient | null>(null);

  const [patientId, setPatientId] = useState<number | "">("");
  const [referringClinicId, setReferringClinicId] = useState<number | "">("");
  const [referringProviderId, setReferringProviderId] = useState<number | "">("");
  const [receivingClinicId, setReceivingClinicId] = useState<number | "">("");
  const [reason, setReason] = useState("");
  const [urgency, setUrgency] = useState<"routine" | "urgent">("routine");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    listClinics().then((res) => setClinics(res.data.results));
    if (isStaff) {
      listPatients().then((res) => setPatients(res.data.results));
    } else {
      getMyPatientProfile().then(setMyPatient);
    }
  }, [isStaff]);

  useEffect(() => {
    if (!referringClinicId) {
      setProviders([]);
      return;
    }
    listProviders({ home_clinic: referringClinicId as number }).then((res) => setProviders(res.data.results));
  }, [referringClinicId]);

  async function handleSubmit() {
    setError(null);
    const effectivePatientId = isStaff ? patientId : myPatient?.id;
    if (!effectivePatientId || !referringClinicId || !receivingClinicId || !reason) {
      setError("Please fill in patient, both clinics, and a reason.");
      return;
    }
    try {
      await createReferral({
        patient: effectivePatientId as number,
        referring_clinic: referringClinicId as number,
        referring_provider: referringProviderId ? (referringProviderId as number) : undefined,
        receiving_clinic: receivingClinicId as number,
        reason,
        urgency,
      });
      setSuccess(true);
      setTimeout(() => navigate("/referrals"), 800);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h1>Create Referral</h1>
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
          Referring clinic
          <select
            value={referringClinicId}
            onChange={(e) => setReferringClinicId(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="">Select a clinic</option>
            {clinics.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Referring provider (optional)
          <select
            value={referringProviderId}
            onChange={(e) => setReferringProviderId(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="">None</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.user_detail?.first_name} {p.user_detail?.last_name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Receiving clinic
          <select
            value={receivingClinicId}
            onChange={(e) => setReceivingClinicId(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="">Select a clinic</option>
            {clinics
              .filter((c) => c.id !== referringClinicId)
              .map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
          </select>
        </label>

        <label>
          Urgency
          <select value={urgency} onChange={(e) => setUrgency(e.target.value as "routine" | "urgent")}>
            <option value="routine">Routine</option>
            <option value="urgent">Urgent</option>
          </select>
        </label>

        <label className="full-width">
          Reason
          <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={3} />
        </label>
      </div>

      {error && <p className="error-text">{error}</p>}
      {success && <p className="success-text">Referral created.</p>}
      <button onClick={handleSubmit}>Create Referral</button>
    </div>
  );
}
