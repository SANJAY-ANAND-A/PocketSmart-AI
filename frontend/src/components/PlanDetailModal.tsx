import React from 'react';
import { X, Calendar, Trash2, Sparkles, Layers, DollarSign } from 'lucide-react';
import type { SavedPlanDetailResponse } from '../types/plans';
import { ProductCard } from './ProductCard';
import { formatINR, formatDate } from '../utils/formatters';

interface PlanDetailModalProps {
  plan: SavedPlanDetailResponse;
  onClose: () => void;
  onDelete?: (planId: number) => Promise<void>;
  isDeleting?: boolean;
}

export const PlanDetailModal: React.FC<PlanDetailModalProps> = ({
  plan,
  onClose,
  onDelete,
  isDeleting = false,
}) => {
  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to permanently delete "${plan.title}"?`)) {
      if (onDelete) {
        await onDelete(plan.id);
        onClose();
      }
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-stack">
            <div className="modal-badge-row">
              <span className={`view-badge ${plan.module_type}`}>
                {plan.module_type.toUpperCase()}
              </span>
              <span className="modal-date">
                <Calendar size={13} /> {formatDate(plan.created_at)}
              </span>
            </div>
            <h2 className="modal-title">{plan.title}</h2>
          </div>

          <button
            type="button"
            className="btn-modal-close"
            onClick={onClose}
            aria-label="Close dialog"
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Financial Summary Strip */}
          <div className="modal-financial-strip">
            <div className="strip-item">
              <span className="strip-label">Requested Budget</span>
              <span className="strip-value highlight">{formatINR(plan.total_budget)}</span>
            </div>
            <div className="strip-item">
              <span className="strip-label">Allocated Spend</span>
              <span className="strip-value">{formatINR(plan.allocated_budget)}</span>
            </div>
            <div className="strip-item">
              <span className="strip-label">Remaining Balance</span>
              <span className={`strip-value ${plan.remaining_budget < 0 ? 'negative' : 'positive'}`}>
                {formatINR(plan.remaining_budget)}
              </span>
            </div>
          </div>

          {/* AI Reasoning Section */}
          {plan.ai_reasoning && (
            <div className="modal-ai-notes">
              <div className="ai-notes-header">
                <Sparkles size={16} className="sparkle-icon" />
                <span>AI Strategy & Planning Rationale</span>
              </div>
              <p className="ai-notes-content">{plan.ai_reasoning}</p>
            </div>
          )}

          {/* Line Items / Category Allocations */}
          {plan.items && plan.items.length > 0 && (
            <div className="modal-section">
              <h3 className="section-title">
                <Layers size={16} /> Category Budget Allocations ({plan.items.length})
              </h3>
              <div className="items-table-container">
                <table className="items-table">
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th>Allocated</th>
                      <th>Spent</th>
                      <th>Priority</th>
                      <th>Allocation Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plan.items.map((item) => (
                      <tr key={item.id}>
                        <td className="item-name-cell">{item.category_name}</td>
                        <td className="item-amount-cell">{formatINR(item.allocated_amount)}</td>
                        <td className="item-spent-cell">{formatINR(item.spent_amount)}</td>
                        <td>
                          <span className={`priority-tag ${item.priority}`}>
                            {item.priority}
                          </span>
                        </td>
                        <td className="item-reason-cell">{item.reason || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Product Recommendations */}
          <div className="modal-section">
            <h3 className="section-title">
              <DollarSign size={16} /> Curated Product Recommendations ({plan.recommendations.length})
            </h3>
            {plan.recommendations && plan.recommendations.length > 0 ? (
              <div className="modal-products-grid">
                {plan.recommendations.map((rec) => {
                  if (!rec.product) return null;
                  return (
                    <ProductCard
                      key={rec.id}
                      product={rec.product}
                      matchScore={rec.match_score}
                      reason={rec.recommendation_reason || undefined}
                    />
                  );
                })}
              </div>
            ) : (
              <p className="empty-subtext">No catalog products attached to this plan.</p>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          {onDelete && (
            <button
              type="button"
              className="btn-delete-plan"
              onClick={handleDelete}
              disabled={isDeleting}
            >
              <Trash2 size={16} />
              <span>{isDeleting ? 'Deleting...' : 'Delete Plan'}</span>
            </button>
          )}
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
