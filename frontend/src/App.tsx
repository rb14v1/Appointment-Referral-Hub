import { RouterProvider } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import { router } from "./router/routes";

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}
