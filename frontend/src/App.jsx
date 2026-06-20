import { Navigate, Route, Routes } from "react-router-dom";
import { AdminAuthProvider, useAdminAuth } from "./auth/AdminAuth.jsx";
import { PublicHome } from "./pages/public/PublicHome.jsx";
import { PublicCall } from "./pages/public/PublicCall.jsx";
import { AdminLogin } from "./pages/admin/AdminLogin.jsx";
import { AdminLayout } from "./pages/admin/AdminLayout.jsx";
import { Dashboard } from "./pages/admin/Dashboard.jsx";
import { ReplicasPage } from "./pages/admin/ReplicasPage.jsx";
import { PersonasPage } from "./pages/admin/PersonasPage.jsx";
import { PropertiesPage } from "./pages/admin/PropertiesPage.jsx";
import { ToolCallsPage } from "./pages/admin/ToolCallsPage.jsx";
import { CallSettingsPage } from "./pages/admin/CallSettingsPage.jsx";
import { DocumentsPage } from "./pages/admin/DocumentsPage.jsx";
import { DemoUsersPage } from "./pages/admin/DemoUsersPage.jsx";
import { ConversationsPage } from "./pages/admin/ConversationsPage.jsx";
import { MeetingsPage } from "./pages/admin/MeetingsPage.jsx";
import { AuditLogPage } from "./pages/admin/AuditLogPage.jsx";
import { ChangePasswordPage } from "./pages/admin/ChangePasswordPage.jsx";

function RequireAdmin({ children }) {
  const { user, loading } = useAdminAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading&hellip;
      </div>
    );
  }
  if (!user) return <Navigate to="/admin/login" replace />;
  return children;
}

export default function App() {
  return (
    <AdminAuthProvider>
      <Routes>
        <Route path="/" element={<PublicHome />} />
        <Route path="/call" element={<PublicCall />} />
        <Route path="/call/join/:inviteId" element={<PublicCall />} />

        <Route path="/admin/login" element={<AdminLogin />} />
        <Route
          path="/admin"
          element={
            <RequireAdmin>
              <AdminLayout />
            </RequireAdmin>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="replicas" element={<ReplicasPage />} />
          <Route path="personas" element={<PersonasPage />} />
          <Route path="properties" element={<PropertiesPage />} />
          <Route path="tool-calls" element={<ToolCallsPage />} />
          <Route path="call-settings" element={<CallSettingsPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="demo-users" element={<DemoUsersPage />} />
          <Route path="conversations" element={<ConversationsPage />} />
          <Route path="meetings" element={<MeetingsPage />} />
          <Route path="audit" element={<AuditLogPage />} />
          <Route path="change-password" element={<ChangePasswordPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AdminAuthProvider>
  );
}
