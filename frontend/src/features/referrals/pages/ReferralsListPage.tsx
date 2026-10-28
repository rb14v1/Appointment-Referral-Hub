import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { extractErrorMessage } from "../../../api/client";
import { acceptReferral, cancelReferral, listReferrals, rejectReferral } from "../../../api/endpoints/referrals";
import { useAuth } from "../../../auth/AuthContext";
import type { Referral } from "../../../types";
import { ScheduleReferralForm } from "../components/ScheduleReferralForm";

export function ReferralsListPage() {
  const { user } = useAuth();
  const isStaff = Boolean(user && ["front_desk", "clinician", "admin"].includes(user.role));
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [schedulingId, setSchedulingId] = useState<number | null>(null);

  function reload() {
    listReferrals()
      .then((res) => setReferrals(res.data.results))
      .catch((err) => setError(extractErrorMessage(err)));
  }

  useEffect(reload, []);

  async function runAction(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
      reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="page-header-row">
        <h1>Referrals</h1>
        <Link to="/referrals/new" className="button-link">
          + New Referral
        </Link>
      </div>
      {error && <p className="error-text">{error}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Patient</th>
            <th>From clinic</th>
            <th>To clinic</th>
            <th>Reason</th>
            <th>Urgency</th>
            <th>Status</th>
            {isStaff && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {referrals.map((referral) => (
            <tr key={referral.id}>
              <td>{referral.patient_name}</td>
              <td>{referral.referring_clinic}</td>
              <td>{referral.receiving_clinic}</td>
              <td>{referral.reason}</td>
              <td>{referral.urgency}</td>
              <td>
                <span className={`status-badge status-${referral.status}`}>{referral.status}</span>
              </td>
              {isStaff && (
                <td className="action-cell">
                  {referral.status === "pending" && (
                    <>
                      <button onClick={() => runAction(() => acceptReferral(referral.id))}>Accept</button>
                      <button onClick={() => runAction(() => rejectReferral(referral.id))}>Reject</button>
                    </>
                  )}
                  {referral.status === "accepted" && schedulingId !== referral.id && (
                    <button onClick={() => setSchedulingId(referral.id)}>Schedule</button>
                  )}
                  {referral.status === "accepted" && schedulingId === referral.id && (
                    <ScheduleReferralForm
                      referral={referral}
                      onDone={() => {
                        setSchedulingId(null);
                        reload();
                      }}
                    />
                  )}
                  {(referral.status === "pending" || referral.status === "accepted") && (
                    <button onClick={() => runAction(() => cancelReferral(referral.id))}>Cancel</button>
                  )}
                </td>
              )}
            </tr>
          ))}
          {referrals.length === 0 && (
            <tr>
              <td colSpan={isStaff ? 7 : 6}>No referrals yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
