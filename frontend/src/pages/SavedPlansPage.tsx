import React, { useEffect, useState } from 'react';
import {
  BookmarkCheck,
  Calendar,
  Layers,
  Sparkles,
  Trash2,
  ExternalLink,
  Plus,
  Home,
  PartyPopper,
  Gem,
  AlertCircle,
} from 'lucide-react';
import { plansService } from '../services/plansService';
import type { SavedPlanDetailResponse, SavedPlanListItem } from '../types/plans';
import { PlanDetailModal } from '../components/PlanDetailModal';
import { Toast } from '../components/Toast';
import { formatINR, formatDate } from '../utils/formatters';

interface SavedPlansPageProps {
  onNavigateToPlanner: (module: 'home' | 'party' | 'jewelry') => void;
}

export const SavedPlansPage: React.FC<SavedPlansPageProps> = ({ onNavigateToPlanner }) => {
  const [plans, setPlans] = useState<SavedPlanListItem[]>([]);
  const [activeFilter, setActiveFilter] = useState<'all' | 'home' | 'party' | 'jewelry'>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Detail Modal state
  const [selectedPlanDetail, setSelectedPlanDetail] = useState<SavedPlanDetailResponse | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  useEffect(() => {
    let isCancelled = false;

    async function loadPlans() {
      setIsLoading(true);
      setErrorMsg(null);
      try {
        const moduleParam = activeFilter === 'all' ? undefined : activeFilter;
        const res = await plansService.getPlans(moduleParam);
        if (!isCancelled) {
          setPlans(res.items);
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          const msg = err instanceof Error ? err.message : 'Failed to fetch saved plans.';
          setErrorMsg(msg);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    loadPlans();

    return () => {
      isCancelled = true;
    };
  }, [activeFilter]);

  const handleOpenDetail = async (planId: number) => {
    setIsLoadingDetail(true);
    try {
      const detail = await plansService.getPlanDetail(planId);
      setSelectedPlanDetail(detail);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load plan details.';
      setErrorMsg(msg);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleDeletePlan = async (planId: number) => {
    setIsDeleting(true);
    try {
      await plansService.deletePlan(planId);
      setPlans((prev) => prev.filter((p) => p.id !== planId));
      setToastMsg('Budget plan deleted successfully.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete plan.';
      setErrorMsg(msg);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="saved-plans-container">
      {/* Page Header */}
      <div className="view-header">
        <span className="view-badge plans">
          <BookmarkCheck size={13} /> Saved Plans & History
        </span>
        <h1 className="view-title">Your Budget Portfolios</h1>
        <p className="view-subtitle">
          Manage saved plans generated across Home Interior, Event/Party Planning, and Jewelry.
        </p>
      </div>

      {toastMsg && (
        <Toast type="success" message={toastMsg} onClose={() => setToastMsg(null)} />
      )}
      {errorMsg && (
        <Toast type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />
      )}

      {/* Filter Tabs Ribbon */}
      <div className="plans-filter-ribbon">
        <div className="filter-pill-group">
          <button
            type="button"
            className={`filter-pill ${activeFilter === 'all' ? 'active' : ''}`}
            onClick={() => setActiveFilter('all')}
          >
            All Plans ({plans.length})
          </button>
          <button
            type="button"
            className={`filter-pill ${activeFilter === 'home' ? 'active' : ''}`}
            onClick={() => setActiveFilter('home')}
          >
            <Home size={14} /> Home Interior
          </button>
          <button
            type="button"
            className={`filter-pill ${activeFilter === 'party' ? 'active' : ''}`}
            onClick={() => setActiveFilter('party')}
          >
            <PartyPopper size={14} /> Party & Event
          </button>
          <button
            type="button"
            className={`filter-pill ${activeFilter === 'jewelry' ? 'active' : ''}`}
            onClick={() => setActiveFilter('jewelry')}
          >
            <Gem size={14} /> Jewelry
          </button>
        </div>

        <div className="quick-plan-actions">
          <button
            type="button"
            className="btn-create-shortcut"
            onClick={() => onNavigateToPlanner('home')}
          >
            <Plus size={15} />
            <span>New Home Plan</span>
          </button>
          <button
            type="button"
            className="btn-create-shortcut"
            onClick={() => onNavigateToPlanner('party')}
          >
            <Plus size={15} />
            <span>New Party Plan</span>
          </button>
          <button
            type="button"
            className="btn-create-shortcut"
            onClick={() => onNavigateToPlanner('jewelry')}
          >
            <Plus size={15} />
            <span>New Jewelry Plan</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <div className="plans-loading-state">
          <span className="btn-spinner">Loading your saved plans...</span>
        </div>
      ) : plans.length === 0 ? (
        /* Empty State */
        <div className="empty-plans-card">
          <div className="empty-icon-circle">
            <BookmarkCheck size={36} />
          </div>
          <h3 className="empty-title">No Saved Plans Found</h3>
          <p className="empty-desc">
            {activeFilter === 'all'
              ? 'You have not generated or saved any budget plans yet. Start planning below!'
              : `You do not have any saved ${activeFilter} plans.`}
          </p>
          <div className="empty-action-buttons">
            <button
              type="button"
              className="btn-primary"
              onClick={() => onNavigateToPlanner(activeFilter === 'all' ? 'home' : activeFilter)}
            >
              <Sparkles size={16} />
              <span>
                Start {activeFilter === 'all' ? 'Home' : activeFilter.toUpperCase()} Planner
              </span>
            </button>
          </div>
        </div>
      ) : (
        /* Plans Grid */
        <div className="saved-plans-grid">
          {plans.map((p) => {
            const isOver = p.remaining_budget < 0;

            return (
              <div key={p.id} className="saved-plan-card">
                <div className="plan-card-header">
                  <span className={`view-badge ${p.module_type}`}>
                    {p.module_type.toUpperCase()}
                  </span>
                  <span className="plan-card-date">
                    <Calendar size={13} /> {formatDate(p.created_at)}
                  </span>
                </div>

                <h3 className="plan-card-title" title={p.title}>
                  {p.title}
                </h3>

                <div className="plan-financial-summary">
                  <div className="fin-row">
                    <span className="fin-label">Requested Budget:</span>
                    <span className="fin-val highlight">{formatINR(p.total_budget)}</span>
                  </div>
                  <div className="fin-row">
                    <span className="fin-label">Allocated Spend:</span>
                    <span className="fin-val">{formatINR(p.allocated_budget)}</span>
                  </div>
                  <div className="fin-row">
                    <span className="fin-label">Remaining:</span>
                    <span className={`fin-val ${isOver ? 'negative' : 'positive'}`}>
                      {formatINR(p.remaining_budget)}
                    </span>
                  </div>
                </div>

                <div className="plan-card-meta-chips">
                  <span className="meta-chip">
                    <Layers size={13} /> {p.items_count} Allocations
                  </span>
                  <span className="meta-chip">
                    <Sparkles size={13} /> {p.recommendations_count} Products
                  </span>
                  {p.is_fallback && (
                    <span className="meta-chip warning" title="Generated using rule-based fallback">
                      <AlertCircle size={13} /> Fallback
                    </span>
                  )}
                </div>

                <div className="plan-card-actions">
                  <button
                    type="button"
                    className="btn-plan-detail"
                    onClick={() => handleOpenDetail(p.id)}
                    disabled={isLoadingDetail}
                  >
                    <span>View Breakdown</span>
                    <ExternalLink size={14} />
                  </button>

                  <button
                    type="button"
                    className="btn-plan-delete-icon"
                    onClick={() => {
                      if (window.confirm(`Delete plan "${p.title}"?`)) {
                        handleDeletePlan(p.id);
                      }
                    }}
                    title="Delete plan"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Plan Detail Modal */}
      {selectedPlanDetail && (
        <PlanDetailModal
          plan={selectedPlanDetail}
          onClose={() => setSelectedPlanDetail(null)}
          onDelete={handleDeletePlan}
          isDeleting={isDeleting}
        />
      )}
    </div>
  );
};
