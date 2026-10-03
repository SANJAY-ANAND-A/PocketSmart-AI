import React, { useState } from 'react';
import {
  PartyPopper,
  Sparkles,
  ArrowRight,
  RotateCcw,
  Users,
  Building,
  Utensils,
  Music,
  BookmarkCheck,
  AlertCircle,
  Clock,
} from 'lucide-react';
import { plannerService } from '../services/plannerService';
import type { PartyPlanResponse } from '../types/planner';
import { BudgetSummaryCard } from '../components/BudgetSummaryCard';
import { ProductCard } from '../components/ProductCard';
import { Toast } from '../components/Toast';
import { formatINR } from '../utils/formatters';

interface PartyPlannerPageProps {
  onNavigateToPlans?: () => void;
}

const EVENT_TYPES = [
  { id: 'birthday', label: 'Birthday Celebration' },
  { id: 'wedding', label: 'Wedding / Reception' },
  { id: 'college_event', label: 'College Fest / Event' },
  { id: 'corporate_event', label: 'Corporate Gathering' },
  { id: 'anniversary', label: 'Anniversary' },
  { id: 'small_gathering', label: 'Casual Get-Together' },
];

const VENUE_TYPES = [
  { id: 'banquet_hall', label: 'Banquet Hall' },
  { id: 'hotel', label: 'Hotel / Resort' },
  { id: 'outdoor', label: 'Outdoor Lawn' },
  { id: 'restaurant', label: 'Lounge / Restaurant' },
  { id: 'community_hall', label: 'Community Hall' },
  { id: 'home', label: 'Private Home / Rooftop' },
  { id: 'college_campus', label: 'Campus Auditorium' },
];

const FOOD_PREFS = [
  { id: 'multicuisine', label: 'Multi-Cuisine Buffet' },
  { id: 'vegetarian', label: 'Pure Vegetarian' },
  { id: 'non_vegetarian', label: 'Non-Vegetarian' },
  { id: 'street_food', label: 'Live Street Food Stalls' },
  { id: 'jain', label: 'Jain Friendly' },
];

const DECOR_PREFS = ['elegant', 'floral', 'balloon', 'minimal', 'grand'];
const ENTERTAINMENT_PREFS = [
  { id: 'dj', label: 'DJ & Sound' },
  { id: 'live_band', label: 'Live Band' },
  { id: 'acoustic', label: 'Acoustic / Vocalist' },
  { id: 'sound_system', label: 'Sound System Only' },
  { id: 'none', label: 'No Music' },
];

export const PartyPlannerPage: React.FC<PartyPlannerPageProps> = ({ onNavigateToPlans }) => {
  const [budget, setBudget] = useState<number>(50000);
  const [guestCount, setGuestCount] = useState<number>(50);
  const [eventType, setEventType] = useState<string>('birthday');
  const [venueType, setVenueType] = useState<string>('banquet_hall');
  const [foodPref, setFoodPref] = useState<string>('multicuisine');
  const [decorPref, setDecorPref] = useState<string>('elegant');
  const [entertainmentPref, setEntertainmentPref] = useState<string>('dj');
  const [durationHours, setDurationHours] = useState<number>(4);
  const [preferences, setPreferences] = useState<string>('');
  const [title, setTitle] = useState<string>('');

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [planResult, setPlanResult] = useState<PartyPlanResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const budgetPerGuest = guestCount > 0 ? budget / guestCount : 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (budget <= 0) {
      setErrorMsg('Please enter a valid budget amount.');
      return;
    }
    if (guestCount <= 0) {
      setErrorMsg('Please enter a valid number of guests.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await plannerService.planParty({
        budget,
        guest_count: guestCount,
        event_type: eventType,
        venue_type: venueType,
        food_preference: foodPref,
        decoration_preference: decorPref,
        entertainment_preference: entertainmentPref,
        event_duration_hours: durationHours,
        preferences: preferences.trim() || undefined,
        title: title.trim() || undefined,
      });

      setPlanResult(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to generate party plan.';
      setErrorMsg(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="planner-page-container">
      {/* Page Header */}
      <div className="view-header">
        <span className="view-badge party">
          <PartyPopper size={13} /> Party & Event Planner
        </span>
        <h1 className="view-title">Celebrate Stress-Free Within Budget</h1>
        <p className="view-subtitle">
          Intelligent venue, catering, decor, and entertainment budget allocations scaled by attendee count.
        </p>
      </div>

      {errorMsg && <Toast type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}

      {!planResult ? (
        /* Planner Form */
        <form onSubmit={handleSubmit} className="planner-form-card">
          {/* Section: Budget Limit */}
          <div className="form-section">
            <div className="label-with-hint">
              <label className="section-label">
                Total Celebration Budget <span className="required">*</span>
              </label>
              <span className="per-guest-hint">
                ≈ {formatINR(budgetPerGuest)} per guest ({guestCount} guests)
              </span>
            </div>
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
              {[15000, 30000, 50000, 100000, 250000].map((preset) => (
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

          {/* Section: Guests & Duration */}
          <div className="form-row-2">
            <div className="form-group">
              <label className="section-label" htmlFor="guest-count">
                <Users size={15} /> Expected Guest Count <span className="required">*</span>
              </label>
              <input
                id="guest-count"
                type="number"
                min="1"
                max="10000"
                className="form-input"
                value={guestCount}
                onChange={(e) => setGuestCount(Number(e.target.value))}
                required
              />
            </div>

            <div className="form-group">
              <label className="section-label" htmlFor="duration-hours">
                <Clock size={15} /> Event Duration (Hours)
              </label>
              <input
                id="duration-hours"
                type="number"
                min="1"
                max="72"
                step="0.5"
                className="form-input"
                value={durationHours}
                onChange={(e) => setDurationHours(Number(e.target.value))}
              />
            </div>
          </div>

          {/* Section: Event Type */}
          <div className="form-section">
            <label className="section-label">Type of Event / Celebration</label>
            <div className="pills-grid">
              {EVENT_TYPES.map((ev) => (
                <button
                  key={ev.id}
                  type="button"
                  className={`pill-option ${eventType === ev.id ? 'active' : ''}`}
                  onClick={() => setEventType(ev.id)}
                >
                  {ev.label}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Venue Type */}
          <div className="form-section">
            <label className="section-label">
              <Building size={15} /> Preferred Venue Environment
            </label>
            <div className="pills-grid">
              {VENUE_TYPES.map((v) => (
                <button
                  key={v.id}
                  type="button"
                  className={`pill-option ${venueType === v.id ? 'active' : ''}`}
                  onClick={() => setVenueType(v.id)}
                >
                  {v.label}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Food & Catering */}
          <div className="form-section">
            <label className="section-label">
              <Utensils size={15} /> Food & Catering Preference
            </label>
            <div className="pills-grid">
              {FOOD_PREFS.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  className={`pill-option ${foodPref === f.id ? 'active' : ''}`}
                  onClick={() => setFoodPref(f.id)}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Decor & Entertainment */}
          <div className="form-row-2">
            <div className="form-group">
              <label className="section-label">Decoration Style</label>
              <div className="badge-select-row">
                {DECOR_PREFS.map((d) => (
                  <button
                    key={d}
                    type="button"
                    className={`badge-toggle ${decorPref === d ? 'selected' : ''}`}
                    onClick={() => setDecorPref(d)}
                  >
                    {d.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="section-label">
                <Music size={15} /> Entertainment Preference
              </label>
              <div className="pills-grid">
                {ENTERTAINMENT_PREFS.map((ent) => (
                  <button
                    key={ent.id}
                    type="button"
                    className={`pill-option ${entertainmentPref === ent.id ? 'active' : ''}`}
                    onClick={() => setEntertainmentPref(ent.id)}
                  >
                    {ent.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Section: Custom Title & Notes */}
          <div className="form-row-2">
            <div className="form-group">
              <label className="section-label" htmlFor="party-title">
                Custom Event Title (optional)
              </label>
              <input
                id="party-title"
                type="text"
                className="form-input"
                placeholder="e.g. 21st Birthday Bash on Rooftop"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="section-label" htmlFor="party-notes">
                Special Requests / VIP Needs (optional)
              </label>
              <input
                id="party-notes"
                type="text"
                className="form-input"
                placeholder="e.g. Need neon photo-booth and mocktail bar"
                value={preferences}
                onChange={(e) => setPreferences(e.target.value)}
              />
            </div>
          </div>

          {/* Submit Action */}
          <button type="submit" className="btn-generate-plan" disabled={isLoading}>
            {isLoading ? (
              <span className="btn-spinner">Computing Event Allocations with Gemini AI...</span>
            ) : (
              <>
                <Sparkles size={18} />
                <span>Generate Smart Event Plan</span>
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
              <span>Plan Another Celebration</span>
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
            title={`${planResult.plan.event_type.replace('_', ' ').toUpperCase()} Plan (${planResult.plan.guest_count} Guests)`}
          />

          {/* AI Strategic Summary */}
          <div className="ai-summary-card">
            <div className="ai-summary-header">
              <Sparkles size={18} className="sparkle-accent" />
              <h4>Event Coordination & Budget Strategy</h4>
            </div>
            <p className="ai-summary-text">{planResult.summary}</p>
            {planResult.budget_guidance && (
              <div className="budget-guidance-pill">
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
                Recommended Vendors, Venue & Services ({planResult.recommendations.length})
              </h3>
              <span className="section-subtitle">
                Cross-platform selection: Swiggy, Zomato, OYO, Amazon & Local vendors
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
