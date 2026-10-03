import React, { useState } from 'react';
import {
  Gem,
  Sparkles,
  ArrowRight,
  RotateCcw,
  Camera,
  CheckCircle2,
  BookmarkCheck,
  AlertCircle,
  Percent,
} from 'lucide-react';
import { plannerService } from '../services/plannerService';
import type { JewelryPlanResponse } from '../types/planner';
import { BudgetSummaryCard } from '../components/BudgetSummaryCard';
import { ProductCard } from '../components/ProductCard';
import { ImageUploader } from '../components/ImageUploader';
import { Toast } from '../components/Toast';
import { formatINR, formatPercentage } from '../utils/formatters';

interface JewelryPlannerPageProps {
  onNavigateToPlans?: () => void;
}

const OCCASIONS = [
  { id: 'wedding', label: 'Wedding / Bridal' },
  { id: 'engagement', label: 'Engagement Ceremony' },
  { id: 'traditional_event', label: 'Festive / Traditional' },
  { id: 'party', label: 'Evening Party' },
  { id: 'formal_event', label: 'Formal / Gala' },
  { id: 'casual', label: 'Daily / Casual Chic' },
];

const METALS = [
  { id: 'gold', label: 'Yellow Gold (22K/18K)' },
  { id: 'rose_gold', label: 'Rose Gold' },
  { id: 'silver', label: 'Sterling Silver' },
  { id: 'platinum', label: 'Platinum' },
  { id: 'oxidized_silver', label: 'Oxidized Silver' },
  { id: 'any', label: 'Any Finish' },
];

const JEWELRY_TYPES = [
  { id: 'necklace', label: 'Necklace / Choker' },
  { id: 'earrings', label: 'Earrings / Jhumkas' },
  { id: 'complete_set', label: 'Complete Bridal Set' },
  { id: 'bangles', label: 'Bangles / Kadas' },
  { id: 'ring', label: 'Statement Ring' },
  { id: 'bracelet', label: 'Bracelet / Kada' },
  { id: 'any', label: 'Curated Ensemble' },
];

const STONE_COLORS = ['Ruby Red', 'Emerald Green', 'Pearl White', 'Sapphire Blue', 'Kundan Gold', 'Diamond Clear'];

export const JewelryPlannerPage: React.FC<JewelryPlannerPageProps> = ({ onNavigateToPlans }) => {
  const [budget, setBudget] = useState<number>(75000);
  const [occasion, setOccasion] = useState<string>('wedding');
  const [style, setStyle] = useState<string>('Traditional');
  const [metal, setMetal] = useState<string>('gold');
  const [jewelryType, setJewelryType] = useState<string>('complete_set');
  const [selectedColor, setSelectedColor] = useState<string>('Ruby Red');
  const [outfitFile, setOutfitFile] = useState<File | null>(null);
  const [preferences, setPreferences] = useState<string>('');
  const [title, setTitle] = useState<string>('');

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [planResult, setPlanResult] = useState<JewelryPlanResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (budget <= 0) {
      setErrorMsg('Please enter a valid budget amount.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await plannerService.planJewelry({
        budget,
        occasion,
        style,
        preferred_metal: metal,
        preferred_color: selectedColor,
        jewelry_type: jewelryType,
        preferences: preferences.trim() || undefined,
        title: title.trim() || undefined,
        outfit_image: outfitFile,
      });

      setPlanResult(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to generate jewelry plan.';
      setErrorMsg(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="planner-page-container">
      {/* Page Header */}
      <div className="view-header">
        <span className="view-badge jewelry">
          <Gem size={13} /> Jewelry & Vision Planner
        </span>
        <h1 className="view-title">Find Harmonious Jewelry Matching Your Style & Budget</h1>
        <p className="view-subtitle">
          Intelligent metal matching, category allocations, and optional outfit image analysis with Google Gemini Multimodal Vision.
        </p>
      </div>

      {errorMsg && <Toast type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}

      {!planResult ? (
        /* Planner Form */
        <form onSubmit={handleSubmit} className="planner-form-card">
          {/* Section: Budget */}
          <div className="form-section">
            <label className="section-label">
              Jewelry Budget Limit <span className="required">*</span>
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
              {[15000, 35000, 75000, 150000, 300000].map((preset) => (
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

          {/* Section: Occasion */}
          <div className="form-section">
            <label className="section-label">
              Occasion / Event Type <span className="required">*</span>
            </label>
            <div className="pills-grid">
              {OCCASIONS.map((occ) => (
                <button
                  key={occ.id}
                  type="button"
                  className={`pill-option ${occasion === occ.id ? 'active' : ''}`}
                  onClick={() => setOccasion(occ.id)}
                >
                  {occ.label}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Style */}
          <div className="form-section">
            <label className="section-label">Aesthetic & Crafting Style</label>
            <div className="pills-grid">
              {['Traditional', 'Minimalist', 'Modern', 'Bohemian', 'Antique'].map((s) => (
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

          {/* Section: Metal Finish & Target Type */}
          <div className="form-row-2">
            <div className="form-group">
              <label className="section-label">Preferred Metal / Finish</label>
              <div className="pills-grid">
                {METALS.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    className={`pill-option ${metal === m.id ? 'active' : ''}`}
                    onClick={() => setMetal(m.id)}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="section-label">Primary Target Piece</label>
              <div className="pills-grid">
                {JEWELRY_TYPES.map((jt) => (
                  <button
                    key={jt.id}
                    type="button"
                    className={`pill-option ${jewelryType === jt.id ? 'active' : ''}`}
                    onClick={() => setJewelryType(jt.id)}
                  >
                    {jt.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Section: Stone & Accent Colors */}
          <div className="form-section">
            <label className="section-label">Preferred Stone or Accent Color</label>
            <div className="badge-select-row">
              {STONE_COLORS.map((col) => (
                <button
                  key={col}
                  type="button"
                  className={`badge-toggle ${selectedColor === col ? 'selected' : ''}`}
                  onClick={() => setSelectedColor(col)}
                >
                  {col}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Multimodal Outfit Photo Upload */}
          <div className="form-section">
            <div className="label-with-hint">
              <label className="section-label">
                <Camera size={15} /> Upload Outfit Photo (Optional Gemini Multimodal Vision)
              </label>
              <span className="per-guest-hint">AI inspects attire pattern & color</span>
            </div>
            <ImageUploader onImageSelected={(file) => setOutfitFile(file)} maxSizeMB={5} />
          </div>

          {/* Section: Title & Details */}
          <div className="form-row-2">
            <div className="form-group">
              <label className="section-label" htmlFor="jewel-title">
                Custom Plan Title (optional)
              </label>
              <input
                id="jewel-title"
                type="text"
                className="form-input"
                placeholder="e.g. Saree Matching Kundan Set"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="section-label" htmlFor="jewel-notes">
                Design Preferences / Notes (optional)
              </label>
              <input
                id="jewel-notes"
                type="text"
                className="form-input"
                placeholder="e.g. Heavy choker with matching drop jhumkas and pearl accents"
                value={preferences}
                onChange={(e) => setPreferences(e.target.value)}
              />
            </div>
          </div>

          {/* Submit Action */}
          <button type="submit" className="btn-generate-plan" disabled={isLoading}>
            {isLoading ? (
              <span className="btn-spinner">
                {outfitFile ? 'Analyzing Outfit & Matching with Gemini Vision...' : 'Curating Jewelry Plan with Gemini AI...'}
              </span>
            ) : (
              <>
                <Sparkles size={18} />
                <span>{outfitFile ? 'Analyze Outfit & Curate Jewelry' : 'Generate Smart Jewelry Plan'}</span>
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
              <span>Plan Another Ensemble</span>
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

          {/* Multimodal Vision Confirmation Pill */}
          {planResult.plan.outfit_analyzed && (
            <div className="multimodal-success-banner">
              <Camera size={18} className="camera-icon" />
              <div>
                <strong>Outfit Analyzed by Gemini Multimodal Vision:</strong>
                <span> Jewelry curated to harmonize with uploaded attire colors and patterns.</span>
              </div>
            </div>
          )}

          {/* Verified Budget Summary Card */}
          <BudgetSummaryCard
            budget={planResult.budget}
            source={planResult.source}
            title={`${planResult.plan.occasion.toUpperCase()} Jewelry Budget`}
          />

          {/* Category Allocations Strip */}
          {planResult.category_allocations && planResult.category_allocations.length > 0 && (
            <div className="allocations-card">
              <div className="allocations-header">
                <Percent size={16} className="sparkle-accent" />
                <h4>Category Budget Allocations</h4>
              </div>
              <div className="allocations-grid">
                {planResult.category_allocations.map((alloc) => (
                  <div key={alloc.category} className="allocation-pill">
                    <span className="alloc-cat">{alloc.category}</span>
                    <span className="alloc-amt">{formatINR(alloc.allocated_amount)}</span>
                    <span className="alloc-pct">{formatPercentage(alloc.percentage)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Strategic Summary */}
          <div className="ai-summary-card">
            <div className="ai-summary-header">
              <Sparkles size={18} className="sparkle-accent" />
              <h4>AI Curation & Styling Advice</h4>
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
                Curated Jewelry Pieces ({planResult.recommendations.length})
              </h3>
              <span className="section-subtitle">
                Metal finish: {planResult.plan.preferred_metal || 'Gold'} • Style: {planResult.plan.style || 'Traditional'}
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
