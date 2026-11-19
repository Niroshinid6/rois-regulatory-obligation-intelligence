import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppShell } from './components/layout/AppShell';

import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Documents } from './pages/Documents';
import { UploadDocument } from './pages/UploadDocument';
import { ObligationExplorer } from './pages/ObligationExplorer';
import { EvidenceViewer } from './pages/EvidenceViewer';
import { VersionComparison } from './pages/VersionComparison';
import { ControlMapping } from './pages/ControlMapping';
import { ReviewQueue } from './pages/ReviewQueue';
import { ImpactReports } from './pages/ImpactReports';
import { AuditLogs } from './pages/AuditLogs';
import { UserManagement } from './pages/UserManagement';
import { Settings } from './pages/Settings';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 text-xs">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500 mb-2"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <AppShell>{children}</AppShell>;
};

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Protected Application Routes */}
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/documents" element={<ProtectedRoute><Documents /></ProtectedRoute>} />
          <Route path="/upload" element={<ProtectedRoute><UploadDocument /></ProtectedRoute>} />
          <Route path="/obligations" element={<ProtectedRoute><ObligationExplorer /></ProtectedRoute>} />
          <Route path="/evidence" element={<ProtectedRoute><EvidenceViewer /></ProtectedRoute>} />
          <Route path="/evidence/:id" element={<ProtectedRoute><EvidenceViewer /></ProtectedRoute>} />
          <Route path="/compare" element={<ProtectedRoute><VersionComparison /></ProtectedRoute>} />
          <Route path="/controls" element={<ProtectedRoute><ControlMapping /></ProtectedRoute>} />
          <Route path="/review-queue" element={<ProtectedRoute><ReviewQueue /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><ImpactReports /></ProtectedRoute>} />
          <Route path="/audit" element={<ProtectedRoute><AuditLogs /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute><UserManagement /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
