import { useEffect, useState } from "react";

import { listClinics } from "../../../api/endpoints/clinics";
import { extractErrorMessage } from "../../../api/client";
import type { Clinic } from "../../../types";

export function ClinicsPage() {
  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listClinics()
      .then((res) => setClinics(res.data.results))
      .catch((err) => setError(extractErrorMessage(err)));
  }, []);

  return (
    <div>
      <h1>Clinics</h1>
      {error && <p className="error-text">{error}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Timezone</th>
            <th>Address</th>
            <th>Phone</th>
            <th>Active</th>
            <th>Requires front-desk approval</th>
          </tr>
        </thead>
        <tbody>
          {clinics.map((clinic) => (
            <tr key={clinic.id}>
              <td>{clinic.name}</td>
              <td>{clinic.timezone}</td>
              <td>{clinic.address}</td>
              <td>{clinic.phone}</td>
              <td>{clinic.is_active ? "Yes" : "No"}</td>
              <td>{clinic.requires_front_desk_approval ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
