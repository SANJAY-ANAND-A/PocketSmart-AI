import React, { useState } from 'react';
import {
  Home,
  Sparkles,
  ArrowRight,
  RotateCcw,
  Layers,
  Palette,
  CheckCircle2,
  BookmarkCheck,
  AlertCircle,
} from 'lucide-react';
import { plannerService } from '../services/plannerService';
import type { HomePlanResponse } from '../types/planner';
import { BudgetSummaryCard } from '../components/BudgetSummaryCard';
import { ProductCard } from '../components/ProductCard';
import { Toast } from '../components/Toast';
import { formatINR } from '../utils/formatters';

interface HomePlannerPageProps {
  onNavigateToPlans?: () => void;
}

const ROOM_OPTIONS = [
  { id: 'bedroom', label: 'Bedroom' },
  { id: 'living_room', label: 'Living Room' },
  { id: 'dining_room', label: 'Dining Room' },
  { id: 'home_office', label: 'Home Office' },
  { id: 'kitchen', label: 'Kitchen' },
  { id: 'studio', label: 'Studio Apartment' },
  { id: 'balcony', label: 'Balcony' },
];

const STYLE_OPTIONS = [
  'Modern Minimalist',
  'Scandinavian',
  'Bohemian',
  'Industrial',
  'Traditional',
];

const POPULAR_COLORS = ['White', 'Neutral Beige', 'Warm Wood', 'Charcoal', 'Navy Blue', 'Forest Green'];
const POPULAR_PRIORITIES = ['Bed', 'Wardrobe', 'Sofa', 'Study Desk', 'Ergonomic Chair', 'Storage Unit', 'Ambient Lighting'];

export const HomePlannerPage: React.FC<HomePlannerPageProps> = ({ onNavigateToPlans }) => {
  const [budget, setBudget] = useState<number>(100000);
  const [roomType, setRoomType] = useState<string>('bedroom');
  const [style, setStyle] = useState<string>('Modern Minimalist');
  const [selectedColors, setSelectedColors] = useState<string[]>(['White', 'Warm Wood']);
  const [selectedPriorities, setSelectedPriorities] = useState<string[]>(['Bed', 'Wardrobe']);
  const [requiredItemsInput, setRequiredItemsInput] = useState<string>('Queen bed, study table');
  const [preferences, setPreferences] = useState<string>('');
  const [title, setTitle] = useState<string>('');

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [planResult, setPlanResult] = useState<HomePlanResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const toggleColor = (color: string) => {
    setSelectedColors((prev) =>
      prev.includes(color) ? prev.filter((c) => c !== color) : [...prev, color]
    );
  };

  const togglePriority = (priority: string) => {
    setSelectedPriorities((prev) =>
      prev.includes(priority) ? prev.filter((p) => p !== priority) : [...prev, priority]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (budget <= 0) {
      setErrorMsg('Please enter a positive budget amount.');
      return;
    }

    const requiredItems = requiredItemsInput
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length > 0);

    setIsLoading(true);
    try {
      const response = await plannerService.planHome({
        budget,
        room_type: roomType,
        style,
        color_preferences: selectedColors,
        priorities: selectedPriorities,
        required_items: requiredItems,
        preferences: preferences.trim() || undefined,
        title: title.trim() || undefined,
      });

      setPlanResult(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to generate home plan. Please try again.';
      setErrorMsg(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="planner-page-container">
      {/* Page Header */}
      <div className="view-header">
        <span className="view-badge home">
          <Home size={13} /> Home Interior Planner
        </span>
        <h1 className="view-title">Plan Your Dream Space Within Budget</h1>
        <p className="view-subtitle">
          AI-driven furniture allocation and aesthetic interior styling with authoritative budget ceiling guarantees.
        </p>
      </div>

      {errorMsg && <Toast type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}

      {!planResult ? (
        /* Planner Form */
        <form onSubmit={handleSubmit} className="planner-form-card">
          {/* Section: Budget Limit */}
          <div className="form-section">
            <label className="section-label">
              Total Budget Limit <span className="required">*</span>
            </label>
            <div className="budget-input-wrapper">
              <span className="currency-prefix">₹</span>
              <input
                type="number"
                min="1000"
                step="500"
                className="budget-main-input"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                required
              />
            </div>
            {/* Quick preset buttons */}
            <div className="quick-presets-row">
              <span className="quick-preset-label">Quick Presets:</span>
              {[25000, 50000, 100000, 200000, 500000].map((preset) => (
                <button
                  key={preset}
                  type="button"
                  className={`btn-preset ${budget === preset ? 'active' : ''}`}
                  onClick={() => setBudget(preset)}
                >
                  {formatINR(preset)}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Room Type */}
          <div className="form-section">
            <label className="section-label">
              Space / Room Type <span className="required">*</span>
            </label>
            <div className="pills-grid">
              {ROOM_OPTIONS.map((room) => (
                <button
                  key={room.id}
                  type="button"
                  className={`pill-option ${roomType === room.id ? 'active' : ''}`}
                  onClick={() => setRoomType(room.id)}
                >
                  {room.label}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Style Selection */}
          <div className="form-section">
            <label className="section-label">Design & Aesthetic Style</label>
            <div className="pills-grid">
              {STYLE_OPTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  className={`pill-option ${style === s ? 'active' : ''}`}
                  onClick={() => setStyle(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Color Palette */}
          <div className="form-section">
            <label className="section-label">
              <Palette size={15} /> Color Palette Preferences
            </label>
            <div className="badge-select-row">
              {POPULAR_COLORS.map((col) => (
                <button
                  key={col}
                  type="button"
                  className={`badge-toggle ${selectedColors.includes(col) ? 'selected' : ''}`}
                  onClick={() => toggleColor(col)}
                >
                  {col}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Priority Furniture */}
          <div className="form-section">
            <label className="section-label">
              <Layers size={15} /> High Priority Furniture Categories
            </label>
            <div className="badge-select-row">
              {POPULAR_PRIORITIES.map((p) => (
                <button
                  key={p}
                  type="button"
                  className={`badge-toggle ${selectedPriorities.includes(p) ? 'selected' : ''}`}
                  onClick={() => togglePriority(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Must-Have Items */}
          <div className="form-section">
            <label className="section-label" htmlFor="required-items">
              Must-Have Specific Items (comma separated)
            </label>
            <input
              id="required-items"
              type="text"
              className="form-input"
              placeholder="e.g. Queen storage bed, study desk with drawers"
              value={requiredItemsInput}
              onChange={(e) => setRequiredItemsInput(e.target.value)}
            />
          </div>

          {/* Section: Optional Notes & Plan Title */}
          <div className="form-row-2">
            <div className="form-group">
              <label className="section-label" htmlFor="plan-title">
                Custom Plan Title (optional)
              </label>
              <input
                id="plan-title"
                type="text"
                className="form-input"
                placeholder="e.g. Master Bedroom Minimalist Redo"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="section-label" htmlFor="custom-pref">
                Additional Notes / Room Dimensions (optional)
              </label>
              <input
                id="custom-pref"
                type="text"
                className="form-input"
                placeholder="e.g. 12x14 ft room with north-facing window"
                value={preferences}
                onChange={(e) => setPreferences(e.target.value)}
              />
            </div>
          </div>

          {/* Submit Action */}
          <button type="submit" className="btn-generate-plan" disabled={isLoading}>
            {isLoading ? (
              <span className="btn-spinner">Analyzing Catalog with Gemini AI...</span>
            ) : (
              <>
                <Sparkles size={18} />
                <span>Generate Smart Home Plan</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>
      ) : (
        /* Results View */
        <div className="plan-results-wrapper">
          {/* Action Ribbon */}
          <div className="results-action-ribbon">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setPlanResult(null)}
            >
              <RotateCcw size={16} />
              <span>Plan Another Room</span>
            </button>

            {onNavigateToPlans && (
              <button
                type="button"
                className="btn-outline-action"
                onClick={onNavigateToPlans}
              >
                <BookmarkCheck size={16} />
                <span>View in Saved Plans Dashboard</span>
              </button>
            )}
          </div>

          {/* Verified Budget Summary Card */}
          <BudgetSummaryCard
            budget={planResult.budget}
            source={planResult.source}
            title={`${planResult.plan.room_type.replace('_', ' ').toUpperCase()} Interior Budget`}
          />

          {/* AI Strategic Summary */}
          <div className="ai-summary-card">
            <div className="ai-summary-header">
              <Sparkles size={18} className="sparkle-accent" />
              <h4>AI Curation & Budget Strategy</h4>
            </div>
            <p className="ai-summary-text">{planResult.summary}</p>
            {planResult.budget_guidance && (
              <div className="budget-guidance-pill">
                <CheckCircle2 size={15} />
                <span>{planResult.budget_guidance}</span>
              </div>
            )}
          </div>

          {/* Warnings (if any) */}
          {planResult.warnings && planResult.warnings.length > 0 && (
            <div className="plan-warnings-banner">
              <AlertCircle size={16} />
              <div className="warnings-list">
                {planResult.warnings.map((w, idx) => (
                  <p key={idx}>{w}</p>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Product Cards Grid */}
          <div className="results-products-section">
            <div className="section-title-bar">
              <h3 className="section-title">
                Recommended Cross-Platform Catalog Items ({planResult.recommendations.length})
              </h3>
              <span className="section-subtitle">
                Matching style: {planResult.plan.style || 'Modern'} • Room: {planResult.plan.room_type}
              </span>
            </div>

            <div className="products-grid">
              {planResult.recommendations.map((rec, index) => (
                <ProductCard
                  key={`${rec.product.id}-${index}`}
                  product={rec.product}
                  quantity={rec.quantity}
                  subtotal={rec.subtotal}
                  reason={rec.reason}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
