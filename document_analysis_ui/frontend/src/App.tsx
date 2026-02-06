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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h1 className="text-xl font-semibold text-gray-900">Document Analysis</h1>
            </Link>

            <nav className="flex items-center space-x-6">
              <Link to="/" className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors">
                New Analysis
              </Link>
              <Link to="/batch-upload" className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors">
                Batch Upload
              </Link>
              <Link to="/history" className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors flex items-center gap-1">
                History
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            AI-Powered Document Analysis System
          </p>
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
