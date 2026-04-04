// src/App.tsx
import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

// Layouts
import { MarketingLayout, AuthLayout, AppLayout } from '@/components/layout';

// Public pages
import {
  HomePage,
  FaqPage,
  ContactPage,
  TutorialsPage,
  TutorialDetailPage,
} from '@/pages/public';

// Auth pages
import { LoginPage, RegisterPage, ForgotPasswordPage } from '@/pages/auth';

// App pages
import {
  OverviewPage,
  UploadPage,
  DashboardsPage,
  DashboardDetailPage,
  ReportsPage,
  ProfilePage,
} from '@/pages/app';

import { TermsPage } from '@/pages/public/TermsPage';
import { PrivacyPage } from '@/pages/public/PrivacyPage';


// Guards
import { useLocation } from 'react-router-dom';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <>{children}</>;
}

function RedirectIfAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/app" replace />;
  return <>{children}</>;
}

// 404 (por ahora inline; luego lo movemos a /pages/public/NotFoundPage.tsx si quieres)
function NotFoundPage() {
  return (
    <MarketingLayout>
      <div className="container py-20 text-center">
        <h1 className="text-4xl font-bold mb-4">Page not found</h1>
        <p className="text-muted-foreground mb-8">
          The page you're looking for doesn't exist.
        </p>
        <a href="/" className="text-secondary hover:underline">
          Go home
        </a>
      </div>
    </MarketingLayout>
  );
}

export default function App() {
  return (
    <Routes>
      {/* Marketing (public) */}
      <Route
        path="/"
        element={
          <MarketingLayout>
            <HomePage />
          </MarketingLayout>
        }
      />
      <Route
        path="/faq"
        element={
          <MarketingLayout>
            <FaqPage />
          </MarketingLayout>
        }
      />
      <Route
        path="/contact"
        element={
          <MarketingLayout>
            <ContactPage />
          </MarketingLayout>
        }
      />
      <Route
        path="/tutorials"
        element={
          <MarketingLayout>
            <TutorialsPage />
          </MarketingLayout>
        }
      />
      <Route
        path="/tutorials/:slug"
        element={
          <MarketingLayout>
            <TutorialDetailPage />
          </MarketingLayout>
        }
      />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />

      {/* Auth (public pero redirige si ya hay sesión) */}
      <Route
        path="/login"
        element={
          <RedirectIfAuth>
            <AuthLayout>
              <LoginPage />
            </AuthLayout>
          </RedirectIfAuth>
        }
      />
      <Route
        path="/register"
        element={
          <RedirectIfAuth>
            <AuthLayout>
              <RegisterPage />
            </AuthLayout>
          </RedirectIfAuth>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <RedirectIfAuth>
            <AuthLayout>
              <ForgotPasswordPage />
            </AuthLayout>
          </RedirectIfAuth>
        }
      />

      {/* App (protegidas) */}
      <Route
        path="/app"
        element={
          <RequireAuth>
            <AppLayout>
              <OverviewPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/app/upload"
        element={
          <RequireAuth>
            <AppLayout>
              <UploadPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/app/dashboards"
        element={
          <RequireAuth>
            <AppLayout>
              <DashboardsPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/app/dashboards/:id"
        element={
          <RequireAuth>
            <AppLayout>
              <DashboardDetailPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/app/reports"
        element={
          <RequireAuth>
            <AppLayout>
              <ReportsPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/app/profile"
        element={
          <RequireAuth>
            <AppLayout>
              <ProfilePage />
            </AppLayout>
          </RequireAuth>
        }
      />

      {/* Si quieres mantener accesos "internos" a contenidos públicos dentro de /app */}
      <Route
        path="/app/tutorials"
        element={
          <RequireAuth>
            <AppLayout>
              <TutorialsPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/app/faq"
        element={
          <RequireAuth>
            <AppLayout>
              <FaqPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/app/contact"
        element={
          <RequireAuth>
            <AppLayout>
              <ContactPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      
      {/* 404 real */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
