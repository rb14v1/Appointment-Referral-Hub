import { useEffect, useState } from "react";

import { extractErrorMessage } from "../../../api/client";
import { listProviders } from "../../../api/endpoints/providers";
import { scheduleReferral } from "../../../api/endpoints/referrals";
import type { Provider, Referral } from "../../../types";

export function ScheduleReferralForm({ referral, onDone }: { referral: Referral; onDone: () => void }) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [providerId, setProviderId] = useState<number | "">("");
  const [startTime, setStartTime] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProviders({ home_clinic: referral.receiving_clinic }).then((res) => setProviders(res.data.results));
  }, [referral.receiving_clinic]);

  async function handleSubmit() {
    setError(null);
    if (!providerId || !startTime) {
      setError("Pick a provider and a start time.");
      return;
    }
    try {
      await scheduleReferral(referral.id, providerId as number, new Date(startTime).toISOString());
      onDone();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div className="inline-form">
      <select value={providerId} onChange={(e) => setProviderId(e.target.value ? Number(e.target.value) : "")}>
        <option value="">Provider</option>
        {providers.map((p) => (
          <option key={p.id} value={p.id}>
            {p.user_detail?.first_name} {p.user_detail?.last_name}
          </option>
        ))}
      </select>
      <input type="datetime-local" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
      <button onClick={handleSubmit}>Confirm</button>
      {error && <span className="error-text">{error}</span>}
    </div>
  );
}
