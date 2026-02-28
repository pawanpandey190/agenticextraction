import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { UploadPage } from './pages/UploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { ReportPage } from './pages/ReportPage';
import { BatchUploadPage } from './pages/BatchUploadPage';
import { BatchResultsPage } from './pages/BatchResultsPage';
import { HistoryPage } from './pages/HistoryPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ProtectedRoute from './components/ProtectedRoute';
import { useAuth } from './hooks/useAuth';
import { LogOut } from 'lucide-react';

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 selection:bg-brand-primary/10 mesh-gradient relative overflow-x-hidden">
      {/* Dynamic Background Elements - Simplified for Light Theme */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-5%] left-[-5%] w-[30%] h-[30%] bg-brand-primary/5 blur-[100px] rounded-full"></div>
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 border-b border-slate-200 backdrop-blur-md shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center space-x-4 group transition-all">
              <div className="h-12 w-auto min-w-[120px] transition-all duration-500 ease-out group-hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.8)] filter">
                <img src="/logo.png" alt="Logo" className="h-full w-auto object-contain group-hover:scale-105 transition-transform duration-500" />
              </div>
              <div className="flex flex-col">
                <h1 className="text-xl font-extrabold tracking-tight text-slate-900 group-hover:text-brand-primary transition-colors">
                  Document Analysis
                </h1>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] -mt-1">
                  Professional Suite
                </span>
              </div>
            </Link>

            <nav className="flex items-center space-x-8">
              <Link to="/" className="text-sm font-medium text-slate-600 hover:text-brand-primary transition-colors relative group">
                New Analysis
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-brand-primary transition-all group-hover:w-full"></span>
              </Link>
              <Link to="/batch-upload" className="text-sm font-medium text-slate-600 hover:text-brand-primary transition-colors relative group">
                Batch Upload
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-brand-primary transition-all group-hover:w-full"></span>
              </Link>
              <Link to="/history" className="text-sm font-medium text-slate-600 hover:text-brand-primary transition-colors relative group">
                History
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-brand-primary transition-all group-hover:w-full"></span>
              </Link>
              <AuthNav />
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-8 min-h-[calc(100vh-160px)]">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-8 mt-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-slate-500 font-medium">
              Professional Document Analysis System
            </p>
            <div className="flex gap-6 text-slate-400 text-xs uppercase tracking-widest font-bold">
              <span>Secure</span>
              <span>•</span>
              <span>Accurate</span>
              <span>•</span>
              <span>Verified</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

function AuthNav() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  if (!isAuthenticated) return null;

  return (
    <button
      onClick={() => { logout(); navigate('/login'); }}
      className="flex items-center gap-2 text-sm font-bold text-red-500 hover:text-red-600 transition-colors px-3 py-1.5 rounded-full hover:bg-red-50"
    >
      <LogOut size={16} />
      <span>Sign Out</span>
    </button>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Auth routes without layout */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Protected routes with layout */}
        <Route path="/*" element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<UploadPage />} />
                <Route path="/batch-upload" element={<BatchUploadPage />} />
                <Route path="/batch/:batchId" element={<BatchResultsPage />} />
                <Route path="/processing/:sessionId" element={<ProcessingPage />} />
                <Route path="/report/:sessionId" element={<ReportPage />} />
                <Route path="/history" element={<HistoryPage />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}
