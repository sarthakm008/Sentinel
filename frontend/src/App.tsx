// Main App component with routing

import { BrowserRouter, Routes, Route, Link, Outlet } from 'react-router-dom';
import { Overview } from './pages/Overview';
import { Cases } from './pages/Cases';
import { CaseDetail } from './pages/CaseDetail';
import { Evaluation } from './pages/Evaluation';

function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="text-xl font-bold text-gray-900">Sentinel</Link>
              <nav className="hidden md:flex items-center gap-6">
                <Link to="/" className="text-sm font-medium text-gray-700 hover:text-blue-600">Dashboard</Link>
                <Link to="/cases" className="text-sm font-medium text-gray-700 hover:text-blue-600">Cases</Link>
                <Link to="/evaluation" className="text-sm font-medium text-gray-700 hover:text-blue-600">Evaluation</Link>
              </nav>
            </div>
            <div className="text-sm text-gray-500">
              AI Risk Manager for Coordinated Refund Abuse
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          Sentinel — Razorpay AI Buildathon 2026 • Track 02: AI Risk Manager
          <br />
          All data synthetic. Results do not represent production performance.
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/cases/:id" element={<CaseDetail />} />
          <Route path="/evaluation" element={<Evaluation />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}