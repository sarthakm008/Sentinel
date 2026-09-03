// Dashboard Overview page

import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { casesApi, demoApi, evaluationApi } from '../api';
import { CaseResponse, EvaluationResponse } from '../types';
import { CaseCard } from '../components/CaseCard';
import { MerchantIntegration } from '../components/MerchantIntegration';

export function Overview() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total: 0,
    high_risk: 0,
    review_queue: 0,
    allowed: 0,
    estimated_exposure: 0,
  });
  const [recentCases, setRecentCases] = useState<CaseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [evalData, setEvalData] = useState<EvaluationResponse | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [casesRes, evalRes] = await Promise.all([
        casesApi.list({ size: 10 }),
        evaluationApi.get(),
      ]);
      setRecentCases(casesRes.cases);

      const highRisk = casesRes.cases.filter(c => c.risk_band === 'HIGH' || c.risk_band === 'CRITICAL').length;
      const reviewQueue = casesRes.cases.filter(c => c.status === 'pending' && (c.recommended_action === 'review' || c.recommended_action === 'hold')).length;
      const allowed = casesRes.cases.filter(c => c.recommended_action === 'approve').length;
      const exposure = casesRes.cases
        .filter(c => c.risk_band === 'HIGH' || c.risk_band === 'CRITICAL')
        .reduce((sum, c) => sum + c.risk_score * 10000, 0); // Rough estimate

      setStats({
        total: casesRes.total,
        high_risk: highRisk,
        review_queue: reviewQueue,
        allowed: allowed,
        estimated_exposure: exposure,
      });
      setEvalData(evalRes);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunDemo = async () => {
    try {
      await demoApi.run();
      await loadDashboard();
    } catch (err) {
      console.error('Demo failed:', err);
    }
  };

  const handleResetDemo = async () => {
    try {
      await demoApi.reset();
      await loadDashboard();
    } catch (err) {
      console.error('Reset failed:', err);
    }
  };

  const formatCurrency = (n: number) => `₹${n.toLocaleString(undefined, { minimumFractionDigits: 0 })}`;

  const formatLossVsBaseline = (lossAvoided: number) => {
    if (lossAvoided >= 0) {
      return `Loss Avoided: ${formatCurrency(lossAvoided)}`;
    } else {
      return `Additional Loss vs Baseline: ${formatCurrency(Math.abs(lossAvoided))}`;
    }
  };

  const handleCaseCreated = (caseId: number) => {
    loadDashboard();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  const sentinel = evalData?.production_candidate;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Sentinel Dashboard</h1>
          <p className="text-text-secondary">AI-Powered Coordinated Refund Abuse Detection</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRunDemo}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary-hover transition font-medium"
          >
            Run Demo Scenario
          </button>
          <button
            onClick={handleResetDemo}
            className="px-4 py-2 bg-bg-tertiary text-text-primary hover:bg-bg-hover transition font-medium"
          >
            Reset Demo
          </button>
        </div>
      </div>

      {/* Merchant Integration / Live Refund Monitoring */}
      <MerchantIntegration onCaseCreated={handleCaseCreated} />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="card p-6">
          <p className="text-sm text-text-secondary">Total Analyzed</p>
          <p className="text-3xl font-bold text-text-primary mt-1">{stats.total}</p>
        </div>
        <div className="card p-6">
          <p className="text-sm text-text-secondary">High Risk Cases</p>
          <p className="text-3xl font-bold text-danger mt-1">{stats.high_risk}</p>
        </div>
        <div className="card p-6">
          <p className="text-sm text-text-secondary">Review Queue</p>
          <p className="text-3xl font-bold text-warning mt-1">{stats.review_queue}</p>
        </div>
        <div className="card p-6">
          <p className="text-sm text-text-secondary">Auto-Approved</p>
          <p className="text-3xl font-bold text-success mt-1">{stats.allowed}</p>
        </div>
        <div className="card p-6">
          <p className="text-sm text-text-secondary">Est. Exposure</p>
          <p className="text-3xl font-bold text-text-primary mt-1">{formatCurrency(stats.estimated_exposure)}</p>
        </div>
      </div>

      {/* Production Model Summary */}
      {sentinel && (
        <div className="card p-4 border-success border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-success">Production Candidate: Full Sentinel (39 features)</p>
              <p className="text-sm text-success mt-1">
                PR-AUC: {sentinel.pr_auc.toFixed(4)} | Recall: {sentinel.recall.toFixed(4)} | Precision: {sentinel.precision.toFixed(4)} | {formatLossVsBaseline(sentinel.loss_avoided_vs_baseline)}
              </p>
            </div>
            <Link
              to="/evaluation"
              className="px-4 py-2 bg-success text-success-foreground rounded-lg hover:bg-success transition font-medium"
            >
              View Full Evaluation
            </Link>
          </div>
        </div>
      )}

      {/* Recent Cases */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-lg font-semibold text-text-primary">Recent Risk Cases</h2>
          <Link to="/cases" className="text-sm text-primary hover:text-primary-hover">View All</Link>
        </div>
        <div className="divide-y divide-border">
          {recentCases.length === 0 ? (
            <div className="p-8 text-center text-text-muted">
              No cases yet. Use the "Send Test Refund" tool above or run the demo scenario.
            </div>
          ) : (
            recentCases.map((caseData) => (
              <CaseCard key={caseData.id} case={caseData} onClick={() => navigate(`/cases/${caseData.id}`)} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function formatCurrency(n: number): string {
  return `₹${n.toLocaleString(undefined, { minimumFractionDigits: 0 })}`;
}

function formatLossVsBaseline(lossAvoided: number): string {
  if (lossAvoided >= 0) {
    return `Loss Avoided: ${formatCurrency(lossAvoided)}`;
  } else {
    return `Additional Loss vs Baseline: ${formatCurrency(Math.abs(lossAvoided))}`;
  }
}