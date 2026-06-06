import { Navigate, Route, Routes } from "react-router-dom";
import { AppLoadingPage } from "@/features/system/AppLoadingPage";
import { LoginPage } from "@/features/login/LoginPage";
import { SessionExpiredPage } from "@/features/system/SessionExpiredPage";
import { ConnectionErrorPage } from "@/features/system/ConnectionErrorPage";
import { AuthenticatedLayout } from "@/features/system/AuthenticatedLayout";
import { RequireAuth } from "@/features/system/RequireAuth";
import { MyDayPage } from "@/features/my-day/MyDayPage";
import { FirmSearchPage } from "@/features/firms/FirmSearchPage";
import { FirmDetailPage } from "@/features/firms/FirmDetailPage";
import { ContactDetailPage } from "@/features/contacts/ContactDetailPage";
import { ActivityDetailPage } from "@/features/activities/ActivityDetailPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/app/loading" replace />} />
      <Route path="/app/loading" element={<AppLoadingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/app/session-expired" element={<SessionExpiredPage />} />
      <Route path="/app/connection-error" element={<ConnectionErrorPage />} />

      <Route
        path="/app"
        element={
          <RequireAuth>
            <AuthenticatedLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/app/my-day" replace />} />
        <Route path="my-day" element={<MyDayPage />} />
        <Route path="firms" element={<FirmSearchPage />} />
        <Route path="firms/:firmId" element={<FirmDetailPage />} />
        <Route path="contacts/:contactId" element={<ContactDetailPage />} />
        <Route path="activities/:activityId" element={<ActivityDetailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/app/loading" replace />} />
    </Routes>
  );
}
