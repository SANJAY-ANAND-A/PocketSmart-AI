import React from 'react';
import { ShieldCheck, AlertTriangle, TrendingDown, DollarSign, PieChart } from 'lucide-react';
import type { BudgetSummary } from '../types/planner';
import { formatINR, formatPercentage } from '../utils/formatters';

interface BudgetSummaryCardProps {
  budget: BudgetSummary;
  source?: 'gemini' | 'deterministic_fallback';
  title?: string;
}

export const BudgetSummaryCard: React.FC<BudgetSummaryCardProps> = ({
  budget,
  source,
  title = 'Authoritative Budget Allocation',
}) => {
  const isOver = !budget.is_within_budget;
  const isFallback = source === 'deterministic_fallback';

  // Determine progress bar color based on utilization
  let progressColor = 'var(--success-text)';
  if (budget.utilization_percentage > 90) {
    progressColor = 'var(--warning-text)';
  }
  if (isOver) {
    progressColor = 'var(--danger-text)';
  }

  return (
    <div className={`budget-summary-card ${isOver ? 'over-budget' : ''}`}>
      <div className="budget-summary-header">
        <div className="budget-summary-title-row">
          <div className="budget-badge-icon">
            <ShieldCheck size={20} />
          </div>
          <div>
            <h3 className="budget-summary-title">{title}</h3>
            <span className="budget-engine-tag">Deterministic Engine Verified</span>
          </div>
        </div>

        <div className="budget-status-badges">
          {isFallback && (
            <span className="badge-fallback" title="Rule-based allocation was used">
              <AlertTriangle size={13} /> Fallback Engine
            </span>
          )}
          <span className={`badge-budget-status ${isOver ? 'danger' : 'success'}`}>
            {isOver ? `Over by ${formatINR(budget.over_budget_amount)}` : 'Within Budget'}
          </span>
        </div>
      </div>

      {/* Grid of Key Metrics */}
      <div className="budget-metrics-grid">
        <div className="metric-box">
          <span className="metric-label">
            <DollarSign size={14} /> Total Budget Limit
          </span>
          <span className="metric-value highlight">{formatINR(budget.total_budget)}</span>
        </div>

        <div className="metric-box">
          <span className="metric-label">
            <PieChart size={14} /> Allocated / Total Cost
          </span>
          <span className="metric-value">{formatINR(budget.total_cost)}</span>
        </div>

        <div className="metric-box">
          <span className="metric-label">
            <TrendingDown size={14} /> Remaining Savings
          </span>
          <span className={`metric-value ${budget.remaining_budget < 0 ? 'negative' : 'positive'}`}>
            {formatINR(budget.remaining_budget)}
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-label">Utilization Rate</span>
          <span className="metric-value">{formatPercentage(budget.utilization_percentage)}</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="budget-progress-section">
        <div className="progress-labels">
          <span>0%</span>
          <span>{formatPercentage(budget.utilization_percentage)} Allocated</span>
          <span>100%</span>
        </div>
        <div className="budget-progress-track">
          <div
            className="budget-progress-fill"
            style={{
              width: `${Math.min(budget.utilization_percentage, 100)}%`,
              backgroundColor: progressColor,
            }}
          />
        </div>
      </div>
    </div>
  );
};
