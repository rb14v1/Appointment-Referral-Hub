import { useEffect, useState } from "react";

import { extractErrorMessage } from "../../../api/client";
import { createAvailability, deleteAvailability, listAvailability } from "../../../api/endpoints/providers";
import { listProviders } from "../../../api/endpoints/providers";
import { useAuth } from "../../../auth/AuthContext";
import type { Provider, ProviderAvailability } from "../../../types";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export function AvailabilityPage() {
  const { user } = useAuth();
  const [myProvider, setMyProvider] = useState<Provider | null>(null);
  const [rules, setRules] = useState<ProviderAvailability[]>([]);
  const [dayOfWeek, setDayOfWeek] = useState(0);
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("12:00");
  const [slotDuration, setSlotDuration] = useState(30);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProviders().then((res) => {
      const mine = res.data.results.find((p) => p.user_detail?.id === user?.id) ?? null;
      setMyProvider(mine);
    });
  }, [user]);

  function reload(providerId: number) {
    listAvailability({ provider: providerId }).then((res) => setRules(res.data.results));
  }

  useEffect(() => {
    if (myProvider) reload(myProvider.id);
  }, [myProvider]);

  async function handleAdd() {
    if (!myProvider) return;
    setError(null);
    try {
      await createAvailability({
        provider: myProvider.id,
        clinic: myProvider.home_clinic,
        recurrence_rule: "weekly",
        day_of_week: dayOfWeek,
        start_time: `${startTime}:00`,
        end_time: `${endTime}:00`,
        slot_duration_minutes: slotDuration,
      });
      reload(myProvider.id);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleDelete(id: number) {
    if (!myProvider) return;
    await deleteAvailability(id);
    reload(myProvider.id);
  }

  if (!myProvider) return <p>Loading your provider profile...</p>;

  return (
    <div>
      <h1>My Availability</h1>

      <div className="form-grid">
        <label>
          Day of week
          <select value={dayOfWeek} onChange={(e) => setDayOfWeek(Number(e.target.value))}>
            {DAYS.map((day, idx) => (
              <option key={day} value={idx}>
                {day}
              </option>
            ))}
          </select>
        </label>
        <label>
          Start time
          <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
        </label>
        <label>
          End time
          <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
        </label>
        <label>
          Slot length (minutes)
          <input type="number" min={5} value={slotDuration} onChange={(e) => setSlotDuration(Number(e.target.value))} />
        </label>
      </div>
      <button onClick={handleAdd}>Add weekly availability</button>
      {error && <p className="error-text">{error}</p>}

      <h2>Current rules</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>When</th>
            <th>Time</th>
            <th>Slot length</th>
            <th>Blocked</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rules.map((rule) => (
            <tr key={rule.id}>
              <td>{rule.recurrence_rule}</td>
              <td>{rule.recurrence_rule === "weekly" ? DAYS[rule.day_of_week ?? 0] : rule.specific_date}</td>
              <td>
                {rule.start_time}-{rule.end_time}
              </td>
              <td>{rule.slot_duration_minutes}m</td>
              <td>{rule.is_blocked ? "Yes" : "No"}</td>
              <td>
                <button onClick={() => handleDelete(rule.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
