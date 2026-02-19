import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { UploadPage } from './pages/UploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { ReportPage } from './pages/ReportPage';
import { BatchUploadPage } from './pages/BatchUploadPage';
import { BatchResultsPage } from './pages/BatchResultsPage';
import { HistoryPage } from './pages/HistoryPage';
import { Link } from 'react-router-dom';

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
            <Link to="/" className="flex items-center space-x-3 group transition-all">
              <div className="w-10 h-10 rounded-xl overflow-hidden shadow-sm group-hover:scale-105 transition-transform">
                <img src="/logo.png" alt="Logo" className="w-full h-full object-contain" />
              </div>
              <h1 className="text-xl font-bold text-slate-900">
                Document Analysis
              </h1>
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

export function App() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  );
}
