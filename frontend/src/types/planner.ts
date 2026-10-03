import type { Product } from './catalog';

export interface BudgetSummary {
  total_budget: number;
  total_cost: number;
  remaining_budget: number;
  is_within_budget: boolean;
  over_budget_amount: number;
  utilization_percentage: number;
  currency: string;
  currency_symbol: string;
}

export interface RecommendedItemDetail {
  product: Product;
  quantity: number;
  subtotal: number;
  reason: string;
}

// ----------------------------------------------------
// Home Interior Planner Types
// ----------------------------------------------------
export interface HomePlanRequest {
  budget: number;
  room_type: string;
  style?: string;
  color_preferences?: string[];
  priorities?: string[];
  required_items?: string[];
  preferences?: string;
  title?: string;
}

export interface HomePlanDetails {
  room_type: string;
  style?: string | null;
  colors: string[];
  priorities: string[];
  required_items: string[];
}

export interface HomePlanResponse {
  module: 'home';
  source: 'gemini' | 'deterministic_fallback';
  plan: HomePlanDetails;
  summary: string;
  budget_guidance?: string | null;
  recommendations: RecommendedItemDetail[];
  budget: BudgetSummary;
  warnings: string[];
  plan_id?: number | null;
  created_at: string;
}

// ----------------------------------------------------
// Party / Event Planner Types
// ----------------------------------------------------
export interface PartyPlanRequest {
  budget: number;
  guest_count: number;
  event_type: string;
  venue_type: string;
  food_preference?: string;
  decoration_preference?: string;
  entertainment_preference?: string;
  event_duration_hours?: number;
  preferences?: string;
  title?: string;
}

export interface PartyPlanDetails {
  event_type: string;
  guest_count: number;
  venue_type: string;
  food_preference?: string | null;
  decoration_preference?: string | null;
  entertainment_preference?: string | null;
  event_duration_hours?: number | null;
}

export interface PartyPlanResponse {
  module: 'party';
  source: 'gemini' | 'deterministic_fallback';
  plan: PartyPlanDetails;
  summary: string;
  budget_guidance?: string | null;
  recommendations: RecommendedItemDetail[];
  budget: BudgetSummary;
  warnings: string[];
  plan_id?: number | null;
  created_at: string;
}

// ----------------------------------------------------
// Jewelry Planner Types
// ----------------------------------------------------
export interface JewelryPlanRequest {
  budget: number;
  occasion: string;
  style?: string;
  preferred_metal?: string;
  preferred_color?: string;
  jewelry_type?: string;
  preferences?: string;
  title?: string;
  outfit_image?: File | null;
}

export interface JewelryCategoryAllocation {
  category: string;
  allocated_amount: number;
  percentage: number;
}

export interface JewelryPlanDetails {
  occasion: string;
  style?: string | null;
  preferred_metal?: string | null;
  preferred_color?: string | null;
  jewelry_type?: string | null;
  outfit_analyzed: boolean;
}

export interface JewelryPlanResponse {
  module: 'jewelry';
  source: 'gemini' | 'deterministic_fallback';
  plan_id?: number | null;
  plan: JewelryPlanDetails;
  category_allocations: JewelryCategoryAllocation[];
  summary: string;
  budget_guidance?: string | null;
  recommendations: RecommendedItemDetail[];
  budget: BudgetSummary;
  warnings: string[];
  created_at: string;
}
