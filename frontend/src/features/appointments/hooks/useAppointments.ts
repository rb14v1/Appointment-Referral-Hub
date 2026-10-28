import { useCallback, useEffect, useState } from "react";

import { listAppointments } from "../../../api/endpoints/appointments";
import type { Appointment } from "../../../types";

export function useAppointments(params?: Record<string, string | number | undefined>) {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    return listAppointments(params)
      .then((res) => setAppointments(res.data.results))
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(params)]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { appointments, loading, error, reload };
}
